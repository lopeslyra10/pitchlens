"""Homografia entre a imagem e o campo em metros (Fase 3).

Uma homografia é a matriz 3x3 que relaciona dois planos vistos em perspectiva. Como o gramado
é plano, a posição de um jogador na imagem pode ser levada para metros no campo desde que se
conheçam quatro pontos correspondentes. O modelo de keypoints entrega esses pontos; aqui eles
são transformados em matriz, com três cuidados:

- **RANSAC**: um ponto previsto no lugar errado estraga o ajuste inteiro. O ajuste é repetido
  em amostras de quatro pontos e vence a matriz que concorda com mais pontos, medindo o erro
  em metros (unidade do campo, e não pixels, que variam com o zoom).
- **Suavização**: a matriz é reestimada a cada frame, então pequenos erros fazem o campo
  "tremer". A suavização é feita na posição dos pontos do campo projetados na imagem, não na
  matriz: média de matrizes não tem significado geométrico, posição de ponto tem.
- **Descarte**: em replay, close no banco ou corte de câmera sobram poucos pontos e o erro
  explode. Nesses frames a última matriz boa é repetida por um tempo, e depois a calibração
  é declarada ausente em vez de devolver posições inventadas.

O módulo usa só NumPy (DLT normalizado e RANSAC escritos à mão), para rodar na CI sem GPU e
sem OpenCV, e o ajuste é determinístico: a mesma entrada dá sempre a mesma matriz.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from pitchlens.pitch import FIFA_PITCH, KEYPOINT_ORDER, PitchSpec

# Um ponto que erra por mais de 1,5 m é tratado como previsão ruim, não como ruído do ajuste.
RANSAC_THRESHOLD_M = 1.5
RANSAC_ITERATIONS = 120
# Quatro pontos bastam para a matriz; menos que isso não define o plano.
MIN_POINTS = 4
# Para aceitar um frame exigimos folga sobre o mínimo: com exatamente 4 pontos o erro é zero
# por construção e não dá para saber se o ajuste está certo.
MIN_POINTS_PER_FRAME = 6
MAX_ERROR_M = 3.0
# O RANSAC sempre encontra alguma matriz: com pontos muito ruins ele se apoia num punhado
# deles e devolve erro baixo numa matriz errada. Por isso a maioria dos pontos vistos tem de
# concordar com o ajuste, e não apenas um número mínimo deles.
MIN_INLIER_FRACTION = 0.5
# Peso do frame novo na suavização. Mais baixo estabiliza, mais alto acompanha a câmera.
SMOOTHING = 0.5
# Depois de meio segundo (a 30 fps) sem pontos, repetir a última matriz passa a mentir.
MAX_REPEATED_FRAMES = 15
# Um corte de câmera muda tudo de uma vez: a matriz suavizada fica pior que a do frame, e aí
# o histórico é esquecido em vez de arrastar a cena anterior.
CUT_ERROR_FACTOR = 1.5
# Pontos do campo projetados para muito longe da imagem são numericamente instáveis (ficam
# perto da linha do horizonte) e não entram na suavização.
ANCHOR_MARGIN = 2.0
# Quão pequena a oitava direção do sistema pode ficar antes de o ajuste ser considerado
# degenerado, em proporção à maior. Com os pontos normalizados a separação é larga: um quadro
# do campo mede 0,19 e quatro pontos em linha medem 1e-17.
DEGENERATE_TOLERANCE = 1e-6

OK = "ok"
REPETIDA = "repetida"
SEM_CAMPO = "sem campo"

_EPS = 1e-9


def transform_points_with_scale(
    matrix: np.ndarray, points: Sequence[Sequence[float]]
) -> tuple[np.ndarray, np.ndarray]:
    """Aplica uma homografia e devolve também o divisor de cada ponto.

    O divisor diz de que lado do horizonte o ponto está: ele troca de sinal quando a linha
    passa para trás da câmera, e é zero exatamente sobre o horizonte, onde o ponto não tem
    posição na imagem (e sai como ``NaN``).
    """
    array = np.asarray(points, dtype=np.float64).reshape(-1, 2)
    homogeneous = np.hstack([array, np.ones((len(array), 1))])
    projected = homogeneous @ np.asarray(matrix, dtype=np.float64).T
    scale = projected[:, 2]
    finite = np.abs(scale) > _EPS
    result = np.full((len(array), 2), np.nan)
    result[finite] = projected[finite, :2] / scale[finite, None]
    return result, scale


def transform_points(matrix: np.ndarray, points: Sequence[Sequence[float]]) -> np.ndarray:
    """Aplica uma homografia a pontos ``(N, 2)``, com ``NaN`` para os pontos no horizonte."""
    return transform_points_with_scale(matrix, points)[0]


def reprojection_errors_m(
    matrix: np.ndarray,
    image_points: Sequence[Sequence[float]],
    pitch_points: Sequence[Sequence[float]],
) -> np.ndarray:
    """Distância, em metros, entre cada ponto levado para o campo e onde ele deveria cair."""
    projected = transform_points(matrix, image_points)
    expected = np.asarray(pitch_points, dtype=np.float64).reshape(-1, 2)
    if len(projected) != len(expected):
        raise ValueError("cada ponto da imagem precisa de um ponto do campo")
    errors = np.linalg.norm(projected - expected, axis=1)
    return np.where(np.isfinite(errors), errors, np.inf)


def _normalization(points: np.ndarray) -> np.ndarray:
    """Matriz que centra os pontos na origem e põe a distância média em raiz de 2.

    Sem essa normalização o sistema do DLT mistura pixels (centenas) com metros (dezenas) e a
    solução fica dominada pelo erro numérico.
    """
    centroid = points.mean(axis=0)
    distances = np.linalg.norm(points - centroid, axis=1)
    mean_distance = float(distances.mean())
    scale = np.sqrt(2.0) / mean_distance if mean_distance > _EPS else 1.0
    return np.array(
        [[scale, 0.0, -scale * centroid[0]], [0.0, scale, -scale * centroid[1]], [0.0, 0.0, 1.0]]
    )


def solve_homography(source: np.ndarray, target: np.ndarray) -> np.ndarray | None:
    """Homografia que leva ``source`` em ``target`` pelo DLT normalizado (mínimos quadrados).

    Devolve ``None`` quando os pontos são degenerados (três deles em linha, por exemplo) e o
    sistema não tem solução única.
    """
    source = np.asarray(source, dtype=np.float64).reshape(-1, 2)
    target = np.asarray(target, dtype=np.float64).reshape(-1, 2)
    if len(source) < MIN_POINTS or len(source) != len(target):
        return None

    to_source, to_target = _normalization(source), _normalization(target)
    src = transform_points(to_source, source)
    dst = transform_points(to_target, target)
    if not (np.isfinite(src).all() and np.isfinite(dst).all()):
        return None

    rows = []
    for (x, y), (u, v) in zip(src, dst, strict=True):
        rows.append([-x, -y, -1.0, 0.0, 0.0, 0.0, u * x, u * y, u])
        rows.append([0.0, 0.0, 0.0, -x, -y, -1.0, v * x, v * y, v])
    _, singular, right = np.linalg.svd(np.array(rows))
    # O sistema tem 9 incógnitas e precisa ter posto 8 para a solução ser única: a oitava
    # direção some quando os pontos são degenerados (três deles em linha, por exemplo).
    if singular[7] < DEGENERATE_TOLERANCE * singular[0]:
        return None

    matrix = np.linalg.inv(to_target) @ right[-1].reshape(3, 3) @ to_source
    if not np.isfinite(matrix).all() or abs(np.linalg.det(matrix)) < _EPS:
        return None
    pivot = matrix[2, 2]
    return matrix / pivot if abs(pivot) > _EPS else matrix / np.linalg.norm(matrix)


@dataclass(frozen=True)
class Homography:
    """Homografia da imagem para o campo, com a qualidade do ajuste que a gerou."""

    matrix: np.ndarray
    error_m: float
    points: int
    inliers: int

    def to_pitch(self, points: Sequence[Sequence[float]]) -> np.ndarray:
        """Leva pontos da imagem (pixels) para o campo (metros)."""
        return transform_points(self.matrix, points)

    def to_image(self, points: Sequence[Sequence[float]]) -> np.ndarray:
        """Leva pontos do campo (metros) para a imagem (pixels), para desenhar por cima."""
        return transform_points(np.linalg.inv(self.matrix), points)

    def to_image_with_scale(
        self, points: Sequence[Sequence[float]]
    ) -> tuple[np.ndarray, np.ndarray]:
        """Como ``to_image``, mas devolve também o divisor, que diz o lado do horizonte."""
        return transform_points_with_scale(np.linalg.inv(self.matrix), points)


def fit_homography(
    image_points: Sequence[Sequence[float]],
    pitch_points: Sequence[Sequence[float]],
    *,
    threshold_m: float = RANSAC_THRESHOLD_M,
    iterations: int = RANSAC_ITERATIONS,
    seed: int = 0,
) -> Homography | None:
    """Ajusta a homografia imagem → campo com RANSAC, tolerando pontos previstos errados.

    O erro informado é a mediana, em metros, sobre os pontos aceitos pelo ajuste.
    """
    image = np.asarray(image_points, dtype=np.float64).reshape(-1, 2)
    pitch = np.asarray(pitch_points, dtype=np.float64).reshape(-1, 2)
    if len(image) != len(pitch):
        raise ValueError("cada ponto da imagem precisa de um ponto do campo")
    if len(image) < MIN_POINTS or not np.isfinite(image).all():
        return None

    if len(image) == MIN_POINTS:
        matrix = solve_homography(image, pitch)
        if matrix is None:
            return None
        errors = reprojection_errors_m(matrix, image, pitch)
        return Homography(matrix, float(np.median(errors)), len(image), len(image))

    rng = np.random.default_rng(seed)
    best_matrix, best_inliers, best_error = None, np.zeros(len(image), dtype=bool), np.inf
    for _ in range(iterations):
        sample = rng.choice(len(image), MIN_POINTS, replace=False)
        matrix = solve_homography(image[sample], pitch[sample])
        if matrix is None:
            continue
        errors = reprojection_errors_m(matrix, image, pitch)
        inliers = errors <= threshold_m
        error = float(np.median(errors[inliers])) if inliers.any() else np.inf
        if (inliers.sum(), -error) > (best_inliers.sum(), -best_error):
            best_matrix, best_inliers, best_error = matrix, inliers, error
        if best_inliers.all():
            break

    if best_matrix is None or best_inliers.sum() < MIN_POINTS:
        return None

    # O ajuste final usa todos os pontos aceitos, não só os quatro sorteados.
    refined = solve_homography(image[best_inliers], pitch[best_inliers])
    matrix = refined if refined is not None else best_matrix
    errors = reprojection_errors_m(matrix, image[best_inliers], pitch[best_inliers])
    return Homography(matrix, float(np.median(errors)), len(image), int(best_inliers.sum()))


def visible_keypoints(
    keypoints: Sequence[Sequence[float]],
    confidences: Sequence[float] | None = None,
    *,
    min_confidence: float = 0.5,
    pitch: PitchSpec = FIFA_PITCH,
) -> tuple[np.ndarray, np.ndarray]:
    """Separa os pontos previstos que servem ao ajuste e os pontos do campo correspondentes.

    Recebe os 32 pontos na ordem de ``KEYPOINT_ORDER``, como o modelo os prevê, e devolve só
    os visíveis: confiança suficiente e coordenada finita e não nula.
    """
    image = np.asarray(keypoints, dtype=np.float64).reshape(-1, 2)
    if len(image) != len(KEYPOINT_ORDER):
        raise ValueError(f"esperados {len(KEYPOINT_ORDER)} pontos, recebidos {len(image)}")
    scores = (
        np.ones(len(image))
        if confidences is None
        else np.asarray(confidences, dtype=np.float64).reshape(-1)
    )
    if len(scores) != len(image):
        raise ValueError("cada ponto precisa de uma confiança")

    visible = (scores >= min_confidence) & np.isfinite(image).all(axis=1) & (image != 0).any(axis=1)
    return image[visible], pitch.keypoints_array(KEYPOINT_ORDER)[visible].astype(np.float64)


@dataclass(frozen=True)
class FrameCalibration:
    """Resultado da calibração de um frame."""

    homography: Homography | None
    status: str
    points: int

    @property
    def usable(self) -> bool:
        return self.homography is not None


class PitchCalibrator:
    """Mantém a homografia ao longo do vídeo: ajusta, suaviza e descarta frames ruins."""

    def __init__(
        self,
        frame_size: tuple[int, int],
        *,
        pitch: PitchSpec = FIFA_PITCH,
        min_points: int = MIN_POINTS_PER_FRAME,
        max_error_m: float = MAX_ERROR_M,
        min_inlier_fraction: float = MIN_INLIER_FRACTION,
        smoothing: float = SMOOTHING,
        max_repeated: int = MAX_REPEATED_FRAMES,
        seed: int = 0,
    ) -> None:
        width, height = frame_size
        if width <= 0 or height <= 0:
            raise ValueError("o tamanho do frame deve ser positivo")
        if not 0.0 < smoothing <= 1.0:
            raise ValueError("a suavização deve ficar entre 0 (exclusivo) e 1")
        if min_points < MIN_POINTS:
            raise ValueError(f"são necessários pelo menos {MIN_POINTS} pontos")
        self.frame_size = (int(width), int(height))
        self.pitch = pitch
        self.min_points = min_points
        self.max_error_m = max_error_m
        self.min_inlier_fraction = min_inlier_fraction
        self.smoothing = smoothing
        self.max_repeated = max_repeated
        self.seed = seed
        self._anchors_pitch = pitch.keypoints_array(KEYPOINT_ORDER).astype(np.float64)
        self._anchors_image: np.ndarray | None = None
        self._last: Homography | None = None
        self._repeated = 0

    def update(
        self,
        keypoints: Sequence[Sequence[float]],
        confidences: Sequence[float] | None = None,
        *,
        min_confidence: float = 0.5,
    ) -> FrameCalibration:
        """Calibra um frame a partir dos pontos previstos pelo modelo."""
        image, pitch = visible_keypoints(
            keypoints, confidences, min_confidence=min_confidence, pitch=self.pitch
        )
        fitted = None
        if len(image) >= self.min_points:
            fitted = fit_homography(image, pitch, seed=self.seed)
        if fitted is None or not self._trustworthy(fitted):
            return self._repeat(len(image))

        smoothed = self._smooth(fitted, image, pitch)
        self._last = smoothed
        self._repeated = 0
        return FrameCalibration(smoothed, OK, len(image))

    def _trustworthy(self, fitted: Homography) -> bool:
        """Aceita o ajuste quando erra pouco e tem o apoio da maioria dos pontos vistos."""
        return (
            fitted.error_m <= self.max_error_m
            and fitted.inliers >= self.min_points
            and fitted.inliers >= self.min_inlier_fraction * fitted.points
        )

    def _repeat(self, points: int) -> FrameCalibration:
        """Repete a última matriz boa enquanto a falta de pontos for passageira."""
        if self._last is None or self._repeated >= self.max_repeated:
            self._last = None
            self._anchors_image = None
            return FrameCalibration(None, SEM_CAMPO, points)
        self._repeated += 1
        return FrameCalibration(self._last, REPETIDA, points)

    def _smooth(self, fitted: Homography, image: np.ndarray, pitch: np.ndarray) -> Homography:
        """Suaviza a matriz pela posição dos pontos do campo projetados na imagem."""
        projected = self._project_anchors(fitted)
        previous = self._anchors_image
        if previous is None:
            self._anchors_image = projected
            return fitted

        blended = np.where(
            np.isnan(previous) | np.isnan(projected),
            projected,
            self.smoothing * projected + (1.0 - self.smoothing) * previous,
        )
        usable = np.isfinite(blended).all(axis=1)
        matrix = (
            solve_homography(blended[usable], self._anchors_pitch[usable])
            if usable.sum() >= MIN_POINTS
            else None
        )
        if matrix is None:
            self._anchors_image = projected
            return fitted

        # O erro é medido sempre nos pontos observados, nunca nos pontos suavizados, que por
        # construção caem no lugar certo.
        errors = reprojection_errors_m(matrix, image, pitch)
        error = float(np.median(errors))
        if error > fitted.error_m * CUT_ERROR_FACTOR + 0.1:
            self._anchors_image = projected  # corte de câmera: o histórico não serve mais
            return fitted

        self._anchors_image = blended
        return Homography(matrix, error, fitted.points, fitted.inliers)

    def _project_anchors(self, homography: Homography) -> np.ndarray:
        """Pontos do campo levados para a imagem, com ``NaN`` nos que caem longe demais."""
        width, height = self.frame_size
        projected = homography.to_image(self._anchors_pitch)
        inside = (
            (projected[:, 0] > -ANCHOR_MARGIN * width)
            & (projected[:, 0] < (1.0 + ANCHOR_MARGIN) * width)
            & (projected[:, 1] > -ANCHOR_MARGIN * height)
            & (projected[:, 1] < (1.0 + ANCHOR_MARGIN) * height)
        )
        return np.where(inside[:, None], projected, np.nan)
