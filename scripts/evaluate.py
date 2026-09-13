"""Avaliação comparável entre detectores (Fase 1).

Todos os modelos passam pelo mesmo código: mesmo split de teste, mesmo limiar de confiança e
o mesmo cálculo de mAP (supervision, compatível com o COCO). As métricas que cada framework
imprime ao fim do treino usam implementações diferentes e não servem para comparar modelos.

Uso:
    python scripts/evaluate.py \
        --rfdetr runs/rfdetr-medium/checkpoint_best_total.pth \
        --yolo runs/yolo26m/weights/best.pt
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

import numpy as np

from pitchlens.console import use_utf8_output

EVAL_THRESHOLD = 0.05  # limiar baixo: o mAP precisa da curva precisão-revocação completa
WARMUP_IMAGES = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compara detectores no split de teste.")
    parser.add_argument("--dataset", type=Path, default=Path("data/datasets/football-players"))
    parser.add_argument("--split", default="test")
    parser.add_argument("--rfdetr", type=Path, help="checkpoint do RF-DETR")
    parser.add_argument("--yolo", type=Path, help="pesos do YOLO (scripts/benchmark)")
    parser.add_argument("--out", type=Path, default=Path("reports/fase-1"))
    return parser.parse_args()


def align_classes(predictions, class_names: list[str]):
    """Reindexa as detecções pelos nomes das classes do dataset.

    Cada framework numera as classes do seu jeito; comparar pelo nome evita que "bola" de um
    modelo seja contada como "goleiro" de outro. Classes fora do dataset são descartadas.
    """
    names = predictions.data.get("class_name")
    if names is None:
        return predictions
    index = {name: i for i, name in enumerate(class_names)}
    keep = np.array([str(name) in index for name in names], dtype=bool)
    predictions = predictions[keep]
    predictions.class_id = np.array(
        [index[str(name)] for name in predictions.data["class_name"]], dtype=int
    )
    return predictions


def evaluate(name: str, detector, dataset) -> dict:
    from supervision.metrics import MeanAveragePrecision

    metric = MeanAveragePrecision()
    latencies = []
    for position, (_, image, target) in enumerate(dataset):
        started = time.perf_counter()
        predictions = detector.predict(image)
        if position >= WARMUP_IMAGES:
            latencies.append(time.perf_counter() - started)
        metric.update(align_classes(predictions, dataset.classes), target)

    result = metric.compute()
    per_class = {
        dataset.classes[int(class_id)]: {
            "ap50": round(float(result.ap_per_class[row, 0]), 4),
            "ap50_95": round(float(result.ap_per_class[row].mean()), 4),
        }
        for row, class_id in enumerate(result.matched_classes)
    }
    latency = statistics.median(latencies)
    return {
        "modelo": name,
        "map50": round(float(result.map50), 4),
        "map50_95": round(float(result.map50_95), 4),
        "por_classe": per_class,
        "latencia_ms": round(latency * 1000, 1),
        "fps": round(1 / latency, 1),
        "imagens": len(dataset),
    }


def to_markdown(results: list[dict], class_names: list[str]) -> str:
    header = ["Modelo", "mAP@50", "mAP@50:95", *[f"AP50 {c}" for c in class_names], "ms/img"]
    lines = ["| " + " | ".join(header) + " |", "|" + " --- |" * len(header)]
    for r in results:
        per_class = [f"{r['por_classe'].get(c, {}).get('ap50', 0):.3f}" for c in class_names]
        row = [r["modelo"], f"{r['map50']:.3f}", f"{r['map50_95']:.3f}", *per_class]
        lines.append("| " + " | ".join([*row, f"{r['latencia_ms']:.1f}"]) + " |")
    return "\n".join(lines) + "\n"


def main() -> None:
    use_utf8_output()
    args = parse_args()
    if not args.rfdetr and not args.yolo:
        raise SystemExit("informe ao menos um modelo: --rfdetr e/ou --yolo")

    import supervision as sv

    root = args.dataset
    dataset = sv.DetectionDataset.from_yolo(
        images_directory_path=str(root / args.split / "images"),
        annotations_directory_path=str(root / args.split / "labels"),
        data_yaml_path=str(root / "data.yaml"),
    )

    detectors = []
    if args.rfdetr:
        from pitchlens.detection.detector import RFDETRDetector

        detector = RFDETRDetector(args.rfdetr, threshold=EVAL_THRESHOLD)
        detectors.append((detector.name, detector))
    if args.yolo:
        from benchmark.yolo import YOLODetector

        detectors.append((f"YOLO ({args.yolo.parent.parent.name})", YOLODetector(args.yolo)))

    results = [evaluate(name, detector, dataset) for name, detector in detectors]
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "metricas.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    table = to_markdown(results, dataset.classes)
    (args.out / "comparacao.md").write_text(table, encoding="utf-8")
    print(table)


if __name__ == "__main__":
    main()
