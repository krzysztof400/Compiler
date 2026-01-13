from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "example7.imp"

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

    mr_path = tmp_path / "example7.mr"
    mr_path.write_text("\n".join(mr_lines) + "\n")
    return mr_path


def _extract_ints(stdout: bytes) -> list[int]:
    out = stdout.decode(errors="replace")
    return [int(tok) for tok in out.replace("?", " ").replace(">", " ").split() if tok.lstrip("-").isdigit()]


@pytest.mark.parametrize(
    "a,b,c",
    [
        (0, 0, 0),
        (1, 0, 2),
        (10, 20, 30),
    ],
)
def test_example7_nested_loops_accumulation(tmp_path: Path, a: int, b: int, c: int):
    """example7 is intended as a stress test for nested loops.

    It adds:
    - sum(k=11..20) = 155 to `a` * 10 inner j iters * 20 outer i iters
    - sum(j=200..209) = 2045 to `b` * 20 outer i iters
    - sum(i=111091..111110) to `c`
    """

    mr_path = _compile_fixture_to_mr(tmp_path)

    vm = REPO_ROOT / "VM" / "maszyna-wirtualna"
    proc = subprocess.run(
        [str(vm), str(mr_path)],
        input=f"{a}\n{b}\n{c}\n".encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=2,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr.decode(errors="replace")

    nums = _extract_ints(proc.stdout)
    assert len(nums) >= 3
    out_a, out_b, out_c = nums[-3], nums[-2], nums[-1]

    expected_a = a + 155 * 10 * 20
    expected_b = b + 2045 * 20
    expected_c = c + sum(range(111091, 111111))
    assert (out_a, out_b, out_c) == (expected_a, expected_b, expected_c)
