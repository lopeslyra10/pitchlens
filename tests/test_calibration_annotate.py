import numpy as np
import pytest

pytest.importorskip("cv2")

from pitchlens.calibration.annotate import CalibrationAnnotator
from pitchlens.calibration.homography import (
    OK,
    SEM_CAMPO,
    FrameCalibration,
    Homography,
    solve_homography,
)
from pitchlens.pitch import KEYPOINT_ORDER

PITCH_QUAD = np.array([[0.0, 0.0], [105.0, 0.0], [105.0, 68.0], [0.0, 68.0]])
IMAGE_QUAD = np.array([[320.0, 180.0], [980.0, 190.0], [1240.0, 650.0], [60.0, 620.0]])


@pytest.fixture
def frame() -> np.ndarray:
    return np.zeros((720, 1280, 3), dtype=np.uint8)


@pytest.fixture
def calibration() -> FrameCalibration:
    matrix = solve_homography(IMAGE_QUAD, PITCH_QUAD)
    return FrameCalibration(Homography(matrix, 0.42, 20, 18), OK, 20)


def test_annotating_draws_the_pitch_without_touching_the_original(frame, calibration):
    scene = CalibrationAnnotator().annotate(frame, calibration)

    assert scene.shape == frame.shape
    assert not frame.any()
    assert scene.any()
    # As linhas do campo chegam perto dos cantos projetados.
    for x, y in IMAGE_QUAD.astype(int):
        assert scene[max(y - 3, 0) : y + 3, max(x - 3, 0) : x + 3].any()


def test_a_frame_without_a_field_still_gets_the_badge(frame):
    scene = CalibrationAnnotator().annotate(frame, FrameCalibration(None, SEM_CAMPO, 2))

    assert scene[:40, :300].any()
    assert not scene[200:, :].any()


def test_points_are_drawn_apart_from_the_ones_that_were_dropped(frame, calibration):
    keypoints = np.zeros((len(KEYPOINT_ORDER), 2))
    keypoints[0], keypoints[1] = (400.0, 400.0), (500.0, 400.0)
    confidences = np.zeros(len(KEYPOINT_ORDER))
    confidences[0], confidences[1] = 0.9, 0.2

    scene = CalibrationAnnotator().annotate(frame, calibration, keypoints, confidences)

    used = scene[395:405, 395:405]
    dropped = scene[395:405, 495:505]
    assert used.any() and dropped.any()
    # O ponto aceito é um círculo cheio, e o descartado só o contorno.
    assert used.astype(bool).sum() > dropped.astype(bool).sum()
