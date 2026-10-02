"""Treino do modelo de pontos do gramado (Fase 3).

Usa o RF-DETR em modo keypoints, no dataset COCO baixado por ``download_data.py keypoints``.
O esquema de pontos (quantos e com que tolerância) é lido do próprio dataset, e a ordem dos
pontos no campo está em ``pitchlens.pitch.KEYPOINT_ORDER``.

Uso:
    python scripts/train_keypoints.py --epochs 60 --batch-size 4 --grad-accum 4
"""

from __future__ import annotations

import argparse
import json
import platform
import time
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

from pitchlens.console import use_utf8_output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Treina o modelo de pontos do gramado.")
    parser.add_argument("--dataset", type=Path, default=Path("data/datasets/football-field"))
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--grad-accum", type=int, default=4)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--resolution", type=int, default=None)
    parser.add_argument("--patience", type=int, default=15)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=Path("runs/keypoints"))
    parser.add_argument("--resume", nargs="?", const="last.ckpt", default=None)
    return parser.parse_args()


def main() -> None:
    use_utf8_output()
    args = parse_args()

    import torch
    from rfdetr import RFDETRKeypointPreview
    from rfdetr.datasets._keypoint_schema import infer_coco_keypoint_schema

    torch.manual_seed(args.seed)
    args.output.mkdir(parents=True, exist_ok=True)
    schema = infer_coco_keypoint_schema(args.dataset / "train" / "_annotations.coco.json")

    options = {
        "dataset_file": "roboflow",
        "dataset_dir": str(args.dataset),
        "output_dir": str(args.output),
        "class_names": schema.class_names,
        "keypoint_oks_sigmas": schema.keypoint_oks_sigmas,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "grad_accum_steps": args.grad_accum,
        "lr": args.lr,
        "lr_encoder": args.lr,
        "early_stopping": True,
        "early_stopping_patience": args.patience,
        "use_ema": False,
        "run_test": False,
    }
    if args.resolution:
        options["resolution"] = args.resolution
    if args.resume:
        checkpoint = Path(args.resume)
        options["resume"] = str(
            checkpoint if checkpoint.is_absolute() else args.output / checkpoint
        )

    model = RFDETRKeypointPreview(
        num_classes=len(schema.class_names),
        num_keypoints_per_class=schema.num_keypoints_per_class,
    )
    started = time.perf_counter()
    model.train(**options)
    minutes = (time.perf_counter() - started) / 60

    record = {
        "modelo": "RF-DETR keypoints (preview)",
        "pontos": schema.num_keypoints_per_class,
        "classes": list(schema.class_names),
        "opcoes": {k: v for k, v in options.items() if k != "keypoint_oks_sigmas"},
        "seed": args.seed,
        "duracao_min": round(minutes, 1),
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
        "versoes": {pkg: version(pkg) for pkg in ("rfdetr", "torch")},
        "python": platform.python_version(),
        "concluido_em": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    (args.output / "treino.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"treino concluído em {minutes:.1f} min; pesos em {args.output}")


if __name__ == "__main__":
    main()
