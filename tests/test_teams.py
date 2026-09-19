import numpy as np
import pytest

from pitchlens.tracking.teams import (
    NO_TEAM,
    TEAM_A,
    TEAM_B,
    TeamClassifier,
    TeamVoter,
    assign_goalkeepers,
    jersey_color,
    kmeans_two,
    torso_crop,
)

GRASS_BGR = (40, 140, 50)
WHITE_BGR = (235, 235, 235)
RED_BGR = (40, 40, 210)


def _player_crop(jersey_bgr, grass_fraction=0.3, size=20):
    crop = np.full((size, size, 3), jersey_bgr, dtype=np.uint8)
    grass_rows = int(size * grass_fraction)
    crop[:grass_rows] = GRASS_BGR
    return crop


def test_jersey_color_ignores_grass_and_returns_rgb():
    color = jersey_color(_player_crop(RED_BGR))

    np.testing.assert_allclose(color, np.array([210, 40, 40]) / 255, atol=1e-6)


def test_jersey_color_is_none_when_crop_is_mostly_grass():
    assert jersey_color(_player_crop(RED_BGR, grass_fraction=0.99)) is None
    assert jersey_color(np.zeros((0, 0, 3), dtype=np.uint8)) is None


def test_torso_crop_stays_inside_the_frame():
    frame = np.zeros((100, 100, 3), dtype=np.uint8)

    crop = torso_crop(frame, (-20, -20, 40, 120))

    assert crop.shape[0] > 0 and crop.shape[1] > 0
    assert crop.shape[0] <= 100 and crop.shape[1] <= 100


def test_kmeans_separates_two_color_groups_deterministically():
    rng = np.random.default_rng(0)
    white = np.array([0.92, 0.92, 0.92]) + rng.normal(0, 0.02, (30, 3))
    red = np.array([0.82, 0.16, 0.16]) + rng.normal(0, 0.02, (30, 3))
    points = np.vstack([white, red])

    _, labels = kmeans_two(points)
    _, again = kmeans_two(points)

    assert len(set(labels[:30])) == 1 and len(set(labels[30:])) == 1
    assert labels[0] != labels[-1]
    np.testing.assert_array_equal(labels, again)


def test_kmeans_needs_two_points():
    with pytest.raises(ValueError):
        kmeans_two(np.zeros((1, 3)))


def test_classifier_puts_the_lighter_kit_in_team_a():
    colors = np.array([[0.8, 0.15, 0.15]] * 5 + [[0.95, 0.95, 0.95]] * 5)

    classifier = TeamClassifier().fit(colors)

    assert classifier.predict([[0.93, 0.93, 0.93], [0.78, 0.2, 0.2]]).tolist() == [TEAM_A, TEAM_B]
    assert classifier.team_colors_hex()[0] == "#F2F2F2"


def test_classifier_rejects_colors_far_from_both_kits():
    rng = np.random.default_rng(1)
    white = np.array([0.92, 0.92, 0.92]) + rng.normal(0, 0.02, (40, 3))
    red = np.array([0.8, 0.15, 0.15]) + rng.normal(0, 0.02, (40, 3))
    classifier = TeamClassifier().fit(np.vstack([white, red]))

    referee_black = [0.08, 0.08, 0.1]

    assert classifier.predict([referee_black]).tolist() == [NO_TEAM]
    assert classifier.predict([referee_black], reject_outliers=False).tolist() in ([0], [1])
    assert classifier.predict([[0.9, 0.93, 0.9]]).tolist() == [TEAM_A]


def test_classifier_requires_fit():
    with pytest.raises(RuntimeError):
        TeamClassifier().predict([[0.5, 0.5, 0.5]])


def test_voter_keeps_the_majority_team_per_track():
    voter = TeamVoter()
    voter.update([7], [TEAM_A])
    voter.update([7], [TEAM_A])

    assert voter.update([7], [TEAM_B]).tolist() == [TEAM_A]
    assert voter.update([9], [NO_TEAM]).tolist() == [NO_TEAM]


def test_goalkeeper_joins_the_nearest_team():
    players_xy = np.array([[10, 50], [20, 60], [90, 50], [80, 40]], dtype=float)
    teams = np.array([TEAM_A, TEAM_A, TEAM_B, TEAM_B])

    assigned = assign_goalkeepers(np.array([[2, 50], [98, 45]]), players_xy, teams)

    assert assigned.tolist() == [TEAM_A, TEAM_B]


def test_goalkeeper_without_teams_has_no_team():
    assigned = assign_goalkeepers(np.array([[5, 5]]), np.zeros((0, 2)), np.array([], dtype=int))

    assert assigned.tolist() == [NO_TEAM]
