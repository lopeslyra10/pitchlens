"""Linha de comando do PitchLens.

Exemplos (``PESOS`` = runs/rfdetr-medium/checkpoint_best_total.pth):
    pitchlens detect data/raw/u17-nz-can-25.webm --weights PESOS
    pitchlens track data/raw/u17-nz-can-25.webm --weights PESOS
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Sequence
from pathlib import Path

from pitchlens import __version__
from pitchlens.console import use_utf8_output


def _detect(args: argparse.Namespace) -> int:
    from pitchlens.detection.annotate import DetectionAnnotator
    from pitchlens.detection.detector import RFDETRDetector
    from pitchlens.video import VideoWriter, iter_frames, probe

    info = probe(args.video)
    output = args.out or Path("outputs") / f"{args.video.stem}-deteccao.mp4"
    detector = RFDETRDetector(args.weights, threshold=args.threshold)
    annotator = DetectionAnnotator()

    started = time.perf_counter()
    with VideoWriter(output, fps=info.fps, size=info.size) as writer:
        for frame in iter_frames(args.video, max_seconds=args.max_seconds):
            writer.write(annotator.annotate(frame, detector.predict(frame)))
    elapsed = time.perf_counter() - started

    fps = writer.frames_written / elapsed if elapsed else 0.0
    print(f"{writer.frames_written} frames em {elapsed:.1f} s ({fps:.1f} fps) -> {output}")
    return 0


def _track(args: argparse.Namespace) -> int:
    from pitchlens.detection.detector import RFDETRDetector
    from pitchlens.tracking.pipeline import track_video

    output = args.out or Path("outputs") / f"{args.video.stem}-rastreamento.mp4"
    detector = RFDETRDetector(args.weights, threshold=args.threshold)
    summary = track_video(detector, args.video, output)
    stats_file = output.with_suffix(".json")
    stats_file.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{summary['frames']} frames, {summary['ids_unicos']} identificadores -> {output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pitchlens",
        description="Visão computacional para análise tática de futebol.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    detect = commands.add_parser(
        "detect", help="detecta jogadores, goleiros, árbitros e bola em um vídeo"
    )
    detect.add_argument("video", type=Path, help="vídeo de entrada")
    detect.add_argument("--weights", type=Path, required=True, help="checkpoint do RF-DETR")
    detect.add_argument("--threshold", type=float, default=0.35, help="confiança mínima")
    detect.add_argument("--max-seconds", type=float, default=None, help="processa só o início")
    detect.add_argument("--out", type=Path, default=None, help="vídeo anotado de saída")
    detect.set_defaults(handler=_detect)

    track = commands.add_parser(
        "track", help="rastreia os jogadores, separa os times e gera o vídeo com os IDs"
    )
    track.add_argument("video", type=Path, help="vídeo de entrada")
    track.add_argument("--weights", type=Path, required=True, help="checkpoint do RF-DETR")
    track.add_argument("--threshold", type=float, default=0.35, help="confiança mínima")
    track.add_argument("--out", type=Path, default=None, help="vídeo anotado de saída")
    track.set_defaults(handler=_track)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    use_utf8_output()
    args = build_parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
