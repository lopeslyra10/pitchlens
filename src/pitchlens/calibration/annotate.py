"""Desenho da calibração sobre o frame (Fase 3).

Mostra três coisas ao mesmo tempo: as linhas do campo projetadas pela homografia (se caem
sobre as linhas do gramado, a calibração está certa), os pontos que o modelo previu, separados
entre os que entraram no ajuste e os que foram descartados, e uma tarja com o estado do frame
e o erro em metros. É a figura da Fase 3 no relatório e no vídeo.
"""

from __future__ import annotations

import numpy as np

from pitchlens.calibration.homography import OK, REPETIDA, FrameCalibration
from pitchlens.calibration.overlay import project_lines
from pitchlens.pitch import FIFA_PITCH, PitchSpec

# Cores em BGR, como o OpenCV desenha. O verde é o mesmo destaque do site (#C8F560).
LINE_COLOR = (96, 245, 200)
REPEATED_LINE_COLOR = (94, 211, 244)
USED_POINT_COLOR = (96, 245, 200)
DROPPED_POINT_COLOR = (107, 107, 255)
BADGE_BACKGROUND = (6, 26, 12)
BADGE_TEXT = (255, 255, 255)

STATUS_LABEL = {OK: "calibrado", REPETIDA: "repetindo o último frame"}
NO_PITCH_LABEL = "sem campo"


class CalibrationAnnotator:
    """Desenha o campo projetado, os pontos previstos e o estado da calibração."""

    def __init__(
        self,
        *,
        pitch: PitchSpec = FIFA_PITCH,
        min_confidence: float = 0.5,
        thickness: int = 2,
    ) -> None:
        self.pitch = pitch
        self.min_confidence = min_confidence
        self.thickness = thickness

    def annotate(
        self,
        frame: np.ndarray,
        calibration: FrameCalibration,
        keypoints: np.ndarray | None = None,
        confidences: np.ndarray | None = None,
    ) -> np.ndarray:
        import cv2

        scene = frame.copy()
        height, width = scene.shape[:2]
        if calibration.homography is not None:
            color = LINE_COLOR if calibration.status == OK else REPEATED_LINE_COLOR
            lines = project_lines(calibration.homography, (width, height), pitch=self.pitch)
            for pieces in lines.values():
                for piece in pieces:
                    cv2.polylines(
                        scene,
                        [np.round(piece).astype(np.int32)],
                        isClosed=False,
                        color=color,
                        thickness=self.thickness,
                        lineType=cv2.LINE_AA,
                    )
        if keypoints is not None:
            self._draw_points(scene, keypoints, confidences)
        return self._draw_badge(scene, calibration)

    def _draw_points(
        self, scene: np.ndarray, keypoints: np.ndarray, confidences: np.ndarray | None
    ) -> None:
        import cv2

        scores = np.ones(len(keypoints)) if confidences is None else np.asarray(confidences)
        for (x, y), score in zip(np.asarray(keypoints, dtype=np.float64), scores, strict=True):
            if not np.isfinite([x, y]).all() or (x == 0 and y == 0):
                continue
            used = score >= self.min_confidence
            cv2.circle(
                scene,
                (round(x), round(y)),
                radius=5 if used else 3,
                color=USED_POINT_COLOR if used else DROPPED_POINT_COLOR,
                thickness=-1 if used else 1,
                lineType=cv2.LINE_AA,
            )

    def _draw_badge(self, scene: np.ndarray, calibration: FrameCalibration) -> np.ndarray:
        import cv2

        parts = [STATUS_LABEL.get(calibration.status, NO_PITCH_LABEL)]
        if calibration.homography is not None:
            parts.append(f"erro {calibration.homography.error_m:.2f} m")
            parts.append(f"{calibration.homography.inliers}/{calibration.points} pontos")
        text = "  ·  ".join(parts)

        font, scale, thickness = cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1
        (text_width, text_height), baseline = cv2.getTextSize(text, font, scale, thickness)
        box = scene[: text_height + baseline + 16, : text_width + 24]
        box[:] = (box * 0.35 + np.array(BADGE_BACKGROUND) * 0.65).astype(scene.dtype)
        cv2.putText(
            scene,
            text,
            (12, text_height + 10),
            font,
            scale,
            BADGE_TEXT,
            thickness,
            lineType=cv2.LINE_AA,
        )
        return scene
