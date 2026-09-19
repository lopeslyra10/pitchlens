import pytest

from pitchlens.tracking.stats import TrackingStats


def test_stable_tracks_produce_one_id_per_visible_player():
    stats = TrackingStats(fps=10)
    for _ in range(20):
        stats.update([1, 2], [0, 1])

    summary = stats.summary()

    assert summary["ids_unicos"] == 2
    assert summary["ids_por_visivel"] == 1.0
    assert summary["duracao_mediana_s"] == 2.0
    assert summary["rastros_curtos_pct"] == 0.0
    assert summary["por_time_por_frame"] == {"0": 1.0, "1": 1.0}


def test_identity_switches_show_up_as_short_tracks():
    stats = TrackingStats(fps=10)
    for frame in range(20):
        stats.update([100 + frame], [0])

    summary = stats.summary()

    assert summary["ids_unicos"] == 20
    assert summary["ids_por_visivel"] == 20.0
    assert summary["rastros_curtos_pct"] == 1.0


def test_invalid_input_is_rejected():
    with pytest.raises(ValueError):
        TrackingStats(fps=0)
    with pytest.raises(ValueError):
        TrackingStats(fps=25).update([1], [])
    assert TrackingStats(fps=25).summary() == {"frames": 0}
