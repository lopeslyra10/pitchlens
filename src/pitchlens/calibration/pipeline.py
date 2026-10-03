"""Pipeline da calibração: vídeo entra, campo projetado e erro em metros saem (Fase 3).

Uma passada só pelo vídeo: para cada frame o modelo prevê os pontos do gramado, a homografia
é ajustada e suavizada, e o resultado é desenhado. Os indicadores do clipe inteiro (cobertura
e erro em metros) voltam no resumo, que a CLI grava ao lado do vídeo.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

import numpy as np

from pitchlens.calibration.annotate import CalibrationAnnotator
from pitchlens.calibration.homography import PitchCalibrator
from pitchlens.calibration.stats import CalibrationStats

if TYPE_CHECKING:
    from pitchlens.calibration.homography import FrameCalibration

MIN_CONFIDENCE = 0.5


class KeypointModel(Protocol):
    """Qualquer modelo que receba um frame BGR e devolva os pontos do gramado e a confiança."""

    def predict(self, frame: np.ndarray) -> tuple[np.ndarray, np.ndarray]: ...


def calibrate_video(
    model: KeypointModel,
    video: Path,
    output: Path,
    *,
    min_confidence: float = MIN_CONFIDENCE,
    max_seconds: float | None = None,
) -> dict:
    """Gera o vídeo com o campo projetado e devolve os indicadores da calibração."""
    from pitchlens.video import VideoWriter, iter_frames, probe

    info = probe(video)
    calibrator = PitchCalibrator(info.size)
    annotator = CalibrationAnnotator(min_confidence=min_confidence)
    stats = CalibrationStats()
    frames: list[FrameCalibration] = []

    started = time.perf_counter()
    width, height = info.width - info.width % 2, info.height - info.height % 2
    with VideoWriter(output, fps=info.fps, size=(width, height)) as writer:
        for frame in iter_frames(video, max_seconds=max_seconds):
            points, scores = model.predict(frame)
            calibration = calibrator.update(points, scores, min_confidence=min_confidence)
            stats.update(calibration)
            frames.append(calibration)
            scene = annotator.annotate(frame, calibration, points, scores)
            writer.write(scene[:height, :width])
    elapsed = time.perf_counter() - started

    summary = stats.summary()
    summary["fps_processamento"] = round(stats.frames / elapsed, 1) if elapsed else 0.0
    summary["maior_sequencia_sem_campo"] = longest_gap(frames)
    return summary


def longest_gap(frames: list[FrameCalibration]) -> int:
    """Maior sequência de frames seguidos sem calibração utilizável.

    Importa mais que o total: 10 frames perdidos espalhados somem na suavização, enquanto 10
    seguidos deixam um buraco visível no radar.
    """
    longest = current = 0
    for calibration in frames:
        current = 0 if calibration.usable else current + 1
        longest = max(longest, current)
    return longest
