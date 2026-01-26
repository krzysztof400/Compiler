from __future__ import annotations

import sys
from pathlib import Path
import re

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


def extract_koszt(stdout: bytes, stderr: bytes | None = None) -> int | None:
    """Extract the koszt value from VM output if present."""

    combined = stdout
    if stderr:
        combined = combined + b"\n" + stderr

    out = combined.decode(errors="replace")
    # Strip ANSI color codes if present.
    out = re.sub(r"\x1b\[[0-9;]*m", "", out)

    for line in out.splitlines():
        lower = line.lower()
        if "koszt" not in lower:
            continue

        match = re.search(r"koszt:\s*([0-9,]+)", lower)
        if match:
            return int(match.group(1).replace(",", ""))

        numbers = re.findall(r"\d+", line)
        if numbers:
            return int(numbers[0])

    return None


def record_koszt(request, stdout: bytes, stderr: bytes | None = None) -> int | None:
    """Attach koszt to the pytest node so reporting hooks can display it."""

    cost = extract_koszt(stdout, stderr)
    if cost is not None:
        setattr(request.node, "koszt", cost)
    return cost


def extract_ints(stdout: bytes, *, allow_negative: bool = True) -> list[int]:
    """Extract ints from VM stdout.

    The VM prompts with '?' and '>' so we replace those before splitting.
    Lines containing "koszt" are ignored to avoid mixing costs with outputs.
    """

    out = stdout.decode(errors="replace")
    filtered_lines = [line for line in out.splitlines() if "koszt" not in line.lower()]
    tokens = "\n".join(filtered_lines).replace("?", " ").replace(">", " ").split()

    if allow_negative:
        return [int(tok) for tok in tokens if tok.lstrip("-").isdigit()]
    return [int(tok) for tok in tokens if tok.isdigit()]
