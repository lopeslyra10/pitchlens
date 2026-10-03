import numpy as np
import pytest

from pitchlens.calibration.homography import (
    OK,
    REPETIDA,
    SEM_CAMPO,
    FrameCalibration,
    Homography,
    PitchCalibrator,
    fit_homography,
    reprojection_errors_m,
    solve_homography,
    transform_points,
    visible_keypoints,
)
from pitchlens.calibration.stats import CalibrationStats
from pitchlens.pitch import FIFA_PITCH, KEYPOINT_ORDER

FRAME_SIZE = (1280, 720)
# Câmera lateral: o campo aparece como um trapézio, com a linha de fundo mais longe menor.
PITCH_QUAD = np.array([[0.0, 0.0], [105.0, 0.0], [105.0, 68.0], [0.0, 68.0]])
IMAGE_QUAD = np.array([[320.0, 180.0], [980.0, 190.0], [1240.0, 650.0], [60.0, 620.0]])


@pytest.fixture
def camera() -> np.ndarray:
    """Homografia campo → imagem de uma câmera lateral fixa."""
    matrix = solve_homography(PITCH_QUAD, IMAGE_QUAD)
    assert matrix is not None
    return matrix


@pytest.fixture
def keypoints(camera) -> np.ndarray:
    """Os 32 pontos do gramado como essa câmera os veria."""
    return transform_points(camera, FIFA_PITCH.keypoints_array(KEYPOINT_ORDER))


def test_transform_points_moves_and_scales():
    translation = np.array([[2.0, 0.0, 10.0], [0.0, 2.0, -5.0], [0.0, 0.0, 1.0]])

    result = transform_points(translation, [[0.0, 0.0], [1.0, 1.0]])

    np.testing.assert_allclose(result, [[10.0, -5.0], [12.0, -3.0]])


def test_transform_points_marks_the_horizon_as_undefined():
    # A terceira linha anula o ponto (1, 0): ele cai na linha do horizonte.
    matrix = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [-1.0, 0.0, 1.0]])

    result = transform_points(matrix, [[1.0, 0.0], [0.0, 0.0]])

    assert np.isnan(result[0]).all()
    np.testing.assert_allclose(result[1], [0.0, 0.0])


def test_solve_homography_recovers_the_camera(camera):
    corners = transform_points(camera, PITCH_QUAD)

    matrix = solve_homography(PITCH_QUAD, corners)

    np.testing.assert_allclose(matrix, camera, rtol=1e-6, atol=1e-9)


def test_solve_homography_rejects_degenerate_points():
    collinear = np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0], [3.0, 0.0]])

    assert solve_homography(collinear, IMAGE_QUAD) is None
    assert solve_homography(PITCH_QUAD[:3], IMAGE_QUAD[:3]) is None


def test_fit_homography_maps_the_image_back_to_metres(keypoints):
    pitch = FIFA_PITCH.keypoints_array(KEYPOINT_ORDER).astype(np.float64)

    homography = fit_homography(keypoints, pitch)

    assert homography is not None
    assert homography.error_m < 0.01
    assert homography.inliers == len(KEYPOINT_ORDER)
    np.testing.assert_allclose(homography.to_pitch(keypoints), pitch, atol=1e-6)
    np.testing.assert_allclose(homography.to_image(pitch), keypoints, atol=1e-6)


def test_fit_homography_ignores_points_predicted_in_the_wrong_place(keypoints):
    pitch = FIFA_PITCH.keypoints_array(KEYPOINT_ORDER).astype(np.float64)
    corrupted = keypoints.copy()
    corrupted[5] += [220.0, -140.0]
    corrupted[17] -= [300.0, 90.0]

    homography = fit_homography(corrupted, pitch)

    assert homography is not None
    assert homography.inliers == len(KEYPOINT_ORDER) - 2
    assert homography.error_m < 0.01
    errors = reprojection_errors_m(homography.matrix, corrupted, pitch)
    assert errors[[5, 17]].min() > 1.5


def test_fit_homography_is_deterministic(keypoints):
    pitch = FIFA_PITCH.keypoints_array(KEYPOINT_ORDER).astype(np.float64)
    noisy = keypoints + np.random.default_rng(7).normal(scale=2.0, size=keypoints.shape)

    first, second = fit_homography(noisy, pitch), fit_homography(noisy, pitch)

    assert first is not None and second is not None
    np.testing.assert_array_equal(first.matrix, second.matrix)


