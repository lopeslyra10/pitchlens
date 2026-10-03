"""Modelo de pontos do gramado: do frame para os 32 pontos do campo (Fase 3).

O RF-DETR em modo keypoints trata o campo como um objeto só, com 32 pontos presos a ele.
Cada ponto vem com uma confiança própria, e é ela que diz quais pontos entram na homografia:
num close na grande área metade dos pontos não está no quadro, e o modelo marca isso.

Como no detector de jogadores, o PyTorch só é importado quando o modelo é criado, para a CLI
e os testes leves rodarem em qualquer máquina.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from pitchlens.pitch import KEYPOINT_ORDER

if TYPE_CHECKING:
    import supervision as sv

NUM_KEYPOINTS = len(KEYPOINT_ORDER)


def pitch_keypoints(
    xy: np.ndarray,
    keypoint_confidence: np.ndarray,
    detection_confidence: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Escolhe o campo mais provável da previsão e devolve seus pontos e confianças.

    O modelo pode devolver mais de um campo no mesmo frame (o gramado aparece em pedaços
    quando a câmera corta). Fica o de maior confiança; sem nenhum, todas as confianças saem
    zeradas e a calibração do frame é descartada mais adiante.
    """
    if len(detection_confidence) == 0:
        return np.zeros((NUM_KEYPOINTS, 2)), np.zeros(NUM_KEYPOINTS)

    best = int(np.argmax(detection_confidence))
    points = np.asarray(xy[best], dtype=np.float64)
    scores = np.asarray(keypoint_confidence[best], dtype=np.float64)
    if points.shape != (NUM_KEYPOINTS, 2) or scores.shape != (NUM_KEYPOINTS,):
        raise ValueError(
            f"o modelo devolveu {points.shape[0]} pontos, e o campo do projeto tem {NUM_KEYPOINTS}"
        )
    return points, scores


class PitchKeypointDetector:
    """RF-DETR de keypoints ajustado ao gramado, carregado de um checkpoint do treino."""

    def __init__(
        self, weights: str | Path, *, threshold: float = 0.3, resolution: int | None = None
    ) -> None:
        from rfdetr.detr import RFDETR

        options = {"resolution": resolution} if resolution else {}
        self.model = RFDETR.from_checkpoint(str(weights), **options)
        self.threshold = threshold

    @property
    def name(self) -> str:
        return type(self.model).__name__

    def predict(self, frame: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Pontos do gramado em pixels ``(32, 2)`` e a confiança de cada um ``(32,)``."""
        # O OpenCV entrega BGR e o RF-DETR espera RGB.
        rgb = np.ascontiguousarray(frame[:, :, ::-1])
        result: sv.KeyPoints = self.model.predict(
            rgb, threshold=self.threshold, include_source_image=False
        )
        return pitch_keypoints(result.xy, result.keypoint_confidence, result.detection_confidence)
