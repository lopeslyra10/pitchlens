"""Pipeline da Fase 2: detecção, rastreamento, times e vídeo anotado.

O vídeo é percorrido duas vezes, mas o detector roda uma só:

1. detecta todos os frames e, em frames espaçados, coleta a cor do tronco dos jogadores;
2. aprende as duas cores de uniforme com essa amostra;
3. percorre o vídeo de novo, reaproveitando as detecções, para rastrear, atribuir os times e
   desenhar o resultado.

Calibrar os times antes de rastrear evita que as primeiras cores vistas decidam tudo.

O rastreador vem do pacote ``trackers`` (Apache 2.0). O BoT-SORT é o padrão porque compensa
o movimento da câmera; o ByteTrack fica disponível para comparação.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from pitchlens.detection.annotate import class_names_of
from pitchlens.tracking.annotate import REFEREE_GROUP, UNKNOWN_GROUP, TrackAnnotator
from pitchlens.tracking.stats import TrackingStats
from pitchlens.tracking.teams import (
    NO_TEAM,
    TeamClassifier,
    TeamVoter,
    assign_goalkeepers,
    jersey_color,
    torso_crop,
)

if TYPE_CHECKING:
    import supervision as sv

    from pitchlens.detection.detector import Detector

CALIBRATION_STRIDE = 5
MIN_CALIBRATION_SAMPLES = 20
LOST_TRACK_SECONDS = 2.0
TRACE_SECONDS = 1.5
TRACKERS = ("botsort", "bytetrack")
# O detector roda com limiar baixo para o rastreador aproveitar detecções fracas. A calibração
# dos times e a bola usam limiares próprios, mais altos, para não aprender ou desenhar ruído.
CALIBRATION_MIN_CONFIDENCE = 0.5
BALL_MIN_CONFIDENCE = 0.3


def make_tracker(name: str, fps: float):
    """Cria o rastreador pelo nome, com o fps do vídeo e 2 s de tolerância para reencontrar."""
    import trackers

    options = {"frame_rate": fps, "lost_track_buffer": round(fps * LOST_TRACK_SECONDS)}
    if name == "botsort":
        return trackers.BoTSORTTracker(**options)
    if name == "bytetrack":
        return trackers.ByteTrackTracker(**options)
    raise ValueError(f"rastreador desconhecido: {name} (opções: {', '.join(TRACKERS)})")


def collect(detector: Detector, video: Path) -> tuple[list[sv.Detections], np.ndarray]:
    """Detecta todos os frames e coleta cores de uniforme a cada ``CALIBRATION_STRIDE``."""
    from pitchlens.video import iter_frames

    detections, colors = [], []
    for index, frame in enumerate(iter_frames(video)):
        frame_detections = detector.predict(frame)
        detections.append(frame_detections)
        if index % CALIBRATION_STRIDE:
            continue
        names = class_names_of(frame_detections)
        confident = frame_detections.confidence >= CALIBRATION_MIN_CONFIDENCE
        for box, name, keep in zip(frame_detections.xyxy, names, confident, strict=True):
            if name != "player" or not keep:
                continue
            if (color := jersey_color(torso_crop(frame, box))) is not None:
                colors.append(color)
    return detections, np.array(colors)


def best_ball(balls: sv.Detections) -> sv.Detections:
    """Só existe uma bola: fica a detecção mais confiável, se passar do limiar."""
    if len(balls) == 0:
        return balls
    best = int(np.argmax(balls.confidence))
    return balls[[best]] if balls.confidence[best] >= BALL_MIN_CONFIDENCE else balls[[]]


def bottom_centers(detections: sv.Detections) -> np.ndarray:
    """Ponto dos pés de cada detecção: centro da borda inferior da caixa."""
    xyxy = detections.xyxy
    return np.column_stack([(xyxy[:, 0] + xyxy[:, 2]) / 2, xyxy[:, 3]])


def assign_groups(
    frame: np.ndarray, tracked: sv.Detections, classifier: TeamClassifier, voter: TeamVoter
) -> tuple[np.ndarray, np.ndarray]:
    """Time (0, 1 ou sem time) e grupo de desenho de cada detecção rastreada."""
    names = np.array(class_names_of(tracked))
    is_player, is_goalkeeper = names == "player", names == "goalkeeper"

    votes = np.full(len(tracked), NO_TEAM, dtype=int)
    for index in np.flatnonzero(is_player):
        color = jersey_color(torso_crop(frame, tracked.xyxy[index]))
        if color is not None:
            votes[index] = int(classifier.predict(color)[0])

    teams = np.full(len(tracked), NO_TEAM, dtype=int)
    teams[is_player] = voter.update(tracked.tracker_id[is_player], votes[is_player])
    if is_goalkeeper.any():
        known = is_player & (teams != NO_TEAM)
        positions = bottom_centers(tracked)
        teams[is_goalkeeper] = assign_goalkeepers(
            positions[is_goalkeeper], positions[known], teams[known]
        )

    groups = np.where(teams != NO_TEAM, teams, UNKNOWN_GROUP)
    groups[names == "referee"] = REFEREE_GROUP
    return teams, groups


def track_video(
    detector: Detector, video: Path, output: Path, *, tracker_name: str = "botsort"
) -> dict:
    """Gera o vídeo anotado com times, identificadores e rastros e devolve os indicadores."""
    from pitchlens.video import VideoWriter, iter_frames, probe

    info = probe(video)
    started = time.perf_counter()
    detections, colors = collect(detector, video)
    if len(colors) < MIN_CALIBRATION_SAMPLES:
        raise RuntimeError(
            f"só {len(colors)} amostras de uniforme; o vídeo precisa mostrar mais jogadores"
        )

    classifier = TeamClassifier().fit(colors)
    tracker = make_tracker(tracker_name, info.fps)
    voter = TeamVoter()
    stats = TrackingStats(info.fps)
    annotator = TrackAnnotator(
        classifier.team_colors_hex(), trace_length=round(info.fps * TRACE_SECONDS)
    )

    width, height = info.width - info.width % 2, info.height - info.height % 2
    with VideoWriter(output, fps=info.fps, size=(width, height)) as writer:
        for frame, frame_detections in zip(iter_frames(video), detections, strict=False):
            names = np.array(class_names_of(frame_detections))
            ball = best_ball(frame_detections[names == "ball"])
            tracked = tracker.update(frame_detections[names != "ball"], frame=frame)
            tracked = tracked[tracked.tracker_id >= 0]
            teams, groups = assign_groups(frame, tracked, classifier, voter)
            stats.update(tracked.tracker_id, teams)
            scene = annotator.annotate(frame, tracked, groups, ball)
            writer.write(scene[:height, :width])

    summary = stats.summary()
    summary["rastreador"] = tracker_name
    summary["cores_dos_times"] = classifier.team_colors_hex()
    summary["amostras_de_uniforme"] = len(colors)
    summary["fps_processamento"] = round(stats.frames / (time.perf_counter() - started), 1)
    return summary
