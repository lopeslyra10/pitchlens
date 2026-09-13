import numpy as np
import pytest

from evaluate import to_markdown

CLASSES = ["ball", "goalkeeper", "player", "referee"]


def test_markdown_table_has_one_row_per_model():
    results = [
        {
            "modelo": "RF-DETR medium",
            "map50": 0.9,
            "map50_95": 0.6,
            "por_classe": {"ball": {"ap50": 0.5}},
            "latencia_ms": 20.0,
        }
    ]

    table = to_markdown(results, ["ball", "player"])

    assert table.splitlines()[0].startswith("| Modelo | mAP@50 | mAP@50:95 | AP50 ball")
    assert "| RF-DETR medium | 0.900 | 0.600 | 0.500 | 0.000 | 20.0 |" in table


def test_align_classes_reindexes_predictions_by_class_name():
    sv = pytest.importorskip("supervision")
    from evaluate import align_classes

    predictions = sv.Detections(
        xyxy=np.zeros((3, 4)),
        class_id=np.array([7, 8, 9]),
        confidence=np.ones(3),
        data={"class_name": np.array(["player", "ball", "bandeirinha"])},
    )

    aligned = align_classes(predictions, CLASSES)

    assert aligned.class_id.tolist() == [2, 0]
