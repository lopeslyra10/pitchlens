"""Geometria do campo e sistema de coordenadas do PitchLens.

Todas as etapas do pipeline (homografia, rastreamento em metros e métricas táticas)
compartilham o mesmo referencial:

- origem no canto superior esquerdo do campo, como visto pela câmera principal;
- eixo ``x`` ao longo do comprimento, de 0 a ``length``, da esquerda para a direita;
- eixo ``y`` ao longo da largura, de 0 a ``width``, de cima para baixo;
- unidades em metros.

O eixo ``y`` cresce para baixo, como nas imagens, o que simplifica a leitura das
homografias e o desenho da mesa tática.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

Point = tuple[float, float]


@dataclass(frozen=True)
class PitchSpec:
    """Dimensões de um campo de futebol, por padrão as recomendadas pela FIFA (105 x 68 m)."""

    length: float = 105.0
    width: float = 68.0
    penalty_area_depth: float = 16.5
    penalty_area_width: float = 40.32
    goal_area_depth: float = 5.5
    goal_area_width: float = 18.32
    penalty_spot_distance: float = 11.0
    center_circle_radius: float = 9.15

    def __post_init__(self) -> None:
        if self.length <= 0 or self.width <= 0:
            raise ValueError("comprimento e largura do campo devem ser positivos")
        if self.width >= self.length:
            raise ValueError("a largura do campo deve ser menor que o comprimento")
        if not self.goal_area_width < self.penalty_area_width < self.width:
            raise ValueError("a pequena área deve caber na grande área, e a grande área no campo")
        if not self.goal_area_depth < self.penalty_area_depth:
            raise ValueError("a pequena área deve ser menos profunda que a grande área")
        if self.penalty_area_depth + self.center_circle_radius >= self.length / 2:
            raise ValueError("a grande área não pode alcançar o círculo central")

    @property
    def center(self) -> Point:
        """Centro do campo (marca do meio-campo)."""
        return (self.length / 2, self.width / 2)

    def contains(self, x: float, y: float, margin: float = 0.0) -> bool:
        """Indica se ``(x, y)`` está dentro do campo, com tolerância opcional em metros."""
        return -margin <= x <= self.length + margin and -margin <= y <= self.width + margin

    def reflect_across_halfway(self, point: Point) -> Point:
        """Espelha um ponto na linha do meio-campo, trocando o lado esquerdo pelo direito."""
        x, y = point
        return (self.length - x, y)

    def rotate_half_turn(self, point: Point) -> Point:
        """Gira um ponto 180 graus em torno do centro do campo.

        Converte a posição de um time que ataca para a esquerda no referencial de quem
        ataca para a direita, preservando os lados do time: o lateral esquerdo continua
        à esquerda na direção do ataque. As análises de formação usam essa normalização.
        """
        x, y = point
        return (self.length - x, self.width - y)

    def keypoints(self) -> dict[str, Point]:
        """Pontos de referência do gramado, em metros, usados para estimar a homografia."""
        length, width = self.length, self.width
        cx, cy = self.center
        radius = self.center_circle_radius
        penalty_top = cy - self.penalty_area_width / 2
        penalty_bottom = cy + self.penalty_area_width / 2
        goal_top = cy - self.goal_area_width / 2
        goal_bottom = cy + self.goal_area_width / 2

        points: dict[str, Point] = {
            "corner_top_left": (0.0, 0.0),
            "corner_bottom_left": (0.0, width),
            "corner_top_right": (length, 0.0),
            "corner_bottom_right": (length, width),
            "halfway_top": (cx, 0.0),
            "halfway_bottom": (cx, width),
            "center_spot": (cx, cy),
            "center_circle_top": (cx, cy - radius),
            "center_circle_bottom": (cx, cy + radius),
            "center_circle_left": (cx - radius, cy),
            "center_circle_right": (cx + radius, cy),
        }
        for side, goal_x, direction in (("left", 0.0, 1.0), ("right", length, -1.0)):
            penalty_x = goal_x + direction * self.penalty_area_depth
            goal_area_x = goal_x + direction * self.goal_area_depth
            points.update(
                {
                    f"{side}_penalty_area_goal_top": (goal_x, penalty_top),
                    f"{side}_penalty_area_top": (penalty_x, penalty_top),
                    f"{side}_penalty_area_bottom": (penalty_x, penalty_bottom),
                    f"{side}_penalty_area_goal_bottom": (goal_x, penalty_bottom),
                    f"{side}_goal_area_goal_top": (goal_x, goal_top),
                    f"{side}_goal_area_top": (goal_area_x, goal_top),
                    f"{side}_goal_area_bottom": (goal_area_x, goal_bottom),
                    f"{side}_goal_area_goal_bottom": (goal_x, goal_bottom),
                    f"{side}_penalty_spot": (goal_x + direction * self.penalty_spot_distance, cy),
                }
            )
        return points

    def keypoints_array(self, names: Sequence[str] | None = None) -> np.ndarray:
        """Pontos de referência como array ``(N, 2)`` em ``float32``, na ordem pedida.

        É o formato esperado por ``cv2.findHomography``: basta alinhar estes pontos com os
        mesmos pontos detectados na imagem.
        """
        available = self.keypoints()
        selected = list(available) if names is None else list(names)
        unknown = [name for name in selected if name not in available]
        if unknown:
            raise KeyError(f"pontos de referência desconhecidos: {', '.join(unknown)}")
        return np.array([available[name] for name in selected], dtype=np.float32)


FIFA_PITCH = PitchSpec()
"""Campo padrão de 105 x 68 m, usado quando nenhuma dimensão é informada."""
