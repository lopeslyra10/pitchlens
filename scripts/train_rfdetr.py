"""Fine-tuning do RF-DETR no dataset de futebol (Fase 1).

Uso:
    python scripts/train_rfdetr.py --size medium --epochs 60

Os pesos e logs vão para ``runs/rfdetr-<tamanho>/`` (fora do Git). Ao final, ``treino.json``
registra configuração, versões e duração, para o relatório da fase ser reproduzível.
"""

from __future__ import annotations

import argparse
import json
import platform
import time
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

from pitchlens.detection.detector import RFDETR_SIZES


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fine-tuning do RF-DETR no dataset de futebol.")
    parser.add_argument("--dataset", type=Path, default=Path("data/datasets/football-players"))
    parser.add_argument("--size", choices=list(RFDETR_SIZES), default="medium")
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--batch-size", default="auto", help='inteiro ou "auto" (sonda a GPU)')
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--resolution", type=int, default=None, help="padrão do modelo se omitido")
    parser.add_argument("--patience", type=int, default=15, help="épocas sem melhora até parar")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    import rfdetr
    import torch

    torch.manual_seed(args.seed)
    output = args.output or Path("runs") / f"rfdetr-{args.size}"
    output.mkdir(parents=True, exist_ok=True)

    options = {
        "dataset_dir": str(args.dataset),
        "output_dir": str(output),
        "epochs": args.epochs,
        "batch_size": args.batch_size if args.batch_size == "auto" else int(args.batch_size),
        "lr": args.lr,
        "early_stopping": True,
        "early_stopping_patience": args.patience,
    }
    if args.resolution:
        options["resolution"] = args.resolution

    model = getattr(rfdetr, RFDETR_SIZES[args.size])()
    started = time.perf_counter()
    model.train(**options)
    minutes = (time.perf_counter() - started) / 60

    record = {
        "modelo": f"RF-DETR {args.size}",
        "opcoes": options,
        "seed": args.seed,
        "duracao_min": round(minutes, 1),
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
        "versoes": {pkg: version(pkg) for pkg in ("rfdetr", "torch", "supervision")},
        "python": platform.python_version(),
        "concluido_em": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    (output / "treino.json").write_text(json.dumps(record, indent=2, ensure_ascii=False))
    print(f"treino concluído em {minutes:.1f} min; pesos em {output}")


if __name__ == "__main__":
    main()
