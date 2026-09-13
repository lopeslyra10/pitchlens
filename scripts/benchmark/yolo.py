"""Adaptador do YOLO para o avaliador comum.

O Ultralytics é distribuído sob AGPL-3.0. Por isso ele fica restrito a esta pasta de
benchmark, fora do pacote ``pitchlens`` (ver ADR-0003).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np


class YOLODetector:
    """YOLO treinado com ``train_yolo.py``, com a mesma interface do ``RFDETRDetector``."""

    def __init__(self, weights: str | Path, *, threshold: float = 0.05, imgsz: int = 640) -> None:
        from ultralytics import YOLO

        self.model = YOLO(str(weights))
        self.threshold = threshold
        self.imgsz = imgsz

    def predict(self, frame: np.ndarray):
        import supervision as sv

        result = self.model.predict(frame, conf=self.threshold, imgsz=self.imgsz, verbose=False)
        return sv.Detections.from_ultralytics(result[0])
