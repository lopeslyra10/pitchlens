import pytest

from pitchlens.detection.stats import DetectionStats


def test_summary_reports_per_frame_average_presence_and_confidence():
    stats = DetectionStats()
    stats.update(["player", "player", "ball"], [0.9, 0.7, 0.4])
    stats.update(["player", "referee"], [0.8, 0.6])

    summary = stats.summary()

    assert summary["frames"] == 2
    assert summary["classes"]["player"] == {
        "por_frame": 1.5,
        "presenca": 1.0,
        "confianca_media": 0.8,
    }
    assert summary["classes"]["ball"]["presenca"] == 0.5
    assert summary["classes"]["referee"]["por_frame"] == 0.5


def test_frames_without_detections_lower_the_averages():
    stats = DetectionStats()
    stats.update(["ball"], [0.5])
    stats.update([], [])

    assert stats.summary()["classes"]["ball"]["presenca"] == 0.5


def test_empty_stats_have_no_classes():
    assert DetectionStats().summary() == {"frames": 0, "classes": {}}


def test_names_and_confidences_must_match():
    with pytest.raises(ValueError):
        DetectionStats().update(["player"], [])
