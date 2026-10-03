"""Avaliação do modelo de pontos do gramado e da calibração (Fase 3).

Duas medidas, porque uma não substitui a outra:

- **erro dos pontos**, em pixels: quanto o modelo erra cada ponto em relação à anotação. Diz
  se o modelo aprendeu, mas não diz o que isso significa no campo.
- **erro de reprojeção**, em metros: ajusta a homografia com os pontos que o modelo previu e
  mede quanto os pontos anotados caem fora do lugar. É o número que importa para a leitura
  tática, e o que entra no relatório da fase.

O mesmo cálculo roda com os pontos anotados, para separar o erro do modelo do teto da
geometria: com anotação perfeita o erro não é zero, porque a própria anotação tem ruído.

Uso:
    python scripts/evaluate_keypoints.py --weights runs/keypoints/checkpoint_best_regular.pth
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from pitchlens.calibration.homography import (
    MAX_ERROR_M,
    MIN_INLIER_FRACTION,
    MIN_POINTS_PER_FRAME,
    fit_homography,
    reprojection_errors_m,
    visible_keypoints,
)
from pitchlens.console import use_utf8_output
from pitchlens.pitch import KEYPOINT_ORDER


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Avalia o modelo de pontos do gramado.")
    parser.add_argument("--dataset", type=Path, default=Path("data/datasets/football-field"))
    parser.add_argument("--split", default="test")
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--threshold", type=float, default=0.3)
    parser.add_argument("--min-confidence", type=float, default=0.5)
    parser.add_argument("--out", type=Path, default=Path("reports/fase-3"))
    return parser.parse_args()


def annotations(dataset: Path, split: str) -> list[tuple[Path, np.ndarray]]:
    """Imagens do split com seus pontos anotados ``(32, 3)``: x, y e visibilidade."""
    coco = json.loads((dataset / split / "_annotations.coco.json").read_text(encoding="utf-8"))
    files = {image["id"]: dataset / split / image["file_name"] for image in coco["images"]}
    return [
        (files[ann["image_id"]], np.array(ann["keypoints"], dtype=np.float64).reshape(-1, 3))
        for ann in coco["annotations"]
        if ann["image_id"] in files
    ]


def usable(homography) -> bool:
    """Aplica ao ajuste as mesmas exigências do pipeline, para o número bater com o vídeo."""
    return (
        homography is not None
        and homography.error_m <= MAX_ERROR_M
        and homography.inliers >= MIN_POINTS_PER_FRAME
        and homography.inliers >= MIN_INLIER_FRACTION * homography.points
    )


def calibrate(points: np.ndarray, scores: np.ndarray, min_confidence: float) -> dict | None:
    """Ajusta a homografia com os pontos informados e devolve o erro em metros."""
    image, pitch = visible_keypoints(points, scores, min_confidence=min_confidence)
    if len(image) < MIN_POINTS_PER_FRAME:
        return None
    homography = fit_homography(image, pitch)
    if not usable(homography):
        return None
    errors = reprojection_errors_m(homography.matrix, image, pitch)
    return {
        "erro_m": homography.error_m,
        "erro_maximo_m": float(np.max(errors)),
        "pontos": len(image),
        "aceitos": homography.inliers,
    }


def summarize(name: str, results: list[dict | None], total: int) -> dict:
    """Resume os ajustes de um conjunto de imagens."""
    done = [result for result in results if result is not None]
    if not done:
        return {"fonte": name, "imagens": total, "calibradas": 0}
    errors = np.array([result["erro_m"] for result in done])
    return {
        "fonte": name,
        "imagens": total,
        "calibradas": len(done),
        "cobertura_pct": round(len(done) / total, 3),
        "erro_mediano_m": round(float(np.median(errors)), 2),
        "erro_p95_m": round(float(np.percentile(errors, 95)), 2),
        "erro_maximo_m": round(float(errors.max()), 2),
        "pontos_por_imagem": round(float(np.mean([r["pontos"] for r in done])), 1),
    }


def main() -> None:
    use_utf8_output()
    args = parse_args()
    import cv2

    from pitchlens.calibration.detector import PitchKeypointDetector

    model = PitchKeypointDetector(args.weights, threshold=args.threshold)
    data = annotations(args.dataset, args.split)

    pixel_errors: list[float] = []
    found: list[float] = []
    from_model: list[dict | None] = []
    from_labels: list[dict | None] = []

    for image_file, labelled in data:
        frame = cv2.imread(str(image_file))
        if frame is None:
            raise FileNotFoundError(f"não foi possível ler a imagem: {image_file}")
        points, scores = model.predict(frame)

        marked = labelled[:, 2] > 0
        distances = np.linalg.norm(points[marked] - labelled[marked, :2], axis=1)
        pixel_errors.extend(distances.tolist())
        found.append(float(np.mean(scores[marked] >= args.min_confidence)) if marked.any() else 0.0)

        from_model.append(calibrate(points, scores, args.min_confidence))
        from_labels.append(calibrate(labelled[:, :2], labelled[:, 2], 1.0))

    report = {
        "modelo": str(args.weights),
        "split": args.split,
        "pontos": len(KEYPOINT_ORDER),
        "erro_dos_pontos_px": {
            "mediano": round(float(np.median(pixel_errors)), 1),
            "p95": round(float(np.percentile(pixel_errors, 95)), 1),
        },
        "pontos_anotados_encontrados_pct": round(float(np.mean(found)), 3),
        "calibracao": [
            summarize("modelo", from_model, len(data)),
            summarize("anotação", from_labels, len(data)),
        ],
    }

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "keypoints.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
