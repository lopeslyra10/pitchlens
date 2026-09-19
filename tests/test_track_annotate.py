import numpy as np
import pytest

from pitchlens.tracking.annotate import DARK_TEXT, LIGHT_TEXT, readable_text_color


def test_text_contrasts_with_the_team_color():
    assert readable_text_color("#F2F2F2") == DARK_TEXT
    assert readable_text_color("#C8F560") == DARK_TEXT
    assert readable_text_color("#1A2A6C") == LIGHT_TEXT
    assert readable_text_color("#B22222") == LIGHT_TEXT


def test_annotator_draws_teams_ids_and_ball_on_a_copy():
    sv = pytest.importorskip("supervision")
    from pitchlens.tracking.annotate import TrackAnnotator

    frame = np.zeros((120, 160, 3), dtype=np.uint8)
    tracked = sv.Detections(
        xyxy=np.array([[10, 10, 40, 90], [80, 20, 110, 100]], dtype=float),
        confidence=np.array([0.9, 0.8]),
        class_id=np.array([2, 2]),
        tracker_id=np.array([3, 7]),
    )
    ball = sv.Detections(xyxy=np.array([[130, 100, 136, 106]], dtype=float))

    annotated = TrackAnnotator(["#F2F2F2", "#B22222"], trace_length=10).annotate(
        frame, tracked, np.array([0, 1]), ball
    )

    assert annotated.any()
    assert not frame.any()


def test_only_the_most_confident_ball_is_kept():
    sv = pytest.importorskip("supervision")
    from pitchlens.tracking.pipeline import best_ball

    balls = sv.Detections(
        xyxy=np.array([[0, 0, 5, 5], [10, 10, 15, 15], [20, 20, 25, 25]], dtype=float),
        confidence=np.array([0.2, 0.6, 0.4]),
    )

    kept = best_ball(balls)

    assert len(kept) == 1 and kept.confidence[0] == 0.6
    assert len(best_ball(balls[[0]])) == 0
