import numpy as np
import pytest

pytest.importorskip("cv2")
pytest.importorskip("imageio_ffmpeg")

from pitchlens.video import VideoWriter, iter_frames, probe

RED_BGR = (0, 0, 255)


def _write_clip(path, frames: int, fps: float = 10, size=(64, 48), color=RED_BGR) -> None:
    width, height = size
    with VideoWriter(path, fps=fps, size=size) as writer:
        for _ in range(frames):
            writer.write(np.full((height, width, 3), color, dtype=np.uint8))


def test_written_video_can_be_read_back(tmp_path):
    path = tmp_path / "clip.mp4"
    _write_clip(path, frames=12)

    info = probe(path)
    frames = list(iter_frames(path))

    assert info.size == (64, 48)
    assert info.frame_count == 12
    assert info.duration == pytest.approx(1.2, abs=0.1)
    assert len(frames) == 12


def test_writer_keeps_color_channels_in_order(tmp_path):
    path = tmp_path / "red.mp4"
    _write_clip(path, frames=3)

    first = next(iter_frames(path))

    assert first[..., 2].mean() > 200
    assert first[..., 0].mean() < 60


def test_iter_frames_respects_time_limit_and_stride(tmp_path):
    path = tmp_path / "long.mp4"
    _write_clip(path, frames=20)

    assert len(list(iter_frames(path, max_seconds=1.0))) == 10
    assert len(list(iter_frames(path, max_seconds=1.0, stride=3))) == 4


def test_writer_rejects_odd_dimensions(tmp_path):
    with pytest.raises(ValueError, match="pares"):
        VideoWriter(tmp_path / "odd.mp4", fps=10, size=(63, 48))


def test_writer_rejects_frames_with_another_size(tmp_path):
    with (
        VideoWriter(tmp_path / "size.mp4", fps=10, size=(64, 48)) as writer,
        pytest.raises(ValueError, match="não bate"),
    ):
        writer.write(np.zeros((32, 32, 3), dtype=np.uint8))
