"""Desenho das detecções sobre o frame, no estilo das transmissões esportivas."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from pitchlens.detection.classes import FALLBACK_COLOR, OBJECT_CLASSES, label_for

if TYPE_CHECKING:
    import supervision as sv

_PALETTE_ORDER = list(OBJECT_CLASSES)
LABEL_TEXT_COLOR = "#0C1A06"


def class_names_of(detections: sv.Detections) -> list[str]:
    """Nome da classe de cada detecção, com o id numérico quando o modelo não informa nomes."""
    names = detections.data.get("class_name")
    if names is None:
        return [str(class_id) for class_id in detections.class_id]
    return [str(name) for name in names]


def palette_index(name: str) -> int:
    """Posição da cor da classe na paleta; classes desconhecidas usam a última cor."""
    return _PALETTE_ORDER.index(name) if name in OBJECT_CLASSES else len(_PALETTE_ORDER)


class DetectionAnnotator:
    """Elipse sob pessoas, triângulo sobre a bola e rótulo com classe e confiança."""

    def __init__(self, *, show_confidence: bool = True) -> None:
        import supervision as sv

        palette = sv.ColorPalette.from_hex(
            [OBJECT_CLASSES[name].color for name in _PALETTE_ORDER] + [FALLBACK_COLOR]
        )
        self.show_confidence = show_confidence
        self._ellipse = sv.EllipseAnnotator(color=palette, thickness=2)
        self._triangle = sv.TriangleAnnotator(color=palette, base=18, height=15)
        self._label = sv.LabelAnnotator(
            color=palette,
            text_color=sv.Color.from_hex(LABEL_TEXT_COLOR),
            text_scale=0.4,
            text_thickness=1,
            text_padding=3,
            text_position=sv.Position.BOTTOM_CENTER,
        )

    def _labels(self, detections: sv.Detections, names: list[str]) -> list[str]:
        if not self.show_confidence or detections.confidence is None:
            return [label_for(name) for name in names]
        return [
            f"{label_for(name)} {confidence:.2f}"
            for name, confidence in zip(names, detections.confidence, strict=True)
        ]

    def annotate(self, frame: np.ndarray, detections: sv.Detections) -> np.ndarray:
        """Devolve uma cópia do frame com as detecções desenhadas."""
        scene = frame.copy()
        if len(detections) == 0:
            return scene
        names = class_names_of(detections)
        is_ball = np.array([name == "ball" for name in names])
        colors = np.array([palette_index(name) for name in names])

        people, ball = detections[~is_ball], detections[is_ball]
        people_names = [name for name, flag in zip(names, is_ball, strict=True) if not flag]

        scene = self._ellipse.annotate(scene, people, custom_color_lookup=colors[~is_ball])
        scene = self._label.annotate(
            scene,
            people,
            labels=self._labels(people, people_names),
            custom_color_lookup=colors[~is_ball],
        )
        return self._triangle.annotate(scene, ball, custom_color_lookup=colors[is_ball])
