"""Detectores de objetos usados pelo pipeline.

O pacote não importa PyTorch nem RF-DETR ao ser carregado: essas dependências ficam no extra
``cv`` e só são importadas quando um detector é criado. Assim a CLI e os testes leves rodam
em qualquer máquina.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol

import numpy as np

if TYPE_CHECKING:
    import supervision as sv

RFDETR_SIZES = {
    "nano": "RFDETRNano",
    "small": "RFDETRSmall",
    "medium": "RFDETRMedium",
    "large": "RFDETRLarge",
}


class Detector(Protocol):
    """Qualquer modelo que receba um frame BGR e devolva detecções do ``supervision``."""

    def predict(self, frame: np.ndarray) -> sv.Detections: ...


class RFDETRDetector:
    """RF-DETR ajustado para futebol, carregado a partir de um checkpoint do treino.

    O ``from_checkpoint`` do RF-DETR descobre o tamanho do modelo e as classes pelo próprio
    arquivo, então quem usa o detector não precisa saber com qual variante o treino foi feito.
    """

    def __init__(self, weights: str | Path, *, threshold: float = 0.35) -> None:
        from rfdetr.detr import RFDETR

        self.model = RFDETR.from_checkpoint(str(weights))
        self.threshold = threshold

    @property
    def name(self) -> str:
        """Nome legível da variante carregada, como "RF-DETR Medium"."""
        class_name = type(self.model).__name__
        sizes = {model_class: size for size, model_class in RFDETR_SIZES.items()}
        return f"RF-DETR {sizes[class_name].capitalize()}" if class_name in sizes else class_name

    def predict(self, frame: np.ndarray) -> sv.Detections:
        # O OpenCV entrega BGR e o RF-DETR espera RGB.
        rgb = np.ascontiguousarray(frame[:, :, ::-1])
        return self.model.predict(rgb, threshold=self.threshold)
