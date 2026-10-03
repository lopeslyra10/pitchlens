"""Indicadores da calibração ao longo de um vídeo (Fase 3).

A homografia é julgada por duas coisas: quantos frames ela cobre e quanto erra, em metros. O
erro em metros é o número que importa para a leitura tática — um erro de 2 m já troca um
jogador de linha —, enquanto erro em pixels muda com o zoom e não diz nada sobre o campo.
"""

from __future__ import annotations

import numpy as np

from pitchlens.calibration.homography import OK, REPETIDA, SEM_CAMPO, FrameCalibration


class CalibrationStats:
    """Acumula, frame a frame, o estado da calibração e o erro de reprojeção."""

    def __init__(self) -> None:
        self.frames = 0
        self._status: dict[str, int] = {OK: 0, REPETIDA: 0, SEM_CAMPO: 0}
        self._errors: list[float] = []
        self._points: list[int] = []

    def update(self, calibration: FrameCalibration) -> None:
        self.frames += 1
        self._status[calibration.status] = self._status.get(calibration.status, 0) + 1
        self._points.append(calibration.points)
        if calibration.status == OK and calibration.homography is not None:
            self._errors.append(calibration.homography.error_m)

    def summary(self) -> dict:
        if self.frames == 0:
            return {"frames": 0}
        calibrated = self._status[OK] + self._status[REPETIDA]
        errors = np.array(self._errors, dtype=np.float64)
        return {
            "frames": self.frames,
            "cobertura_pct": round(calibrated / self.frames, 3),
            "frames_ajustados": self._status[OK],
            "frames_repetidos": self._status[REPETIDA],
            "frames_sem_campo": self._status[SEM_CAMPO],
            "pontos_por_frame": round(float(np.mean(self._points)), 1),
            "erro_mediano_m": round(float(np.median(errors)), 2) if len(errors) else None,
            "erro_p95_m": round(float(np.percentile(errors, 95)), 2) if len(errors) else None,
            "erro_maximo_m": round(float(errors.max()), 2) if len(errors) else None,
        }