def test_fit_homography_needs_four_points(keypoints):
    pitch = FIFA_PITCH.keypoints_array(KEYPOINT_ORDER).astype(np.float64)

    assert fit_homography(keypoints[:3], pitch[:3]) is None
    with pytest.raises(ValueError, match="cada ponto"):
        fit_homography(keypoints[:5], pitch[:4])


def test_reprojection_errors_are_measured_in_metres():
    identity = np.eye(3)

    errors = reprojection_errors_m(identity, [[0.0, 0.0], [3.0, 4.0]], [[0.0, 0.0], [0.0, 0.0]])

    np.testing.assert_allclose(errors, [0.0, 5.0])


def test_visible_keypoints_keeps_only_trustworthy_points(keypoints):
    confidences = np.ones(len(KEYPOINT_ORDER))
    confidences[:4] = 0.1
    masked = keypoints.copy()
    masked[6] = [0.0, 0.0]  # ponto não anotado

    image, pitch = visible_keypoints(masked, confidences, min_confidence=0.5)

    assert len(image) == len(pitch) == len(KEYPOINT_ORDER) - 5
    np.testing.assert_allclose(pitch[0], FIFA_PITCH.keypoints()[KEYPOINT_ORDER[4]])


def test_visible_keypoints_requires_the_whole_set(keypoints):
    with pytest.raises(ValueError, match="esperados 32 pontos"):
        visible_keypoints(keypoints[:10])
    with pytest.raises(ValueError, match="cada ponto"):
        visible_keypoints(keypoints, np.ones(5))


def test_calibrator_rejects_impossible_settings():
    with pytest.raises(ValueError, match="tamanho do frame"):
        PitchCalibrator((0, 720))
    with pytest.raises(ValueError, match="suavização"):
        PitchCalibrator(FRAME_SIZE, smoothing=0.0)
    with pytest.raises(ValueError, match="pelo menos 4 pontos"):
        PitchCalibrator(FRAME_SIZE, min_points=3)


def test_calibrator_calibrates_a_frame_with_enough_points(keypoints):
    calibration = PitchCalibrator(FRAME_SIZE).update(keypoints)

    assert calibration.status == OK
    assert calibration.usable
    assert calibration.points == len(KEYPOINT_ORDER)
    assert calibration.homography.error_m < 0.01


def test_calibrator_repeats_the_last_homography_and_then_gives_up(keypoints):
    calibrator = PitchCalibrator(FRAME_SIZE, max_repeated=2)
    good = calibrator.update(keypoints)
    hidden = np.zeros_like(keypoints)

    repeated = [calibrator.update(hidden) for _ in range(3)]

    assert [frame.status for frame in repeated] == [REPETIDA, REPETIDA, SEM_CAMPO]
    assert repeated[0].homography is good.homography
    assert repeated[-1].homography is None
    assert not repeated[-1].usable
    # Depois de desistir, um frame bom recalibra do zero.
    assert calibrator.update(keypoints).status == OK


def test_calibrator_discards_frames_whose_error_is_too_large(keypoints):
    shaky = keypoints + np.random.default_rng(3).normal(scale=5.0, size=keypoints.shape)

    assert PitchCalibrator(FRAME_SIZE, max_error_m=0.5).update(shaky).status == SEM_CAMPO
    # O mesmo frame passa quando a exigência é a do projeto: erra meio metro, não cinco.
    tolerant = PitchCalibrator(FRAME_SIZE).update(shaky)
    assert tolerant.status == OK
    assert tolerant.homography.error_m < 1.0


def test_calibrator_rejects_a_fit_supported_by_few_points(keypoints):
    """Com pontos muito ruins o RANSAC acha uma matriz boa para poucos deles: não serve."""
    scrambled = keypoints + np.random.default_rng(3).normal(scale=20.0, size=keypoints.shape)

    calibration = PitchCalibrator(FRAME_SIZE).update(scrambled)

    assert calibration.status == SEM_CAMPO
    assert calibration.points == len(KEYPOINT_ORDER)


