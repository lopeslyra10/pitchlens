"""Junta calibração, linhas do campo e radar numa peça só, para o pipeline usar (Fase 3).

O rastreamento não precisa saber como a homografia é estimada nem como o radar é desenhado:
entrega o frame e as posições dos pés, e recebe a cena pronta.
"""

from __future__ import annotations

import numpy as np

from pitchlens.calibration.annotate import CalibrationAnnotator
from pitchlens.calibration.homography import FrameCalibration, PitchCalibrator
from pitchlens.calibration.radar import Radar, positions_in_metres
from pitchlens.calibration.stats import CalibrationStats
from pitchlens.pitch import FIFA_PITCH, PitchSpec


class FieldView:
    """Calibra o frame, desenha as linhas do campo e o radar 2D com os jogadores."""

    def __init__(
        self,
        group_colors: list[str],
        frame_size: tuple[int, int],
        *,
        pitch: PitchSpec = FIFA_PITCH,
        min_confidence: float = 0.5,
    ) -> None:
        self.calibrator = PitchCalibrator(frame_size, pitch=pitch)
        self.stats = CalibrationStats()
        self.min_confidence = min_confidence
        self._lines = CalibrationAnnotator(pitch=pitch, min_confidence=min_confidence)
        self._radar = Radar(group_colors, pitch=pitch)

    def update(self, keypoints: np.ndarray, confidences: np.ndarray) -> FrameCalibration:
        """Calibra um frame e guarda o resultado nos indicadores."""
        calibration = self.calibrator.update(
            keypoints, confidences, min_confidence=self.min_confidence
        )
        self.stats.update(calibration)
        return calibration

    def draw(
        self,
        scene: np.ndarray,
        calibration: FrameCalibration,
        feet_px: np.ndarray,
        groups: np.ndarray,
    ) -> np.ndarray:
        """Desenha as linhas do campo e cola o radar com os jogadores em metros."""
        scene = self._lines.annotate(scene, calibration)
        positions = positions_in_metres(calibration.homography, feet_px)
        return self._radar.paste(scene, self._radar.render(positions, groups))
