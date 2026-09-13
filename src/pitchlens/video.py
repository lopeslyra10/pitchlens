"""Leitura e escrita de vídeo.

A leitura usa o OpenCV, com frames em BGR. A escrita usa o ffmpeg que acompanha o pacote
``imageio-ffmpeg`` e gera MP4 em H.264 com ``yuv420p``, formato que abre em qualquer
navegador, diferente do ``mp4v`` que o OpenCV grava por padrão. Isso importa para o site
(Fase 5) e para os vídeos e GIFs da documentação.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType

import numpy as np

DEFAULT_FPS = 25.0


@dataclass(frozen=True)
class VideoInfo:
    """Metadados básicos de um vídeo."""

    width: int
    height: int
    fps: float
    frame_count: int

    @property
    def size(self) -> tuple[int, int]:
        return (self.width, self.height)

    @property
    def duration(self) -> float:
        """Duração em segundos."""
        return self.frame_count / self.fps


def _open(path: str | Path):
    import cv2

    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise FileNotFoundError(f"não foi possível abrir o vídeo: {path}")
    return capture


def probe(path: str | Path) -> VideoInfo:
    """Lê largura, altura, fps e número de frames sem decodificar o vídeo inteiro."""
    import cv2

    capture = _open(path)
    try:
        return VideoInfo(
            width=int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
            height=int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            fps=capture.get(cv2.CAP_PROP_FPS) or DEFAULT_FPS,
            frame_count=int(capture.get(cv2.CAP_PROP_FRAME_COUNT)),
        )
    finally:
        capture.release()


def iter_frames(
    path: str | Path, *, max_seconds: float | None = None, stride: int = 1
) -> Iterator[np.ndarray]:
    """Percorre os frames do vídeo em BGR.

    ``max_seconds`` limita o trecho lido a partir do início e ``stride`` pula frames
    (``stride=2`` lê um a cada dois), o que ajuda em testes rápidos com vídeos longos.
    """
    import cv2

    if stride < 1:
        raise ValueError("stride deve ser maior ou igual a 1")
    capture = _open(path)
    try:
        fps = capture.get(cv2.CAP_PROP_FPS) or DEFAULT_FPS
        limit = round(max_seconds * fps) if max_seconds is not None else None
        index = 0
        while limit is None or index < limit:
            ok, frame = capture.read()
            if not ok:
                break
            if index % stride == 0:
                yield frame
            index += 1
    finally:
        capture.release()


class VideoWriter:
    """Grava frames BGR em MP4 H.264, compatível com navegadores."""

    def __init__(
        self, path: str | Path, *, fps: float, size: tuple[int, int], quality: int = 7
    ) -> None:
        import imageio_ffmpeg

        width, height = size
        if width % 2 or height % 2:
            raise ValueError("largura e altura precisam ser pares para H.264 com yuv420p")
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.size = size
        self.frames_written = 0
        self._writer = imageio_ffmpeg.write_frames(
            str(self.path),
            size,
            fps=fps,
            codec="libx264",
            pix_fmt_in="rgb24",
            pix_fmt_out="yuv420p",
            quality=quality,
            macro_block_size=2,
        )
        self._writer.send(None)

    def write(self, frame: np.ndarray) -> None:
        """Adiciona um frame BGR com o mesmo tamanho informado na criação."""
        height, width = frame.shape[:2]
        if (width, height) != self.size:
            raise ValueError(f"frame {width}x{height} não bate com o tamanho do vídeo {self.size}")
        self._writer.send(np.ascontiguousarray(frame[:, :, ::-1]).tobytes())
        self.frames_written += 1

    def close(self) -> None:
        self._writer.close()

    def __enter__(self) -> VideoWriter:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
