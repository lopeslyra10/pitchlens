"""Baixa os dados da Fase 1: dataset rotulado (Roboflow) e vídeos de licença livre.

A chave do Roboflow fica no ``.env`` (ver ``.env.example``) e os arquivos baixados ficam fora
do Git. Versão do dataset, origem, autor e licença de cada vídeo são registrados em
``data/sources.json``, para que o treino possa ser reproduzido e as licenças respeitadas.

Uso:
    python scripts/download_data.py dataset          # dataset em formato YOLO
    python scripts/download_data.py videos           # vídeos de demonstração (ADR-0004)
    python scripts/download_data.py stats            # contagens do dataset baixado
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import urllib.request
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from pitchlens.console import use_utf8_output

WORKSPACE = "roboflow-jvuqo"
PROJECT = "football-players-detection-3zvbc"
DATASET_DIR = Path("data/datasets/football-players")
VIDEOS_DIR = Path("data/raw")
SOURCES_FILE = Path("data/sources.json")
SPLITS = ("train", "valid", "test")
USER_AGENT = "PitchLens/0.2 (https://github.com/lopeslyra10/pitchlens)"


@dataclass(frozen=True)
class VideoSource:
    """Vídeo de demonstração com a origem e a licença que precisam ser respeitadas."""

    arquivo: str
    download: str
    pagina: str
    autor: str
    licenca: str
    uso: str


# Escolhidos por licença livre e ângulo alto (ADR-0004). Nenhum deles é redistribuído aqui.
VIDEOS = [
    VideoSource(
        arquivo="pexels-2657261.mp4",
        download="https://videos.pexels.com/video-files/2657261/2657261-uhd_3840_2160_24fps.mp4",
        pagina="https://www.pexels.com/video/aerial-footage-of-a-game-of-soccer-2657261/",
        autor="Pexels (ver página)",
        licenca="Licença Pexels",
        uso="detecção e campo 2D: vista alta e aberta de um jogo 11 contra 11",
    ),
    VideoSource(
        arquivo="pexels-28870860.mp4",
        download="https://videos.pexels.com/video-files/28870860/12500590_1920_1080_30fps.mp4",
        pagina="https://www.pexels.com/video/aerial-view-of-soccer-game-on-green-field-28870860/",
        autor="Benjamin Quezada Arevalo",
        licenca="Licença Pexels",
        uso="campo 2D: drone com vista de cima",
    ),
    VideoSource(
        arquivo="u17-nz-can-25.webm",
        download=(
            "https://upload.wikimedia.org/wikipedia/commons/f/f9/"
            "2018_FIFA_U-17_Women%27s_World_Cup_-_New_Zealand_vs_Canada_-_25.webm"
        ),
        pagina=(
            "https://commons.wikimedia.org/wiki/"
            "File:2018_FIFA_U-17_Women%27s_World_Cup_-_New_Zealand_vs_Canada_-_25.webm"
        ),
        autor="NaBUru38 (Wikimedia Commons)",
        licenca="CC BY-SA 4.0",
        uso="detecção com ângulo baixo; derivados precisam manter a CC BY-SA 4.0",
    ),
]


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
            for line in label_file.read_text(encoding="utf-8").splitlines():
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
            for line in label_file.read_text(encoding="utf-8").splitlines():
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


def download_videos(videos: list[VideoSource]) -> None:
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    for video in videos:
        target = VIDEOS_DIR / video.arquivo
        if target.exists():
            print(f"{target} já existe")
            continue
        request = urllib.request.Request(video.download, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request) as response:
            target.write_bytes(response.read())
        print(f"{target} baixado ({target.stat().st_size / 1e6:.1f} MB)")
    update_sources("videos", {"itens": [asdict(video) for video in videos], "baixado_em": now()})


def main() -> None:
    use_utf8_output()
    parser = argparse.ArgumentParser(description="Baixa os dados da Fase 1.")
    commands = parser.add_subparsers(dest="command", required=True)
    dataset = commands.add_parser("dataset", help="dataset rotulado do Roboflow (formato YOLO)")
    dataset.add_argument("--version", type=int, default=None, help="padrão: versão mais recente")
    commands.add_parser("videos", help="vídeos de demonstração de licença livre")
    commands.add_parser("stats", help="contagens do dataset já baixado")
    args = parser.parse_args()

    load_env()
    if args.command == "dataset":
        download_dataset(args.version)
    elif args.command == "videos":
        download_videos(VIDEOS)
    else:
        import yaml

        names = yaml.safe_load((DATASET_DIR / "data.yaml").read_text(encoding="utf-8"))["names"]
        print(json.dumps(dataset_stats(DATASET_DIR, list(names)), indent=2))


if __name__ == "__main__":
    main()
