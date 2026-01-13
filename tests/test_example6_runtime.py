from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "example6.imp"

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

    mr_path = tmp_path / "example6.mr"
    mr_path.write_text("\n".join(mr_lines) + "\n")
    return mr_path


def _extract_ints(stdout: bytes) -> list[int]:
    out = stdout.decode(errors="replace")
    return [int(tok) for tok in out.replace("?", " ").replace(">", " ").split() if tok.lstrip("-").isdigit()]


def _fib(n: int) -> int:
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


@pytest.mark.parametrize("n", [2, 3, 5, 10, 20])
def test_example6_factorial_and_fibonacci(tmp_path: Path, n: int):
    mr_path = _compile_fixture_to_mr(tmp_path)

    vm = REPO_ROOT / "VM" / "maszyna-wirtualna"
    proc = subprocess.run(
        [str(vm), str(mr_path)],
        input=f"{n}\n".encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=2,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr.decode(errors="replace")

    nums = _extract_ints(proc.stdout)
    assert len(nums) >= 2
    fact_out, fib_out = nums[-2], nums[-1]
    assert fact_out == math.factorial(n)
    assert fib_out == _fib(n)
