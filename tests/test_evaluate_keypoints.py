import json

import numpy as np
import pytest

from evaluate_keypoints import annotations, calibrate, summarize, usable
from pitchlens.calibration.homography import Homography, solve_homography, transform_points
from pitchlens.pitch import FIFA_PITCH, KEYPOINT_ORDER

PITCH_QUAD = np.array([[0.0, 0.0], [105.0, 0.0], [105.0, 68.0], [0.0, 68.0]])
IMAGE_QUAD = np.array([[320.0, 180.0], [980.0, 190.0], [1240.0, 650.0], [60.0, 620.0]])


@pytest.fixture
def seen_points() -> np.ndarray:
    camera = solve_homography(PITCH_QUAD, IMAGE_QUAD)
    return transform_points(camera, FIFA_PITCH.keypoints_array(KEYPOINT_ORDER))


def test_annotations_pair_each_image_with_its_points(tmp_path):
    split = tmp_path / "test"
    split.mkdir()
    coco = {
        "images": [{"id": 7, "file_name": "jogo.jpg"}],
        "annotations": [{"image_id": 7, "keypoints": [1, 2, 2] * len(KEYPOINT_ORDER)}],
    }
    (split / "_annotations.coco.json").write_text(json.dumps(coco), encoding="utf-8")

    found = annotations(tmp_path, "test")

    assert len(found) == 1
    image_file, points = found[0]
    assert image_file.name == "jogo.jpg"
    assert points.shape == (len(KEYPOINT_ORDER), 3)


def test_usable_demands_support_and_a_small_error():
    assert usable(Homography(np.eye(3), 0.4, 20, 18))
    assert not usable(None)
    assert not usable(Homography(np.eye(3), 9.0, 20, 18))  # erro grande demais
    assert not usable(Homography(np.eye(3), 0.4, 20, 5))  # pouca gente concorda
    assert not usable(Homography(np.eye(3), 0.4, 8, 4))  # menos pontos que o mínimo


def test_calibrate_measures_a_clean_prediction(seen_points):
    result = calibrate(seen_points, np.ones(len(KEYPOINT_ORDER)), 0.5)

    assert result["pontos"] == len(KEYPOINT_ORDER)
    assert result["erro_m"] < 0.01
    assert result["erro_maximo_m"] < 0.01


def test_calibrate_gives_up_when_too_few_points_are_confident(seen_points):
    scores = np.zeros(len(KEYPOINT_ORDER))
    scores[:4] = 1.0

    assert calibrate(seen_points, scores, 0.5) is None


def test_summary_counts_the_images_that_could_not_be_calibrated():
    results = [{"erro_m": 0.2, "pontos": 20}, {"erro_m": 0.6, "pontos": 10}, None, None]

    summary = summarize("modelo", results, 4)

    assert summary == {
        "fonte": "modelo",
        "imagens": 4,
        "calibradas": 2,
        "cobertura_pct": 0.5,
        "erro_mediano_m": 0.4,
        "erro_p95_m": 0.58,
        "erro_maximo_m": 0.6,
        "pontos_por_imagem": 15.0,
    }


def test_summary_of_a_model_that_never_calibrates():
    assert summarize("modelo", [None, None], 2) == {
        "fonte": "modelo",
        "imagens": 2,
        "calibradas": 0,
    }
