"""Garante que o código de src/ e scripts/ lê e grava texto sempre com encoding explícito.

No Windows, sem ``encoding`` o Python usa a codificação local (cp1252). Com o projeto numa
pasta como "IA e Automações", um caminho gravado num JSON ou YAML vira bytes que bibliotecas
como o RF-DETR não conseguem ler de volta em UTF-8. Este teste impede que o problema volte.
"""

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SOURCES = sorted([*ROOT.glob("src/**/*.py"), *ROOT.glob("scripts/**/*.py")])
# Posição do argumento ``encoding`` quando ele é passado sem nome.
ENCODING_POSITION = {"read_text": 0, "write_text": 1}


def _is_binary_open(call: ast.Call) -> bool:
    mode = call.args[1] if len(call.args) > 1 else None
    for keyword in call.keywords:
        if keyword.arg == "mode":
            mode = keyword.value
    return isinstance(mode, ast.Constant) and "b" in str(mode.value)


def missing_encoding(tree: ast.AST) -> list[int]:
    """Linhas com leitura ou escrita de texto sem ``encoding``."""
    lines = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if any(keyword.arg == "encoding" for keyword in node.keywords):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr in ENCODING_POSITION:
            if len(node.args) <= ENCODING_POSITION[func.attr]:
                lines.append(node.lineno)
        elif isinstance(func, ast.Name) and func.id == "open" and not _is_binary_open(node):
            lines.append(node.lineno)
    return sorted(lines)


def test_checker_flags_text_io_without_encoding():
    snippet = (
        "from pathlib import Path\n"
        "Path('a').write_text('x')\n"
        "open('b')\n"
        "open('c', 'rb')\n"
        "Path('d').read_text(encoding='utf-8')\n"
        "Path('e').write_text('x', 'utf-8')\n"
    )

    assert missing_encoding(ast.parse(snippet)) == [2, 3]


@pytest.mark.parametrize("path", SOURCES, ids=lambda path: path.relative_to(ROOT).as_posix())
def test_text_io_declares_encoding(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))

    assert missing_encoding(tree) == [], f"texto sem encoding explícito em {path.name}"
