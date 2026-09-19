"""Folha de conferência da separação de times (Fase 2).

Monta uma imagem com recortes de jogadores de frames espaçados, agrupados pelo time previsto
para cada detecção isolada (time A, time B ou sem time), sem o voto por identificador. Assim a
conferência mede o classificador de cor sozinho, que é o caso mais difícil. Cada recorte recebe
um número para anotar os erros encontrados na conferência visual.

Uso:
    python scripts/team_sheet.py data/raw/u17-nz-can-25.webm \
        --weights runs/rfdetr-medium/checkpoint_best_total.pth
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from pitchlens.console import use_utf8_output

TILE_WIDTH, TILE_HEIGHT, COLUMNS = 72, 144, 12
MIN_CONFIDENCE = 0.5


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Folha de conferência da separação de times.")
    parser.add_argument("video", type=Path)
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--frames", type=int, default=12, help="frames espaçados na amostra")
    parser.add_argument("--out", type=Path, default=Path("reports/fase-2"))
    return parser.parse_args()


def tile(crop: np.ndarray, number: int, team_color: tuple[int, int, int]) -> np.ndarray:
    import cv2

    canvas = np.full((TILE_HEIGHT + 18, TILE_WIDTH, 3), 24, dtype=np.uint8)
    height, width = crop.shape[:2]
    scale = min(TILE_WIDTH / width, TILE_HEIGHT / height)
    resized = cv2.resize(crop, (max(1, int(width * scale)), max(1, int(height * scale))))
    top, left = 18 + (TILE_HEIGHT - resized.shape[0]) // 2, (TILE_WIDTH - resized.shape[1]) // 2
    canvas[top : top + resized.shape[0], left : left + resized.shape[1]] = resized
    canvas[:18] = team_color
    cv2.putText(canvas, str(number), (4, 13), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 0), 1)
    return canvas


def main() -> None:
    use_utf8_output()
    args = parse_args()

    import cv2

    from pitchlens.detection.annotate import class_names_of
    from pitchlens.detection.detector import RFDETRDetector
    from pitchlens.tracking.pipeline import collect
    from pitchlens.tracking.teams import NO_TEAM, TeamClassifier, jersey_color, torso_crop
    from pitchlens.video import iter_frames

    detector = RFDETRDetector(args.weights, threshold=0.1)
    detections, colors = collect(detector, args.video)
    classifier = TeamClassifier().fit(colors)
    team_bgr = {
        team: tuple(int(h[i : i + 2], 16) for i in (5, 3, 1))
        for team, h in enumerate(classifier.team_colors_hex())
    }
    team_bgr[NO_TEAM] = (160, 165, 154)

    chosen = set(np.linspace(0, len(detections) - 1, args.frames).round().astype(int).tolist())
    tiles: dict[int, list[np.ndarray]] = {0: [], 1: [], NO_TEAM: []}
    records = []
    for index, frame in enumerate(iter_frames(args.video)):
        if index not in chosen:
            continue
        frame_detections = detections[index]
        names = class_names_of(frame_detections)
        for box, name, confidence in zip(
            frame_detections.xyxy, names, frame_detections.confidence, strict=True
        ):
            if name != "player" or confidence < MIN_CONFIDENCE:
                continue
            color = jersey_color(torso_crop(frame, box))
            if color is None:
                continue
            team = int(classifier.predict(color)[0])
            number = len(records) + 1
            x1, y1, x2, y2 = box.round().astype(int)
            crop = frame[max(y1, 0) : y2, max(x1, 0) : x2]
            tiles[team].append(tile(crop, number, team_bgr[team]))
            records.append(
                {
                    "numero": number,
                    "frame": index,
                    "time_previsto": team,
                    "cor": [round(float(c), 3) for c in color],
                }
            )

    rows = []
    for team in (0, 1, NO_TEAM):
        items = tiles[team]
        if not items:
            continue
        for start in range(0, len(items), COLUMNS):
            row = items[start : start + COLUMNS]
            row += [np.full_like(row[0], 24)] * (COLUMNS - len(row))
            rows.append(np.hstack(row))
        rows.append(np.full((10, rows[-1].shape[1], 3), 255, dtype=np.uint8))

    args.out.mkdir(parents=True, exist_ok=True)
    sheet = args.out / f"times-{args.video.stem}.jpg"
    cv2.imwrite(str(sheet), np.vstack(rows[:-1]), [cv2.IMWRITE_JPEG_QUALITY, 85])
    (args.out / f"times-{args.video.stem}.json").write_text(
        json.dumps(
            {
                "cores": classifier.team_colors_hex(),
                "raios": [round(float(r), 3) for r in classifier.radii],
                "recortes": records,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    counts = {team: len(items) for team, items in tiles.items()}
    print(
        f"{len(records)} recortes (time A: {counts[0]}, time B: {counts[1]}, "
        f"sem time: {counts[NO_TEAM]}) -> {sheet}"
    )


if __name__ == "__main__":
    main()
