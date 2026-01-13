from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(REPO_ROOT / "src"))

from code_generator import CodeGenerator
from my_lexer import MyLexer
from my_parser import MyParser
from semantic_analyzer import SemanticAnalyzer


def compile_source_to_mr(source: str) -> str:
    """Compile IMP source text to MR text."""

    lexer = MyLexer()
    parser = MyParser()

    ast = parser.parse(lexer.tokenize(source))
    assert ast is not None, "Parsing failed: AST is None"

    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)

    gen = CodeGenerator(analyzer)
    mr_lines = gen.generate(ast)
    return "\n".join(mr_lines) + "\n"


def compile_fixture_to_mr_path(*, fixture_path: Path, tmp_path: Path, out_name: str | None = None) -> Path:
    """Compile an .imp fixture file to a .mr file in tmp_path."""

    out_name = out_name or f"{fixture_path.stem}.mr"
    mr_text = compile_source_to_mr(fixture_path.read_text())

    mr_path = tmp_path / out_name
    mr_path.write_text(mr_text)
    return mr_path


def extract_ints(stdout: bytes, *, allow_negative: bool = True) -> list[int]:
    """Extract ints from VM stdout.

    The VM prompts with '?' and '>' so we replace those before splitting.
    """

    out = stdout.decode(errors="replace")
    tokens = out.replace("?", " ").replace(">", " ").split()

    if allow_negative:
        return [int(tok) for tok in tokens if tok.lstrip("-").isdigit()]
    return [int(tok) for tok in tokens if tok.isdigit()]
