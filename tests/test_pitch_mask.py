import numpy as np
import pytest

from pitchlens.calibration.homography import Homography, solve_homography
from pitchlens.calibration.mask import feet, inside_pitch, on_pitch, pitch_outline
from pitchlens.pitch import FIFA_PITCH

PITCH_QUAD = np.array([[0.0, 0.0], [105.0, 0.0], [105.0, 68.0], [0.0, 68.0]])
IMAGE_QUAD = np.array([[320.0, 180.0], [980.0, 190.0], [1240.0, 650.0], [60.0, 620.0]])


@pytest.fixture
def homography() -> Homography:
    """Homografia imagem → campo de uma câmera lateral fixa."""
    matrix = solve_homography(IMAGE_QUAD, PITCH_QUAD)
    assert matrix is not None
    return Homography(matrix, 0.2, 20, 20)


def test_feet_is_the_middle_of_the_box_base():
    result = feet([[100.0, 50.0, 140.0, 210.0], [0.0, 0.0, 10.0, 10.0]])

    np.testing.assert_allclose(result, [[120.0, 210.0], [5.0, 10.0]])


def test_inside_pitch_accepts_the_field_and_rejects_the_stands(homography):
    center, corner = homography.to_image([FIFA_PITCH.center, (0.0, 0.0)])
    stands = [IMAGE_QUAD[0, 0], IMAGE_QUAD[0, 1] - 120.0]  # acima da linha de fundo distante

    result = inside_pitch(homography, [center, corner, stands])

    assert result.tolist() == [True, True, False]


def test_inside_pitch_tolerates_a_step_over_the_line(homography):
    just_outside = homography.to_image([(-1.0, 34.0)])[0]
    far_outside = homography.to_image([(-8.0, 34.0)])[0]

    assert inside_pitch(homography, [just_outside]).tolist() == [True]
    assert inside_pitch(homography, [far_outside]).tolist() == [False]
    assert inside_pitch(homography, [just_outside], margin_m=0.0).tolist() == [False]


def test_inside_pitch_rejects_points_on_the_horizon():
    # A terceira linha anula o ponto (0, 0): ele não tem posição no campo.
    matrix = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 0.0]])

    assert inside_pitch(Homography(matrix, 0.0, 4, 4), [[0.0, 0.0]]).tolist() == [False]


def test_on_pitch_looks_at_the_feet_not_at_the_head(homography):
    # Jogador no círculo central: os pés no gramado, a cabeça projetada na arquibancada.
    x, y = homography.to_image([FIFA_PITCH.center])[0]
    player = [x - 15.0, y - 160.0, x + 15.0, y]
    in_the_stands = [x - 15.0, y - 400.0, x + 15.0, y - 240.0]

    assert on_pitch(homography, [player, in_the_stands]).tolist() == [True, False]


def test_on_pitch_handles_an_empty_frame(homography):
    assert on_pitch(homography, np.zeros((0, 4))).tolist() == []


def test_pitch_outline_follows_the_lines_on_the_image(homography):
    outline = pitch_outline(homography)

    assert len(outline) == 160
    # O contorno começa no canto do campo e passa pelos outros três cantos.
    for corner in IMAGE_QUAD:
        assert np.linalg.norm(outline - corner, axis=1).min() < 1e-6


def test_pitch_outline_drops_the_part_that_falls_behind_the_camera():
    # Câmera rasante: o horizonte passa no meio do campo (y = 34 m), e os pontos exatamente
    # sobre ele não têm posição na imagem.
    to_image = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, -1.0 / 34.0, 1.0]])
    outline = pitch_outline(Homography(np.linalg.inv(to_image), 0.5, 10, 10))

    assert len(outline) == 158
    assert np.isfinite(outline).all()


def test_pitch_outline_matches_the_projected_corners(homography):
    outline = pitch_outline(homography, samples=1)

    np.testing.assert_allclose(outline, IMAGE_QUAD, atol=1e-6)