def test_calibrator_trusts_a_zoomed_frame_where_every_point_agrees(keypoints):
    """Num close sobram poucos pontos, mas se todos concordam a calibração vale."""
    few = keypoints.copy()
    confidences = np.zeros(len(KEYPOINT_ORDER))
    confidences[[0, 5, 13, 16, 7, 8]] = 1.0

    calibration = PitchCalibrator(FRAME_SIZE).update(few, confidences)

    assert calibration.status == OK
    assert calibration.points == 6


def test_smoothing_steadies_a_fixed_camera(keypoints):
    pitch_center = [FIFA_PITCH.center]
    rng = np.random.default_rng(11)
    noise = [rng.normal(scale=3.0, size=keypoints.shape) for _ in range(30)]

    def track(smoothing: float) -> float:
        calibrator = PitchCalibrator(FRAME_SIZE, smoothing=smoothing)
        centers = []
        for frame in noise:
            calibration = calibrator.update(keypoints + frame)
            assert calibration.status == OK
            centers.append(calibration.homography.to_image(pitch_center)[0])
        return float(np.std(np.array(centers), axis=0).mean())

    assert track(0.3) < track(1.0) * 0.6


def test_smoothing_forgets_the_scene_after_a_camera_cut(keypoints, camera):
    calibrator = PitchCalibrator(FRAME_SIZE, smoothing=0.3)
    calibrator.update(keypoints)
    # Outro ângulo: o campo passa a ocupar outra região da imagem.
    other = solve_homography(PITCH_QUAD, IMAGE_QUAD * [0.5, 0.9] + [120.0, 40.0])
    cut = transform_points(other, FIFA_PITCH.keypoints_array(KEYPOINT_ORDER))

    calibration = calibrator.update(cut)

    assert calibration.status == OK
    assert calibration.homography.error_m < 0.01
    np.testing.assert_allclose(
        calibration.homography.to_pitch(cut),
        FIFA_PITCH.keypoints_array(KEYPOINT_ORDER),
        atol=1e-5,
    )


def test_stats_report_coverage_and_error_in_metres():
    stats = CalibrationStats()
    homography = Homography(np.eye(3), 0.4, 20, 18)

    stats.update(_frame(homography, OK, 20))
    stats.update(_frame(Homography(np.eye(3), 0.8, 20, 18), OK, 20))
    stats.update(_frame(homography, REPETIDA, 3))
    stats.update(_frame(None, SEM_CAMPO, 0))

    summary = stats.summary()
    assert summary["frames"] == 4
    assert summary["frames_ajustados"] == 2
    assert summary["cobertura_pct"] == 0.75
    assert summary["erro_mediano_m"] == 0.6
    assert summary["erro_maximo_m"] == 0.8
    assert summary["pontos_por_frame"] == 10.8


def test_stats_are_empty_before_the_first_frame():
    assert CalibrationStats().summary() == {"frames": 0}


def _frame(homography, status, points):
    return FrameCalibration(homography, status, points)


def test_convex_projection_accepts_a_real_camera(keypoints):
    from pitchlens.calibration.homography import convex_projection

    homography = fit_homography(keypoints, FIFA_PITCH.keypoints_array(KEYPOINT_ORDER))

    assert convex_projection(homography)


def test_convex_projection_rejects_an_impossible_field():
    from pitchlens.calibration.homography import Homography, convex_projection

    # Troca duas colunas da matriz: o campo projetado vira um laço, e não um retângulo.
    twisted = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.004, -0.004, 1.0]])
    folded = np.array([[1.0, 0.5, 0.0], [1.0, -0.5, 0.0], [0.02, 0.0, 1.0]])

    assert convex_projection(Homography(np.linalg.inv(twisted), 0.2, 20, 18))
    assert not convex_projection(Homography(folded, 0.2, 20, 18))


def test_a_fit_that_draws_an_impossible_field_is_discarded(keypoints):
    """Poucos pontos amontoados passam pelo erro em metros, mas não pela geometria."""
    confidences = np.zeros(len(KEYPOINT_ORDER))
    confidences[[13, 14, 15, 16, 30, 31]] = 1.0  # só o miolo do campo
    crowded = keypoints.copy()
    crowded[[30, 31]] += [0.0, 60.0]  # dois deles previstos fora do lugar

    calibration = PitchCalibrator(FRAME_SIZE).update(crowded, confidences)

    assert calibration.status == SEM_CAMPO
