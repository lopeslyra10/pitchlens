from download_data import dataset_stats, normalized_yaml

CLASSES = ["ball", "goalkeeper", "player", "referee"]


def test_normalized_yaml_points_both_frameworks_to_the_dataset_folder(tmp_path):
    exported = {"train": "../train/images", "val": "../valid/images", "nc": 4, "names": CLASSES}

    data = normalized_yaml(exported, tmp_path)

    assert data["path"] == str(tmp_path.resolve())
    assert (data["train"], data["val"], data["test"]) == (
        "train/images",
        "valid/images",
        "test/images",
    )
    assert data["names"] == CLASSES


def test_dataset_stats_counts_images_and_instances(tmp_path):
    for split, count in (("train", 2), ("valid", 1)):
        (tmp_path / split / "images").mkdir(parents=True)
        (tmp_path / split / "labels").mkdir(parents=True)
        for index in range(count):
            (tmp_path / split / "images" / f"{index}.jpg").write_bytes(b"")
            (tmp_path / split / "labels" / f"{index}.txt").write_text(
                "2 0.5 0.5 0.1 0.2\n0 0.3 0.3 0.01 0.01\n"
            )

    stats = dataset_stats(tmp_path, CLASSES)

    assert stats["imagens"] == {"train": 2, "valid": 1, "test": 0}
    assert stats["instancias"] == {"ball": 3, "goalkeeper": 0, "player": 3, "referee": 0}
