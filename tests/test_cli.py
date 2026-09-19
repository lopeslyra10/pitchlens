import pytest

from pitchlens.cli import build_parser, main


def test_detect_command_defaults():
    args = build_parser().parse_args(["detect", "clip.mp4", "--weights", "best.pth"])

    assert args.threshold == 0.35
    assert args.max_seconds is None
    assert args.out is None


def test_version_flag_prints_package_version(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])

    assert exit_info.value.code == 0
    assert "pitchlens" in capsys.readouterr().out


def test_detect_requires_model_weights():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["detect", "clip.mp4"])


def test_track_command_defaults():
    args = build_parser().parse_args(["track", "clip.mp4", "--weights", "best.pth"])

    assert args.threshold == 0.35
    assert args.out is None
    assert args.handler.__name__ == "_track"
