import numpy as np
import pytest

from pitchlens.calibration.homography import Homography, solve_homography
from pitchlens.calibration.overlay import pitch_to_radar
from pitchlens.calibration.radar import hex_to_bgr, positions_in_metres
from pitchlens.pitch import FIFA_PITCH

PITCH_QUAD = np.array([[0.0, 0.0], [105.0, 0.0], [105.0, 68.0], [0.0, 68.0]])
IMAGE_QUAD = np.array([[320.0, 180.0], [980.0, 190.0], [1240.0, 650.0], [60.0, 620.0]])


@pytest.fixture
def homography() -> Homography:
    return Homography(solve_homography(IMAGE_QUAD, PITCH_QUAD), 0.2, 20, 20)


def test_hex_to_bgr_reverses_the_channels():
    assert hex_to_bgr("#C8F560") == (0x60, 0xF5, 0xC8)


def test_pitch_to_radar_keeps_the_field_inside_the_panel():
    corners = pitch_to_radar(PITCH_QUAD, (420, 282), padding=14)

    np.testing.assert_allclose(corners[0], [14.0, 14.3], atol=0.5)
    np.testing.assert_allclose(corners[2], [406.0, 267.7], atol=0.5)


def test_pitch_to_radar_keeps_the_pitch_proportions():
    # Painel largo demais: o campo é centrado, e não esticado.
    corners = pitch_to_radar(PITCH_QUAD, (600, 282), padding=14)
    width = corners[1, 0] - corners[0, 0]
    height = corners[2, 1] - corners[1, 1]

    assert width / height == pytest.approx(FIFA_PITCH.length / FIFA_PITCH.width, rel=1e-6)
    assert corners[0, 0] == pytest.approx(600 - corners[1, 0])


def test_positions_in_metres_follow_the_homography(homography):
    centre_px = homography.to_image([FIFA_PITCH.center])

    np.testing.assert_allclose(positions_in_metres(homography, centre_px), [FIFA_PITCH.center])


def test_positions_without_calibration_are_unknown():
    positions = positions_in_metres(None, np.array([[10.0, 20.0], [30.0, 40.0]]))

    assert positions.shape == (2, 2)
    assert np.isnan(positions).all()


def test_radar_drawing_places_players_on_the_pitch(homography):
    pytest.importorskip("cv2")
    from pitchlens.calibration.radar import Radar

    radar = Radar(["#C8F560", "#FF6B6B", "#F4D35E", "#9AA5A0"])
    empty = radar.render(np.zeros((0, 2)), np.zeros(0, dtype=int))
    with_players = radar.render(np.array([FIFA_PITCH.center]), np.array([0]))

    assert empty.shape == (282, 420, 3)
    assert (with_players != empty).any()
    # O ponto cai no centro do painel, onde fica a marca do meio-campo.
    assert (with_players[130:142, 200:220] != empty[130:142, 200:220]).any()


def test_radar_ignores_whoever_is_outside_the_lines():
    pytest.importorskip("cv2")
    from pitchlens.calibration.radar import Radar

    radar = Radar(["#C8F560", "#FF6B6B"])
    empty = radar.render(np.zeros((0, 2)), np.zeros(0, dtype=int))
    outside = radar.render(np.array([[-20.0, -30.0], [np.nan, np.nan]]), np.array([0, 1]))

    np.testing.assert_array_equal(outside, empty)


def test_radar_panel_is_pasted_in_the_corner():
    pytest.importorskip("cv2")
    from pitchlens.calibration.radar import Radar

    radar = Radar(["#C8F560", "#FF6B6B"])
    scene = np.zeros((720, 1280, 3), dtype=np.uint8)
    panel = radar.render(np.array([FIFA_PITCH.center]), np.array([0]))

    pasted = radar.paste(scene.copy(), panel)

    assert pasted[:400, :800].sum() == 0
    assert pasted[-100:, -100:].any()


def test_a_panel_bigger_than_the_frame_is_left_out():
    pytest.importorskip("cv2")
    from pitchlens.calibration.radar import Radar

    radar = Radar(["#C8F560", "#FF6B6B"])
    tiny = np.zeros((100, 100, 3), dtype=np.uint8)

    pasted = radar.paste(tiny, radar.render(np.zeros((0, 2)), np.zeros(0, dtype=int)))

    assert not pasted.any()
