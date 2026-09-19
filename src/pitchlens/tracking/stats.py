"""Indicadores de estabilidade do rastreamento, sem rótulos.

Um rastreador ideal mantém um identificador por jogador durante todo o clipe. Quando ele
perde o jogador e cria outro número, surgem muitos identificadores e rastros curtos. Por isso
os indicadores principais são a razão entre identificadores criados e jogadores visíveis e a
fração de rastros que duram menos de um segundo.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

import numpy as np


class TrackingStats:
    """Acumula, frame a frame, quem foi visto e em qual time."""

    def __init__(self, fps: float) -> None:
        if fps <= 0:
            raise ValueError("fps deve ser positivo")
        self.fps = fps
        self.frames = 0
        self._frames_seen: Counter[int] = Counter()
        self._visible: list[int] = []
        self._team_counts: list[Counter[int]] = []

    def update(self, tracker_ids: Sequence[int], teams: Sequence[int]) -> None:
        if len(tracker_ids) != len(teams):
            raise ValueError("cada identificador precisa de um time")
        self.frames += 1
        self._frames_seen.update(int(tracker_id) for tracker_id in tracker_ids)
        self._visible.append(len(tracker_ids))
        self._team_counts.append(Counter(int(team) for team in teams))

    def summary(self) -> dict:
        if self.frames == 0:
            return {"frames": 0}
        durations = np.array(list(self._frames_seen.values()), dtype=np.float64) / self.fps
        visible = float(np.mean(self._visible))
        return {
            "frames": self.frames,
            "ids_unicos": len(self._frames_seen),
            "visiveis_por_frame": round(visible, 1),
            "ids_por_visivel": round(len(self._frames_seen) / visible, 2) if visible else None,
            "duracao_mediana_s": round(float(np.median(durations)), 1),
            "rastros_curtos_pct": round(float(np.mean(durations < 1.0)), 3),
            "por_time_por_frame": {
                str(team): round(sum(c[team] for c in self._team_counts) / self.frames, 1)
                for team in sorted({t for c in self._team_counts for t in c})
            },
        }
