"""Máscara do campo: quem está no gramado e onde o gramado fica na imagem (Fase 3).

O detector marca como jogador quem está no banco, na borda do campo e às vezes na
arquibancada. Sem filtrar, essas pessoas entram na contagem e deformam a formação. Com a
homografia a decisão fica simples e explicável: o pé do jogador é levado para metros e basta
perguntar se ele caiu dentro das linhas.

A mesma homografia desenha o contorno do gramado na imagem, usado na prévia e no radar.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from pitchlens.calibration.homography import Homography
from pitchlens.pitch import FIFA_PITCH, PitchSpec

# Tolerância em metros: o goleiro pisa a linha, o lateral cobra o lateral de fora do campo e a
# própria homografia erra alguns decímetros. Cortar exatamente na linha perderia jogada válida.
PITCH_MARGIN_M = 2.0
# Pontos por linha ao desenhar o contorno: as linhas do campo são retas na imagem, mas quando
# o horizonte corta o campo parte delas deixa de ter resultado finito e precisa ser descartada.
OUTLINE_SAMPLES = 40


def feet(boxes: Sequence[Sequence[float]]) -> np.ndarray:
    """Ponto de apoio de cada caixa ``(x1, y1, x2, y2)``: o meio da base.

    É o ponto que toca o gramado, e por isso o único que a homografia pode converter em
    metros — o centro da caixa flutua acima do plano do campo.
    """
    array = np.asarray(boxes, dtype=np.float64).reshape(-1, 4)
    return np.stack([(array[:, 0] + array[:, 2]) / 2.0, array[:, 3]], axis=1)


def inside_pitch(
    homography: Homography,
    points: Sequence[Sequence[float]],
    *,
    margin_m: float = PITCH_MARGIN_M,
    pitch: PitchSpec = FIFA_PITCH,
) -> np.ndarray:
    """Diz, para cada ponto da imagem, se ele cai dentro do campo (com tolerância)."""
    mapped = homography.to_pitch(points)
    finite = np.isfinite(mapped).all(axis=1)
    inside = np.zeros(len(mapped), dtype=bool)
    x, y = mapped[finite, 0], mapped[finite, 1]
    inside[finite] = (
        (x >= -margin_m)
        & (x <= pitch.length + margin_m)
        & (y >= -margin_m)
        & (y <= pitch.width + margin_m)
    )
    return inside


def on_pitch(
    homography: Homography,
    boxes: Sequence[Sequence[float]],
    *,
    margin_m: float = PITCH_MARGIN_M,
    pitch: PitchSpec = FIFA_PITCH,
) -> np.ndarray:
    """Máscara das caixas cujo ponto de apoio está no gramado."""
    boxes = np.asarray(boxes, dtype=np.float64).reshape(-1, 4)
    if len(boxes) == 0:
        return np.zeros(0, dtype=bool)
    return inside_pitch(homography, feet(boxes), margin_m=margin_m, pitch=pitch)


def pitch_outline(
    homography: Homography,
    *,
    pitch: PitchSpec = FIFA_PITCH,
    samples: int = OUTLINE_SAMPLES,
) -> np.ndarray:
    """Contorno do gramado na imagem, em pixels, para desenhar por cima do vídeo.

    As quatro linhas são amostradas em vez de usar só os cantos: assim o contorno continua
    desenhável quando um canto cai atrás da câmera e some da imagem.
    """
    corners = [
        (0.0, 0.0),
        (pitch.length, 0.0),
        (pitch.length, pitch.width),
        (0.0, pitch.width),
    ]
    border = []
    for start, end in zip(corners, corners[1:] + corners[:1], strict=True):
        steps = np.linspace(0.0, 1.0, samples, endpoint=False)[:, None]
        border.append(np.array(start) + steps * (np.array(end) - np.array(start)))
    projected = homography.to_image(np.vstack(border))
    return projected[np.isfinite(projected).all(axis=1)]
