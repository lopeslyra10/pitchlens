from pitchlens.detection import OBJECT_CLASSES, color_for, label_for


def test_dataset_classes_have_portuguese_labels():
    assert set(OBJECT_CLASSES) == {"ball", "goalkeeper", "player", "referee"}
    assert label_for("referee") == "árbitro"
    assert label_for("ball") == "bola"


def test_unknown_classes_fall_back_gracefully():
    assert label_for("linesman") == "linesman"
    assert color_for("linesman").startswith("#")
