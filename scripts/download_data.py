"""Baixa os dados da Fase 1: dataset rotulado (Roboflow) e clipes de vídeo (Kaggle).

As credenciais ficam no ``.env`` (ver ``.env.example``) e os arquivos baixados ficam fora do
Git. Versão do dataset e clipes usados são registrados em ``data/sources.json`` para que o
treino possa ser reproduzido.

Uso:
    python scripts/download_data.py dataset          # dataset em formato YOLO
    python scripts/download_data.py clips            # clipes de 30 s da competição DFL
    python scripts/download_data.py stats            # contagens do dataset baixado
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

WORKSPACE = "roboflow-jvuqo"
PROJECT = "football-players-detection-3zvbc"
DATASET_DIR = Path("data/datasets/football-players")
COMPETITION = "dfl-bundesliga-data-shootout"
CLIPS_DIR = Path("data/raw")
SOURCES_FILE = Path("data/sources.json")
SPLITS = ("train", "valid", "test")
# Clipes da câmera principal usados como referência em projetos públicos de futebol.
DEFAULT_CLIPS = ["08fd33_0", "0bfacc_0", "121364_0", "2e57b9_0", "573e61_0"]


def load_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def update_sources(key: str, value: dict) -> None:
    sources = json.loads(SOURCES_FILE.read_text(encoding="utf-8")) if SOURCES_FILE.exists() else {}
    sources[key] = value
    SOURCES_FILE.write_text(json.dumps(sources, indent=2, ensure_ascii=False) + "\n", "utf-8")


def normalized_yaml(exported: dict, root: Path) -> dict:
    """Ajusta o data.yaml exportado pelo Roboflow.

    O export aponta para ``../train/images``, que o Ultralytics resolve fora da pasta do
    dataset. Com ``path`` na própria pasta, RF-DETR e YOLO leem o mesmo arquivo sem ajustes.
    """
    return {
        **exported,
        "path": str(root.resolve()),
        "train": "train/images",
        "val": "valid/images",
        "test": "test/images",
    }


def _ball_sizes_px(root: Path, class_names: list[str]) -> list[float]:
    try:
        from PIL import Image
    except ImportError:
        return []
    if "ball" not in class_names:
        return []
    ball_id = class_names.index("ball")
    sizes = []
    for split in SPLITS:
        for label_file in (root / split / "labels").glob("*.txt"):
            images = list((root / split / "images").glob(f"{label_file.stem}.*"))
            try:
                width, height = Image.open(images[0]).size
            except (IndexError, OSError):
                continue
            for line in label_file.read_text().splitlines():
                parts = line.split()
                if parts and int(parts[0]) == ball_id:
                    sizes.append(max(float(parts[3]) * width, float(parts[4]) * height))
    return sizes


def dataset_stats(root: Path, class_names: list[str]) -> dict:
    """Imagens por split, instâncias por classe e tamanho típico da bola em pixels."""
    images = {}
    instances = dict.fromkeys(class_names, 0)
    for split in SPLITS:
        image_dir, label_dir = root / split / "images", root / split / "labels"
        images[split] = sum(1 for _ in image_dir.glob("*")) if image_dir.exists() else 0
        for label_file in label_dir.glob("*.txt") if label_dir.exists() else []:
            for line in label_file.read_text().splitlines():
                if line.strip():
                    instances[class_names[int(line.split()[0])]] += 1
    ball_sizes = _ball_sizes_px(root, class_names)
    return {
        "imagens": images,
        "instancias": instances,
        "bola_px_mediana": round(statistics.median(ball_sizes), 1) if ball_sizes else None,
    }


def download_dataset(version: int | None) -> None:
    import yaml
    from roboflow import Roboflow

    api_key = os.environ.get("ROBOFLOW_API_KEY")
    if not api_key:
        raise SystemExit("defina ROBOFLOW_API_KEY no .env (veja .env.example)")

    project = Roboflow(api_key=api_key).workspace(WORKSPACE).project(PROJECT)
    if version is None:
        version = max(int(str(v.version).rsplit("/", 1)[-1]) for v in project.versions())
    project.version(version).download("yolov8", location=str(DATASET_DIR), overwrite=True)

    data_yaml = DATASET_DIR / "data.yaml"
    exported = yaml.safe_load(data_yaml.read_text(encoding="utf-8"))
    data = normalized_yaml(exported, DATASET_DIR)
    data_yaml.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), "utf-8")

    update_sources(
        "dataset",
        {
            "fonte": "Roboflow Universe",
            "url": f"https://universe.roboflow.com/{WORKSPACE}/{PROJECT}/dataset/{version}",
            "versao": version,
            "formato": "yolov8",
            "licenca": "CC BY 4.0",
            "classes": list(data["names"]),
            "baixado_em": now(),
        },
    )
    print(f"dataset v{version} salvo em {DATASET_DIR}")
    print(json.dumps(dataset_stats(DATASET_DIR, list(data["names"])), indent=2))


def kaggle_cli() -> str:
    local = Path(sys.executable).parent / ("kaggle.exe" if os.name == "nt" else "kaggle")
    return shutil.which("kaggle") or str(local)


def download_clips(clip_ids: list[str]) -> None:
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    for clip_id in clip_ids:
        target = CLIPS_DIR / f"{clip_id}.mp4"
        if target.exists():
            print(f"{target} já existe")
            continue
        command = [kaggle_cli(), "competitions", "download", "-c", COMPETITION]
        command += ["-f", f"clips/{clip_id}.mp4", "-p", str(CLIPS_DIR), "-q"]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise SystemExit(
                f"falha ao baixar {clip_id}: {detail}\n"
                "Confira se as regras da competição foram aceitas no Kaggle e se o token está"
                " configurado (.env ou `kaggle auth login`)."
            )
        archive = CLIPS_DIR / f"{clip_id}.mp4.zip"
        if archive.exists():
            with zipfile.ZipFile(archive) as bundle:
                bundle.extractall(CLIPS_DIR)
            archive.unlink()
        print(f"{target} baixado")

    update_sources(
        "clips",
        {
            "fonte": f"Kaggle, competição {COMPETITION}",
            "url": f"https://www.kaggle.com/competitions/{COMPETITION}/data",
            "ids": clip_ids,
            "uso": "regras da competição; vídeos não são redistribuídos neste repositório",
            "baixado_em": now(),
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Baixa os dados da Fase 1.")
    commands = parser.add_subparsers(dest="command", required=True)
    dataset = commands.add_parser("dataset", help="dataset rotulado do Roboflow (formato YOLO)")
    dataset.add_argument("--version", type=int, default=None, help="padrão: versão mais recente")
    clips = commands.add_parser("clips", help="clipes de 30 s da competição DFL no Kaggle")
    clips.add_argument("--ids", nargs="+", default=DEFAULT_CLIPS)
    commands.add_parser("stats", help="contagens do dataset já baixado")
    args = parser.parse_args()

    load_env()
    if args.command == "dataset":
        download_dataset(args.version)
    elif args.command == "clips":
        download_clips(args.ids)
    else:
        import yaml

        names = yaml.safe_load((DATASET_DIR / "data.yaml").read_text(encoding="utf-8"))["names"]
        print(json.dumps(dataset_stats(DATASET_DIR, list(names)), indent=2))


if __name__ == "__main__":
    main()
