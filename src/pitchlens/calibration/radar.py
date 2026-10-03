"""Radar 2D: o campo visto de cima, no canto do vídeo (Fase 3).

É o que a homografia serve para mostrar. Cada jogador vira um ponto na posição real em
metros, na cor do seu time, sobre o desenho do campo. Ao lado do vídeo, o radar deixa
conferir a calibração num relance: se os pontos saem do gramado ou se encavalam, a
homografia está errada.

Quem está fora das linhas não entra: banco, arbitragem na borda e torcida não fazem parte da
leitura tática (ver ``mask.py``).
"""

from __future__ import annotations

import numpy as np

from pitchlens.calibration.homography import Homography
from pitchlens.calibration.mask import PITCH_MARGIN_M
from pitchlens.calibration.overlay import pitch_to_radar
from pitchlens.pitch import FIFA_PITCH, PitchSpec

# O painel segue a proporção do campo (105 x 68), para o desenho não sobrar nem faltar.
RADAR_SIZE = (420, 282)
RADAR_PADDING = 14
# Cores em BGR. O fundo é o verde escuro do site, e as linhas, brancas com transparência.
RADAR_BACKGROUND = (26, 48, 18)
RADAR_LINES = (210, 235, 220)
PLAYER_RADIUS = 5
BALL_COLOR = (255, 255, 255)
PANEL_OPACITY = 0.82
PANEL_MARGIN = 16


def hex_to_bgr(hex_color: str) -> tuple[int, int, int]:
    """Converte "#C8F560" para a ordem BGR que o OpenCV desenha."""
    red, green, blue = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    return (blue, green, red)


class Radar:
    """Desenha o campo visto de cima com os jogadores na posição em metros."""

    def __init__(
        self,
        group_colors: list[str],
        *,
        size: tuple[int, int] = RADAR_SIZE,
        padding: int = RADAR_PADDING,
        pitch: PitchSpec = FIFA_PITCH,
        margin_m: float = PITCH_MARGIN_M,
    ) -> None:
        self.size = size
        self.padding = padding
        self.pitch = pitch
        self.margin_m = margin_m
        self.colors = [hex_to_bgr(color) for color in group_colors]
        self._background = self._draw_pitch()

    def _draw_pitch(self) -> np.ndarray:
        import cv2

        width, height = self.size
        panel = np.full((height, width, 3), RADAR_BACKGROUND, dtype=np.uint8)
        for line in self.pitch.lines().values():
            points = pitch_to_radar(line, self.size, pitch=self.pitch, padding=self.padding)
            cv2.polylines(
                panel,
                [np.round(points).astype(np.int32)],
                isClosed=False,
                color=RADAR_LINES,
                thickness=1,
                lineType=cv2.LINE_AA,
            )
        return panel

    def render(self, positions_m: np.ndarray, groups: np.ndarray) -> np.ndarray:
        """Radar com um ponto por posição, na cor do grupo (time, arbitragem, desconhecido)."""
        import cv2

        panel = self._background.copy()
        positions_m = np.asarray(positions_m, dtype=np.float64).reshape(-1, 2)
        groups = np.asarray(groups, dtype=int).reshape(-1)
        points = pitch_to_radar(positions_m, self.size, pitch=self.pitch, padding=self.padding)
        for (x, y), (metre_x, metre_y), group in zip(points, positions_m, groups, strict=True):
            if not np.isfinite([x, y]).all():
                continue
            if not self.pitch.contains(metre_x, metre_y, margin=self.margin_m):
                continue
            color = self.colors[group] if 0 <= group < len(self.colors) else BALL_COLOR
            cv2.circle(panel, (round(x), round(y)), PLAYER_RADIUS, color, -1, lineType=cv2.LINE_AA)
            cv2.circle(
                panel, (round(x), round(y)), PLAYER_RADIUS, RADAR_LINES, 1, lineType=cv2.LINE_AA
            )
        return panel

    def paste(self, scene: np.ndarray, panel: np.ndarray, margin: int = PANEL_MARGIN) -> np.ndarray:
        """Cola o radar no canto inferior direito do frame, com leve transparência."""
        height, width = scene.shape[:2]
        panel_height, panel_width = panel.shape[:2]
        if panel_height + 2 * margin > height or panel_width + 2 * margin > width:
            return scene
        top, left = height - panel_height - margin, width - panel_width - margin
        region = scene[top : top + panel_height, left : left + panel_width]
        blended = region * (1.0 - PANEL_OPACITY) + panel * PANEL_OPACITY
        scene[top : top + panel_height, left : left + panel_width] = blended.astype(scene.dtype)
        return scene


def positions_in_metres(homography: Homography | None, feet_px: np.ndarray) -> np.ndarray:
    """Posição em metros de cada jogador; sem homografia, tudo sai como ``NaN``."""
    feet_px = np.asarray(feet_px, dtype=np.float64).reshape(-1, 2)
    if homography is None or len(feet_px) == 0:
        return np.full((len(feet_px), 2), np.nan)
    return homography.to_pitch(feet_px)
