"""Separação dos jogadores em dois times pela cor do uniforme (Fase 2).

A cor de cada jogador é a mediana dos pixels do tronco, ignorando o gramado. Essas cores são
agrupadas em dois times com k-means, sem nenhum rótulo manual. Como a cor de um mesmo jogador
varia entre frames (sombra, oclusão, desfoque), o time final de cada identificador é decidido
por voto ao longo do tempo.

O módulo usa só NumPy, para poder ser testado na CI sem GPU.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Sequence

import numpy as np

TEAM_A, TEAM_B, NO_TEAM = 0, 1, -1

# Um pixel é gramado quando o verde supera o vermelho e o azul por esta margem.
GRASS_MARGIN = 1.08
MIN_JERSEY_PIXELS = 12
# Recortes com menos uniforme que isso são quase só gramado e dariam uma cor pouco confiável.
MIN_JERSEY_FRACTION = 0.15
# Uma cor mais distante dos dois times do que isso (em múltiplos do raio de cada time) não é de
# nenhum deles: arbitragem, reservas e pessoas fora do campo que o detector marcou como jogador.
OUTLIER_RADIUS_FACTOR = 3.5
# O ajuste robusto descarta as cores mais distantes de cada time antes de recalcular o centro,
# para que arbitragem e sombras não puxem a cor do time nem inflem o raio.
TRIM_PERCENTILE = 75
TRIM_ROUNDS = 2
# Raio mínimo de cada time: a cor de um uniforme sempre varia um pouco com luz e sombra.
MIN_TEAM_RADIUS = 0.05


def torso_crop(frame: np.ndarray, box: Sequence[float]) -> np.ndarray:
    """Recorte central do tronco: evita cabeça, braços, calção e o gramado ao redor."""
    x1, y1, x2, y2 = box
    width, height = x2 - x1, y2 - y1
    top, bottom = int(y1 + 0.2 * height), int(y1 + 0.55 * height)
    left, right = int(x1 + 0.25 * width), int(x2 - 0.25 * width)
    frame_height, frame_width = frame.shape[:2]
    top, bottom = max(top, 0), min(bottom, frame_height)
    left, right = max(left, 0), min(right, frame_width)
    return frame[top:bottom, left:right]


def jersey_color(crop: np.ndarray) -> np.ndarray | None:
    """Cor mediana do uniforme em RGB (0 a 1), ou ``None`` se sobrar pouco além do gramado.

    O recorte chega em BGR, como o OpenCV entrega os frames.
    """
    if crop.size == 0:
        return None
    rgb = crop.reshape(-1, 3)[:, ::-1].astype(np.float64) / 255.0
    red, green, blue = rgb.T
    grass = (green > red * GRASS_MARGIN) & (green > blue * GRASS_MARGIN)
    jersey = rgb[~grass]
    if len(jersey) < max(MIN_JERSEY_PIXELS, MIN_JERSEY_FRACTION * len(rgb)):
        return None
    return np.median(jersey, axis=0)


def kmeans_two(points: np.ndarray, iterations: int = 25) -> tuple[np.ndarray, np.ndarray]:
    """K-means com dois grupos e inicialização determinística.

    O primeiro centro é o ponto mais distante da média e o segundo é o mais distante do
    primeiro. Assim o resultado não depende de sorteio e se repete entre execuções.
    """
    points = np.asarray(points, dtype=np.float64)
    if len(points) < 2:
        raise ValueError("são necessários ao menos dois pontos para separar dois grupos")
    first = points[np.argmax(np.linalg.norm(points - points.mean(axis=0), axis=1))]
    second = points[np.argmax(np.linalg.norm(points - first, axis=1))]
    centers = np.stack([first, second])
    for _ in range(iterations):
        distances = np.linalg.norm(points[:, None, :] - centers[None, :, :], axis=2)
        labels = distances.argmin(axis=1)
        updated = np.stack(
            [
                points[labels == k].mean(axis=0) if np.any(labels == k) else centers[k]
                for k in (0, 1)
            ]
        )
        if np.allclose(updated, centers):
            break
        centers = updated
    labels = np.linalg.norm(points[:, None, :] - centers[None, :, :], axis=2).argmin(axis=1)
    return centers, labels


class TeamClassifier:
    """Aprende as duas cores de uniforme e classifica cada jogador em um dos times.

    O ajuste é robusto: depois do k-means, as cores mais distantes de cada time são descartadas
    e o centro é recalculado. O raio de cada time é a distância mediana até o centro, e cores
    fora do raio ampliado dos dois times ficam sem time.
    """

    def __init__(self) -> None:
        self.centers: np.ndarray | None = None
        self.radii: np.ndarray | None = None

    def fit(self, colors: np.ndarray) -> TeamClassifier:
        colors = np.asarray(colors, dtype=np.float64)
        centers, labels = kmeans_two(colors)
        for _ in range(TRIM_ROUNDS):
            distances = np.linalg.norm(colors - centers[labels], axis=1)
            trimmed = []
            for k in (0, 1):
                group = labels == k
                if not group.any():
                    trimmed.append(centers[k])
                    continue
                keep = group & (distances <= np.percentile(distances[group], TRIM_PERCENTILE))
                trimmed.append(colors[keep].mean(axis=0))
            centers = np.stack(trimmed)
            labels = np.linalg.norm(colors[:, None, :] - centers[None, :, :], axis=2).argmin(1)

        # O time A é o de uniforme mais claro, para as cores serem estáveis entre vídeos.
        if centers[0].sum() < centers[1].sum():
            centers, labels = centers[::-1], 1 - labels
        distances = np.linalg.norm(colors - centers[labels], axis=1)
        self.centers = centers
        self.radii = np.array(
            [np.median(distances[labels == k]) if np.any(labels == k) else 0.0 for k in (0, 1)]
        )
        return self

    def predict(self, colors: np.ndarray, *, reject_outliers: bool = True) -> np.ndarray:
        """Time de cada cor; com ``reject_outliers``, ``NO_TEAM`` para cores de fora."""
        if self.centers is None or self.radii is None:
            raise RuntimeError("chame fit antes de predict")
        colors = np.asarray(colors, dtype=np.float64).reshape(-1, 3)
        distances = np.linalg.norm(colors[:, None, :] - self.centers[None, :, :], axis=2)
        teams = distances.argmin(axis=1)
        if reject_outliers:
            limit = np.maximum(self.radii, MIN_TEAM_RADIUS) * OUTLIER_RADIUS_FACTOR
            outside = np.all(distances > limit[None, :], axis=1)
            teams = np.where(outside, NO_TEAM, teams)
        return teams

    def team_colors_hex(self) -> list[str]:
        """Cor aprendida de cada time, em hexadecimal, para desenhar o vídeo."""
        if self.centers is None:
            raise RuntimeError("chame fit antes de pedir as cores")
        return [
            "#{:02X}{:02X}{:02X}".format(*np.clip(center * 255, 0, 255).round().astype(int))
            for center in self.centers
        ]


class TeamVoter:
    """Mantém o time de cada identificador pela maioria dos votos já recebidos."""

    def __init__(self) -> None:
        self._votes: defaultdict[int, Counter[int]] = defaultdict(Counter)

    def update(self, tracker_ids: Sequence[int], teams: Sequence[int]) -> np.ndarray:
        stable = []
        for tracker_id, team in zip(tracker_ids, teams, strict=True):
            votes = self._votes[int(tracker_id)]
            if team != NO_TEAM:
                votes[int(team)] += 1
            stable.append(votes.most_common(1)[0][0] if votes else NO_TEAM)
        return np.array(stable, dtype=int)


def assign_goalkeepers(
    goalkeepers_xy: np.ndarray, players_xy: np.ndarray, player_teams: np.ndarray
) -> np.ndarray:
    """Cada goleiro vai para o time cujo centro está mais perto dele.

    O uniforme do goleiro é diferente do resto do time, então a cor não serve. A posição
    média de cada time é uma aproximação razoável; na Fase 3 ela passa a ser medida em metros.
    """
    goalkeepers_xy = np.asarray(goalkeepers_xy, dtype=np.float64).reshape(-1, 2)
    if len(goalkeepers_xy) == 0:
        return np.array([], dtype=int)
    centroids = {
        team: players_xy[player_teams == team].mean(axis=0)
        for team in (TEAM_A, TEAM_B)
        if np.any(player_teams == team)
    }
    if not centroids:
        return np.full(len(goalkeepers_xy), NO_TEAM, dtype=int)
    teams = list(centroids)
    stacked = np.stack([centroids[team] for team in teams])
    nearest = np.linalg.norm(goalkeepers_xy[:, None, :] - stacked[None, :, :], axis=2).argmin(1)
    return np.array([teams[index] for index in nearest], dtype=int)
