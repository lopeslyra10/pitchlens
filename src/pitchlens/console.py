"""Saída de console em UTF-8.

No Windows, quando a saída do Python vai para um arquivo (logs de treino em segundo plano ou
redirecionamento no terminal), a codificação padrão é cp1252. Bibliotecas como o rich, usado
nas barras de progresso do treino, quebram ao escrever caracteres como "━" nessa codificação.
"""

from __future__ import annotations

import sys


def use_utf8_output() -> None:
    """Reconfigura stdout e stderr para UTF-8 antes de qualquer biblioteca escrever neles."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")
