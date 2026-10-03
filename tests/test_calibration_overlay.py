import numpy as np
import pytest

from pitchlens.calibration.detector import pitch_keypoints
from pitchlens.calibration.homography import (
    OK,
    SEM_CAMPO,
    FrameCalibration,
    Homography,
    solve_homography,
)
from pitchlens.calibration.overlay import (
    project_lines,
    radar_positions,
    split_polyline,
    visible,
)
from pitchlens.calibration.pipeline import longest_gap
from pitchlens.pitch import FIFA_PITCH, KEYPOINT_ORDER

FRAME_SIZE = (1280, 720)
PITCH_QUAD = np.array([[0.0, 0.0], [105.0, 0.0], [105.0, 68.0], [0.0, 68.0]])
IMAGE_QUAD = np.array([[320.0, 180.0], [980.0, 190.0], [1240.0, 650.0], [60.0, 620.0]])


@pytest.fixture
def homography() -> Homography:
    matrix = solve_homography(IMAGE_QUAD, PITCH_QUAD)
    assert matrix is not None
    return Homography(matrix, 0.2, 20, 20)


def test_pitch_lines_cover_the_markings_that_the_camera_sees():
    lines = FIFA_PITCH.lines()

    assert set(lines) == {
        "contorno",
        "meio_campo",
        "circulo_central",
        "grande_area_esquerda",
        "grande_area_direita",
        "pequena_area_esquerda",
        "pequena_area_direita",
    }
    np.testing.assert_allclose(lines["contorno"][0], lines["contorno"][-1])
    np.testing.assert_allclose(lines["meio_campo"], [[52.5, 0.0], [52.5, 68.0]])
    assert all(FIFA_PITCH.contains(x, y) for line in lines.values() for x, y in line)


def test_center_circle_keeps_its_radius():
    circle = FIFA_PITCH.lines(circle_samples=16)

    distances = np.linalg.norm(circle["circulo_central"] - FIFA_PITCH.center, axis=1)
    assert len(circle["circulo_central"]) == 17
    np.testing.assert_allclose(distances, 9.15)


def test_split_polyline_keeps_a_whole_line_together():
    # Uma linha longe do horizonte é um pedaço só, por mais pixels que ela cubra.
    line = np.array([[0.0, 0.0], [900.0, 400.0], [2000.0, 900.0]])

    pieces = split_polyline(line, np.array([1.0, 1.0, 1.0]))

    assert len(pieces) == 1
    np.testing.assert_allclose(pieces[0], line)


def test_split_polyline_breaks_where_the_divider_changes_sign():
    # Entre o segundo e o terceiro ponto a linha passa para trás da câmera.
    line = np.array([[0.0, 0.0], [10.0, 5.0], [1270.0, 700.0], [1260.0, 690.0]])

    pieces = split_polyline(line, np.array([2.0, 0.5, -0.5, -2.0]))

    assert len(pieces) == 2
    assert len(pieces[0]) == len(pieces[1]) == 2


def test_split_polyline_breaks_on_the_horizon_itself():
    line = np.array([[0.0, 0.0], [10.0, 5.0], [np.nan, np.nan], [20.0, 10.0], [30.0, 15.0]])

    pieces = split_polyline(line, np.array([1.0, 1.0, 0.0, 1.0, 1.0]))

    assert len(pieces) == 2


def test_split_polyline_drops_pieces_with_a_single_point():
    line = np.array([[0.0, 0.0], [np.nan, np.nan], [10.0, 10.0]])

    assert split_polyline(line, np.array([1.0, 0.0, 1.0])) == []


def test_visible_only_accepts_lines_near_the_image():
    inside = np.array([[10.0, 10.0], [100.0, 100.0]])
    far_away = np.array([[-5000.0, -5000.0], [-4000.0, -4000.0]])

    assert visible(inside, FRAME_SIZE)
    assert not visible(far_away, FRAME_SIZE)


def test_project_lines_puts_the_markings_back_on_the_image(homography):
    lines = project_lines(homography, FRAME_SIZE)

    assert set(lines) == set(FIFA_PITCH.lines())
    corners = lines["contorno"][0]
    for corner in IMAGE_QUAD:
        assert np.linalg.norm(corners - corner, axis=1).min() < 1e-6


def test_project_lines_leaves_out_what_is_far_from_the_image():
    # Close no canto esquerdo: a 20 px por metro, a área do outro lado fica a 1 770 px do
    # quadro de 40 px e não precisa ser desenhada. A linha segue inteira, só longe.
    to_image = np.array([[20.0, 0.0, 0.0], [0.0, 20.0, 0.0], [0.0, 0.0, 1.0]])
    lines = project_lines(Homography(np.linalg.inv(to_image), 0.3, 10, 10), (40, 30))

    assert "contorno" in lines
    assert "grande_area_direita" not in lines


def test_radar_positions_map_the_pitch_into_the_radar(homography):
    corners = homography.to_image(FIFA_PITCH.lines()["contorno"][:4])

    radar = radar_positions(homography, corners, (420, 280), padding=10)

    np.testing.assert_allclose(radar[0], [10.0, 10.5], atol=0.6)
    np.testing.assert_allclose(radar[2], [410.0, 269.5], atol=0.6)


def test_radar_positions_reject_a_radar_smaller_than_its_margin(homography):
    with pytest.raises(ValueError, match="pequeno demais"):
        radar_positions(homography, np.zeros((1, 2)), (10, 10), padding=10)


def test_pitch_keypoints_takes_the_most_confident_field():
    xy = np.stack([np.full((len(KEYPOINT_ORDER), 2), 1.0), np.full((len(KEYPOINT_ORDER), 2), 2.0)])
    keypoint_confidence = np.stack([np.zeros(len(KEYPOINT_ORDER)), np.ones(len(KEYPOINT_ORDER))])

    points, scores = pitch_keypoints(xy, keypoint_confidence, np.array([0.3, 0.9]))

    np.testing.assert_allclose(points, 2.0)
    np.testing.assert_allclose(scores, 1.0)


def test_pitch_keypoints_handles_a_frame_without_a_field():
    points, scores = pitch_keypoints(np.zeros((0, 32, 2)), np.zeros((0, 32)), np.zeros(0))

    assert points.shape == (len(KEYPOINT_ORDER), 2)
    assert not scores.any()


def test_pitch_keypoints_rejects_a_model_with_another_number_of_points():
    with pytest.raises(ValueError, match="o campo do projeto tem 32"):
        pitch_keypoints(np.zeros((1, 17, 2)), np.zeros((1, 17)), np.ones(1))


def test_longest_gap_counts_frames_in_a_row():
    homography = Homography(np.eye(3), 0.2, 10, 10)
    frames = [
        FrameCalibration(homography, OK, 10),
        FrameCalibration(None, SEM_CAMPO, 0),
        FrameCalibration(None, SEM_CAMPO, 0),
        FrameCalibration(homography, OK, 10),
        FrameCalibration(None, SEM_CAMPO, 0),
    ]

    assert longest_gap(frames) == 2
    assert longest_gap([]) == 0
