"""Treino do baseline YOLO no mesmo dataset e split usados pelo RF-DETR.

Uso:
    python scripts/benchmark/train_yolo.py --model yolo26m.pt --epochs 60

Os pesos vão para ``runs/<modelo>/weights/best.pt`` (fora do Git).
"""

from __future__ import annotations

import argparse
import json
import platform
import time
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Treina o baseline YOLO no dataset de futebol.")
    parser.add_argument("--dataset", type=Path, default=Path("data/datasets/football-players"))
    parser.add_argument("--model", default="yolo26m.pt", help="pesos pré-treinados no COCO")
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=-1, help="-1 escolhe pelo uso de memória")
    parser.add_argument("--patience", type=int, default=15)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=Path("runs"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    import torch
    from ultralytics import YOLO

    name = Path(args.model).stem
    options = {
        "data": str(args.dataset / "data.yaml"),
        "epochs": args.epochs,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "patience": args.patience,
        "seed": args.seed,
        "project": str(args.output.resolve()),
        "name": name,
        "exist_ok": True,
    }
    started = time.perf_counter()
    YOLO(args.model).train(**options)
    minutes = (time.perf_counter() - started) / 60

    record = {
        "modelo": name,
        "opcoes": options,
        "duracao_min": round(minutes, 1),
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
        "versoes": {pkg: version(pkg) for pkg in ("ultralytics", "torch")},
        "python": platform.python_version(),
        "concluido_em": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    run_dir = args.output / name
    (run_dir / "treino.json").write_text(json.dumps(record, indent=2, ensure_ascii=False))
    print(f"treino concluído em {minutes:.1f} min; pesos em {run_dir / 'weights'}")


if __name__ == "__main__":
    main()
