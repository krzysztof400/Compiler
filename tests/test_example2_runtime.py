from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "example2.imp"

# Compiler entrypoint uses flat imports
sys.path.append(str(REPO_ROOT / "src"))

from my_lexer import MyLexer
from my_parser import MyParser
from semantic_analyzer import SemanticAnalyzer
from code_generator import CodeGenerator


def _compile_fixture_to_mr(tmp_path: Path) -> Path:
    text = FIXTURE.read_text()

    lexer = MyLexer()
    parser = MyParser()
    ast = parser.parse(lexer.tokenize(text))
    assert ast is not None

    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)

    gen = CodeGenerator(analyzer)
    mr_lines = gen.generate(ast)

    mr_path = tmp_path / "example2.mr"
    mr_path.write_text("\n".join(mr_lines) + "\n")
    return mr_path


def _extract_ints(stdout: bytes) -> list[int]:
    out = stdout.decode(errors="replace")
    return [int(tok) for tok in out.replace("?", " ").replace(">", " ").split() if tok.lstrip("-").isdigit()]


@pytest.mark.parametrize(
    "a,b",
    [
        (0, 1),
        (1, 0),
        (12, 8),
        (123, 456),
        (46368, 28657),
    ],
)
def test_example2_nested_procs_swap_even_times(tmp_path: Path, a: int, b: int):
    """example2 applies nested procedures that repeatedly swap (a,b).

    pd() calls pa() 2^4 * 4 = 16 times total, so (a,b) should end up swapped
    compared to the input.
    """

    mr_path = _compile_fixture_to_mr(tmp_path)

    vm = REPO_ROOT / "VM" / "maszyna-wirtualna"
    proc = subprocess.run(
        [str(vm), str(mr_path)],
        input=f"{a}\n{b}\n".encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=2,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr.decode(errors="replace")

    nums = _extract_ints(proc.stdout)
    assert len(nums) >= 2
    out_a, out_b = nums[-2], nums[-1]
    assert (out_a, out_b) == (b, a)
