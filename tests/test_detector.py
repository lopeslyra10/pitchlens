import json

from pitchlens.detection.detector import training_resolution


def test_resolution_is_read_from_the_training_config(tmp_path):
    (tmp_path / "training_config.json").write_text(json.dumps({"resolution": 1024}), "utf-8")

    assert training_resolution(tmp_path / "checkpoint_best_total.pth") == 1024


def test_nested_model_config_is_also_supported(tmp_path):
    config = {"model_config": {"resolution": 704}}
    (tmp_path / "training_config.json").write_text(json.dumps(config), "utf-8")

    assert training_resolution(tmp_path / "best.pth") == 704


def test_missing_training_config_keeps_the_model_default(tmp_path):
    assert training_resolution(tmp_path / "best.pth") is None
