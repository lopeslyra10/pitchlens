import numpy as np
import pytest

from pitchlens.pitch import FIFA_PITCH, PitchSpec


def test_default_pitch_follows_fifa_recommendation():
    assert (FIFA_PITCH.length, FIFA_PITCH.width) == (105.0, 68.0)
    assert FIFA_PITCH.center == (52.5, 34.0)


def test_keypoints_are_unique_and_inside_the_pitch():
    keypoints = FIFA_PITCH.keypoints()

    assert len(keypoints) == 33
    assert len(set(keypoints.values())) == len(keypoints)
    assert all(FIFA_PITCH.contains(x, y) for x, y in keypoints.values())


def test_left_and_right_keypoints_mirror_each_other():
    keypoints = FIFA_PITCH.keypoints()
    left = {n.removeprefix("left_"): p for n, p in keypoints.items() if n.startswith("left_")}
    right = {n.removeprefix("right_"): p for n, p in keypoints.items() if n.startswith("right_")}

    assert left.keys() == right.keys()
    for name, point in left.items():
        assert FIFA_PITCH.reflect_across_halfway(point) == pytest.approx(right[name])


def test_penalty_area_uses_official_measures():
    keypoints = FIFA_PITCH.keypoints()
    top = keypoints["left_penalty_area_top"]
    bottom = keypoints["left_penalty_area_bottom"]

    assert top[0] == pytest.approx(16.5)
    assert bottom[1] - top[1] == pytest.approx(40.32)
    assert keypoints["left_penalty_spot"] == pytest.approx((11.0, 34.0))


def test_rotate_half_turn_normalizes_attacking_direction():
    point = (20.0, 10.0)
    rotated = FIFA_PITCH.rotate_half_turn(point)

    assert rotated == pytest.approx((85.0, 58.0))
    assert FIFA_PITCH.rotate_half_turn(rotated) == pytest.approx(point)
    assert FIFA_PITCH.rotate_half_turn(FIFA_PITCH.center) == pytest.approx(FIFA_PITCH.center)


def test_keypoints_array_keeps_requested_order():
    array = FIFA_PITCH.keypoints_array(["center_spot", "corner_top_left"])

    assert array.shape == (2, 2)
    assert array.dtype == np.float32
    np.testing.assert_allclose(array, [[52.5, 34.0], [0.0, 0.0]])


def test_keypoints_array_rejects_unknown_names():
    with pytest.raises(KeyError, match="desconhecidos"):
        FIFA_PITCH.keypoints_array(["corner_top_left", "marca_inexistente"])


@pytest.mark.parametrize(
    "overrides",
    [
        {"length": 0.0},
        {"width": 110.0},
        {"goal_area_width": 45.0},
        {"penalty_area_width": 70.0},
        {"goal_area_depth": 20.0},
        {"penalty_area_depth": 45.0},
    ],
)
def test_inconsistent_dimensions_are_rejected(overrides):
    with pytest.raises(ValueError):
        PitchSpec(**overrides)


def test_keypoint_order_matches_the_dataset_layout():
    from pitchlens.pitch import KEYPOINT_ORDER

    keypoints = FIFA_PITCH.keypoints()

    assert len(KEYPOINT_ORDER) == 32
    assert len(set(KEYPOINT_ORDER)) == 32
    assert all(name in keypoints for name in KEYPOINT_ORDER)
    # Os pontos seguem a numeração 1 a 32 do dataset: 1 é o canto superior esquerdo,
    # 14 é o meio-campo na linha de cima e 32 é a borda direita do círculo central.
    assert keypoints[KEYPOINT_ORDER[0]] == (0.0, 0.0)
    assert keypoints[KEYPOINT_ORDER[13]] == (52.5, 0.0)
    assert keypoints[KEYPOINT_ORDER[31]] == pytest.approx((52.5 + 9.15, 34.0))


def test_keypoints_array_follows_the_dataset_order():
    from pitchlens.pitch import KEYPOINT_ORDER

    array = FIFA_PITCH.keypoints_array(KEYPOINT_ORDER)

    assert array.shape == (32, 2)
    np.testing.assert_allclose(array[14], [52.5, 34.0 - 9.15], atol=1e-6)


def test_flip_pairs_mirror_left_and_right_points():
    from pitchlens.pitch import KEYPOINT_ORDER, keypoint_flip_pairs

    pairs = keypoint_flip_pairs()
    keypoints = FIFA_PITCH.keypoints()

    # 14 pares (13 de cada lado mais o círculo central); 4 pontos do meio do campo não têm par.
    assert len(pairs) == 14
    assert len(pairs) * 2 + 4 == len(KEYPOINT_ORDER)
    assert all(first < second for first, second in pairs)
    for first, second in pairs:
        left, right = keypoints[KEYPOINT_ORDER[first]], keypoints[KEYPOINT_ORDER[second]]
        assert FIFA_PITCH.reflect_across_halfway(left) == pytest.approx(right)
