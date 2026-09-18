"""Estatísticas de detecção para vídeos sem anotações.

Sem rótulos não existe mAP. Para comparar o comportamento do detector entre as imagens de
teste (câmera de transmissão) e vídeos com outros ângulos, usamos indicadores indiretos:
quantos objetos de cada classe aparecem por frame, em quantos frames a bola é encontrada e
com que confiança. Quedas nesses números indicam que o modelo está fora do domínio do treino.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Sequence

import numpy as np


class DetectionStats:
    """Acumula as detecções frame a frame e resume por classe."""

    def __init__(self) -> None:
        self.frames = 0
        self._counts: Counter[str] = Counter()
        self._frames_with: Counter[str] = Counter()
        self._confidences: defaultdict[str, list[float]] = defaultdict(list)

    def update(self, names: Sequence[str], confidences: Sequence[float] | np.ndarray) -> None:
        """Registra as detecções de um frame: nome da classe e confiança de cada uma."""
        if len(names) != len(confidences):
            raise ValueError("cada detecção precisa de um nome e de uma confiança")
        self.frames += 1
        self._counts.update(names)
        self._frames_with.update(set(names))
        for name, confidence in zip(names, confidences, strict=True):
            self._confidences[name].append(float(confidence))

    def summary(self) -> dict:
        """Médias por frame, presença (fração de frames com a classe) e confiança média."""
        if self.frames == 0:
            return {"frames": 0, "classes": {}}
        classes = {
            name: {
                "por_frame": round(self._counts[name] / self.frames, 2),
                "presenca": round(self._frames_with[name] / self.frames, 3),
                "confianca_media": round(float(np.mean(self._confidences[name])), 3),
            }
            for name in sorted(self._counts)
        }
        return {"frames": self.frames, "classes": classes}
