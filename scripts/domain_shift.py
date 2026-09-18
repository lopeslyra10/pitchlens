"""Mede como o detector se comporta fora do ângulo de transmissão (Fase 1).

Roda o mesmo detector, com o mesmo limiar, nas imagens de teste do dataset (referência) e em
cada vídeo de licença livre, gera os vídeos anotados e compara os indicadores de
``pitchlens.detection.stats``.

Uso:
    python scripts/domain_shift.py --weights runs/rfdetr-medium/checkpoint_best_total.pth
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from pitchlens.console import use_utf8_output
from pitchlens.detection.annotate import DetectionAnnotator, class_names_of
from pitchlens.detection.classes import label_for
from pitchlens.detection.stats import DetectionStats

CLASSES = ["player", "goalkeeper", "referee", "ball"]
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compara o detector entre domínios.")
    parser.add_argument("--weights", type=Path, required=True, help="checkpoint do RF-DETR")
    parser.add_argument("--threshold", type=float, default=0.35)
    parser.add_argument("--dataset", type=Path, default=Path("data/datasets/football-players"))
    parser.add_argument("--videos", type=Path, nargs="+", default=None)
    parser.add_argument("--outputs", type=Path, default=Path("outputs"))
    parser.add_argument("--out", type=Path, default=Path("reports/fase-1"))
    return parser.parse_args()


def record(stats: DetectionStats, detections) -> None:
    confidences = detections.confidence if detections.confidence is not None else []
    stats.update(class_names_of(detections), confidences)


def run_images(detector, folder: Path) -> dict:
    import cv2

    stats = DetectionStats()
    for path in sorted(p for p in folder.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES):
        record(stats, detector.predict(cv2.imread(str(path))))
    return stats.summary()


def run_video(detector, annotator, video: Path, output: Path) -> dict:
    from pitchlens.video import VideoWriter, iter_frames, probe

    info = probe(video)
    size = (info.width - info.width % 2, info.height - info.height % 2)
    stats = DetectionStats()
    started = time.perf_counter()
    with VideoWriter(output, fps=info.fps, size=size) as writer:
        for frame in iter_frames(video):
            detections = detector.predict(frame)
            record(stats, detections)
            writer.write(annotator.annotate(frame, detections)[: size[1], : size[0]])
    summary = stats.summary()
    summary["fps_processamento"] = round(stats.frames / (time.perf_counter() - started), 1)
    return summary


def to_markdown(results: dict[str, dict]) -> str:
    header = ["Fonte", "Frames"]
    for name in CLASSES:
        header += [f"{label_for(name)}/frame", f"conf. {label_for(name)}"]
    header.append("frames com bola")
    lines = ["| " + " | ".join(header) + " |", "|" + " --- |" * len(header)]
    for source, summary in results.items():
        classes = summary["classes"]
        row = [source, str(summary["frames"])]
        for name in CLASSES:
            data = classes.get(name, {"por_frame": 0, "confianca_media": 0})
            row += [f"{data['por_frame']:.1f}", f"{data['confianca_media']:.2f}"]
        row.append(f"{classes.get('ball', {}).get('presenca', 0):.0%}")
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines) + "\n"


def main() -> None:
    use_utf8_output()
    args = parse_args()

    from pitchlens.detection.detector import RFDETRDetector

    detector = RFDETRDetector(args.weights, threshold=args.threshold)
    annotator = DetectionAnnotator()
    videos = args.videos or sorted(Path("data/raw").glob("*.*"))

    results = {"teste (transmissão)": run_images(detector, args.dataset / "test" / "images")}
    for video in videos:
        output = args.outputs / f"{video.stem}-deteccao.mp4"
        results[video.stem] = run_video(detector, annotator, video, output)
        print(f"{video.name}: {results[video.stem]['frames']} frames -> {output}")

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "mudanca-de-dominio.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    table = to_markdown(results)
    (args.out / "mudanca-de-dominio.md").write_text(table, encoding="utf-8")
    print(table)


if __name__ == "__main__":
    main()
