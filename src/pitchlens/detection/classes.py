"""Classes que o detector reconhece e como elas aparecem nas anotações."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ObjectClass:
    """Classe do dataset com rótulo em português e cor usada ao desenhar."""

    name: str
    label: str
    color: str


# As cores seguem a paleta do site: jogadores no verde de destaque e bola em branco.
# A separação por time só chega na Fase 2; até lá, todos os jogadores usam a mesma cor.
OBJECT_CLASSES: dict[str, ObjectClass] = {
    "ball": ObjectClass("ball", "bola", "#FFFFFF"),
    "goalkeeper": ObjectClass("goalkeeper", "goleiro", "#F4D35E"),
    "player": ObjectClass("player", "jogador", "#C8F560"),
    "referee": ObjectClass("referee", "árbitro", "#FF6B6B"),
}

FALLBACK_COLOR = "#9AA5A0"


def label_for(name: str) -> str:
    """Rótulo em português de uma classe; nomes desconhecidos são devolvidos como vieram."""
    known = OBJECT_CLASSES.get(name)
    return known.label if known else name


def color_for(name: str) -> str:
    """Cor hexadecimal de uma classe, com uma cor neutra para classes desconhecidas."""
    known = OBJECT_CLASSES.get(name)
    return known.color if known else FALLBACK_COLOR
