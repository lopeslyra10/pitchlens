import numpy as np
import pytest

sv = pytest.importorskip("supervision")

from pitchlens.calibration.homography import (  # noqa: E402
    OK,
    SEM_CAMPO,
    FrameCalibration,
    Homography,
    solve_homography,
)
from pitchlens.pitch import FIFA_PITCH  # noqa: E402
from pitchlens.tracking.pipeline import only_on_pitch  # noqa: E402

PITCH_QUAD = np.array([[0.0, 0.0], [105.0, 0.0], [105.0, 68.0], [0.0, 68.0]])
IMAGE_QUAD = np.array([[320.0, 180.0], [980.0, 190.0], [1240.0, 650.0], [60.0, 620.0]])


@pytest.fixture
def calibration() -> FrameCalibration:
    matrix = solve_homography(IMAGE_QUAD, PITCH_QUAD)
    return FrameCalibration(Homography(matrix, 0.3, 20, 19), OK, 20)


def _people(calibration: FrameCalibration) -> sv.Detections:
    # Um jogador no meio do campo e alguém no banco, bem acima da linha de fundo distante.
    x, y = calibration.homography.to_image([FIFA_PITCH.center])[0]
    return sv.Detections(
        xyxy=np.array([[x - 15, y - 160, x + 15, y], [400, 20, 430, 120]], dtype=float),
        class_id=np.array([2, 2]),
        confidence=np.array([0.9, 0.8]),
        data={"class_name": np.array(["player", "player"])},
    )


def test_people_outside_the_lines_are_dropped(calibration):
    kept = only_on_pitch(_people(calibration), calibration)

    assert len(kept) == 1
    assert kept.confidence[0] == pytest.approx(0.9)


def test_without_calibration_everyone_is_kept(calibration):
    people = _people(calibration)

    kept = only_on_pitch(people, FrameCalibration(None, SEM_CAMPO, 0))

    assert len(kept) == len(people)


def test_an_empty_frame_stays_empty(calibration):
    empty = sv.Detections.empty()

    assert len(only_on_pitch(empty, calibration)) == 0
