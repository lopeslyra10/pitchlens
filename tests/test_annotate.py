import numpy as np
import pytest

sv = pytest.importorskip("supervision")

from pitchlens.detection.annotate import (  # noqa: E402
    DetectionAnnotator,
    class_names_of,
    palette_index,
)


def _detections():
    return sv.Detections(
        xyxy=np.array([[10, 10, 40, 80], [60, 60, 66, 66]], dtype=float),
        class_id=np.array([2, 0]),
        confidence=np.array([0.9, 0.6]),
        data={"class_name": np.array(["player", "ball"])},
    )


def test_annotator_draws_on_a_copy_of_the_frame():
    frame = np.zeros((120, 120, 3), dtype=np.uint8)

    annotated = DetectionAnnotator().annotate(frame, _detections())

    assert annotated.any()
    assert not frame.any()


def test_frame_without_detections_is_returned_unchanged():
    frame = np.full((50, 50, 3), 7, dtype=np.uint8)

    annotated = DetectionAnnotator().annotate(frame, sv.Detections.empty())

    np.testing.assert_array_equal(annotated, frame)


def test_class_names_and_palette_positions():
    assert class_names_of(_detections()) == ["player", "ball"]
    assert palette_index("ball") == 0
    assert palette_index("bandeirinha") == 4
