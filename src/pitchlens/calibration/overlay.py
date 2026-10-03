"""Projeção das linhas do campo na imagem (Fase 3).

Desenhar o modelo do campo por cima do vídeo é a forma mais direta de conferir a homografia:
se as linhas desenhadas caem sobre as linhas do gramado, a calibração está certa.

A projeção não é só multiplicar matriz. Uma linha reta no campo continua reta na imagem, mas
quando ela cruza o horizonte o resultado salta de um lado ao outro da tela, e ligar os dois
pedaços desenharia um risco atravessado. O divisor da homografia troca de sinal exatamente
nessa travessia, e é por ele que as linhas são quebradas em pedaços desenháveis.
"""

from __future__ import annotations

import numpy as np

from pitchlens.calibration.homography import Homography
from pitchlens.pitch import FIFA_PITCH, PitchSpec

# Pedaços totalmente fora da imagem por mais de uma tela de distância não precisam ser desenhados.
VISIBLE_MARGIN = 1.0

_EPS = 1e-9


def split_polyline(points: np.ndarray, scales: np.ndarray | None = None) -> list[np.ndarray]:
    """Quebra uma linha projetada onde ela cruza o horizonte, devolvendo os pedaços desenháveis.

    ``scales`` são os divisores devolvidos pela projeção. Sem eles, a linha só é quebrada nos
    pontos sem resultado finito.
    """
    points = np.asarray(points, dtype=np.float64).reshape(-1, 2)
    scales = np.ones(len(points)) if scales is None else np.asarray(scales, dtype=np.float64)

    pieces: list[np.ndarray] = []
    current: list[np.ndarray] = []
    previous: float | None = None

    def flush() -> None:
        nonlocal current
        if len(current) >= 2:
            pieces.append(np.array(current))
        current = []

    for point, scale in zip(points, scales, strict=True):
        if not (np.isfinite(point).all() and np.isfinite(scale) and abs(scale) > _EPS):
            flush()
            previous = None
            continue
        if previous is not None and np.sign(scale) != np.sign(previous):
            flush()
        current.append(point)
        previous = float(scale)
    flush()
    return pieces


def visible(piece: np.ndarray, frame_size: tuple[int, int], margin: float = VISIBLE_MARGIN) -> bool:
    """Indica se um pedaço de linha passa perto o bastante da imagem para valer o desenho."""
    width, height = frame_size
    x, y = piece[:, 0], piece[:, 1]
    return bool(
        (x.max() > -margin * width)
        and (x.min() < (1.0 + margin) * width)
        and (y.max() > -margin * height)
        and (y.min() < (1.0 + margin) * height)
    )


def project_lines(
    homography: Homography,
    frame_size: tuple[int, int],
    *,
    pitch: PitchSpec = FIFA_PITCH,
) -> dict[str, list[np.ndarray]]:
    """Linhas do campo levadas para a imagem, prontas para desenhar, em pixels."""
    projected = {}
    for name, line in pitch.lines().items():
        points, scales = homography.to_image_with_scale(line)
        pieces = [piece for piece in split_polyline(points, scales) if visible(piece, frame_size)]
        if pieces:
            projected[name] = pieces
    return projected


def pitch_to_radar(
    points_m: np.ndarray,
    radar_size: tuple[int, int],
    *,
    pitch: PitchSpec = FIFA_PITCH,
    padding: int = 10,
) -> np.ndarray:
    """Posições em metros levadas para os pixels do radar: o campo visto de cima.

    A escala é a mesma nos dois eixos e o campo fica centrado no painel. Esticar o desenho
    para preencher o painel deformaria as distâncias, que são justamente o que a homografia
    foi estimada para medir.
    """
    width, height = radar_size
    usable_width, usable_height = width - 2 * padding, height - 2 * padding
    if usable_width <= 0 or usable_height <= 0:
        raise ValueError("o radar é pequeno demais para a margem pedida")
    scale = min(usable_width / pitch.length, usable_height / pitch.width)
    offset = np.array([(width - pitch.length * scale) / 2, (height - pitch.width * scale) / 2])
    return np.asarray(points_m, dtype=np.float64).reshape(-1, 2) * scale + offset


def radar_positions(
    homography: Homography,
    points: np.ndarray,
    radar_size: tuple[int, int],
    *,
    pitch: PitchSpec = FIFA_PITCH,
    padding: int = 10,
) -> np.ndarray:
    """Pontos da imagem levados para as coordenadas do radar.

    Pontos que a homografia não resolve saem como ``NaN``.
    """
    metres = homography.to_pitch(points)
    return pitch_to_radar(metres, radar_size, pitch=pitch, padding=padding)
