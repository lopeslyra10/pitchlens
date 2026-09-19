"""Desenho dos jogadores rastreados: cor do time, número do identificador e rastro."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from pitchlens.detection.classes import OBJECT_CLASSES

if TYPE_CHECKING:
    import supervision as sv

REFEREE_GROUP, UNKNOWN_GROUP = 2, 3
UNKNOWN_COLOR = "#9AA5A0"
DARK_TEXT, LIGHT_TEXT = "#0C1A06", "#FFFFFF"


def readable_text_color(hex_color: str) -> str:
    """Texto escuro sobre cores claras e claro sobre cores escuras (luminância relativa)."""
    red, green, blue = (int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5))
    luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
    return DARK_TEXT if luminance > 0.5 else LIGHT_TEXT


class TrackAnnotator:
    """Elipse e rastro na cor do time, rótulo com o número e triângulo sobre a bola.

    Cada detecção recebe um grupo: 0 e 1 são os times, 2 é arbitragem e 3 é desconhecido.
    """

    def __init__(self, team_colors: list[str], *, trace_length: int) -> None:
        import supervision as sv

        colors = [*team_colors, OBJECT_CLASSES["referee"].color, UNKNOWN_COLOR]
        palette = sv.ColorPalette.from_hex(colors)
        text_palette = sv.ColorPalette.from_hex([readable_text_color(c) for c in colors])
        self._ellipse = sv.EllipseAnnotator(color=palette, thickness=2)
        self._trace = sv.TraceAnnotator(
            color=palette,
            position=sv.Position.BOTTOM_CENTER,
            trace_length=trace_length,
            thickness=2,
        )
        self._label = sv.LabelAnnotator(
            color=palette,
            text_color=text_palette,
            text_scale=0.4,
            text_thickness=1,
            text_padding=3,
            text_position=sv.Position.BOTTOM_CENTER,
        )
        self._ball = sv.TriangleAnnotator(
            color=sv.Color.from_hex(OBJECT_CLASSES["ball"].color),
            base=18,
            height=15,
            color_lookup=sv.ColorLookup.INDEX,
        )

    def annotate(
        self,
        frame: np.ndarray,
        tracked: sv.Detections,
        groups: np.ndarray,
        ball: sv.Detections,
    ) -> np.ndarray:
        """Devolve uma cópia do frame com jogadores rastreados e bola desenhados."""
        scene = frame.copy()
        if len(tracked):
            lookup = np.asarray(groups, dtype=int)
            labels = [f"#{tracker_id}" for tracker_id in tracked.tracker_id]
            scene = self._trace.annotate(scene, tracked, custom_color_lookup=lookup)
            scene = self._ellipse.annotate(scene, tracked, custom_color_lookup=lookup)
            scene = self._label.annotate(scene, tracked, labels=labels, custom_color_lookup=lookup)
        if len(ball):
            scene = self._ball.annotate(scene, ball)
        return scene
