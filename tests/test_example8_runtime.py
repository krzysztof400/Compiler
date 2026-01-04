from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "example8.imp"

# Compiler entrypoint uses flat imports
sys.path.append(str(REPO_ROOT / "src"))

from my_lexer import MyLexer  # noqa: E402
from my_parser import MyParser  # noqa: E402
from semantic_analyzer import SemanticAnalyzer  # noqa: E402
from code_generator import CodeGenerator  # noqa: E402


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

    mr_path = tmp_path / "example8.mr"
    mr_path.write_text("\n".join(mr_lines) + "\n")
    return mr_path


def _extract_ints(stdout: bytes) -> list[int]:
    out = stdout.decode(errors="replace")
    return [int(tok) for tok in out.replace("?", " ").replace(">", " ").split() if tok.lstrip("-").isdigit()]


def _shuffle(n: int) -> list[int]:
    # Must match shuffle() procedure in fixture.
    q = 5
    w = 1
    t = [None] * (n + 1)
    for i in range(1, n + 1):
        w = w * q
        w = w % n
        t[i] = w
    t[n] = 0
    return t[1:]


def test_example8_shuffle_and_sort(tmp_path: Path):
    """example8 prints the shuffled sequence, a sentinel, then the sorted sequence."""

    mr_path = _compile_fixture_to_mr(tmp_path)

    vm = REPO_ROOT / "VM" / "maszyna-wirtualna"
    proc = subprocess.run(
        [str(vm), str(mr_path)],
        input=b"",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=2,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr.decode(errors="replace")
    nums = _extract_ints(proc.stdout)

    n = 23
    expected_shuffled = _shuffle(n)
    # Output: n shuffled numbers, then sentinel 1234567890, then n sorted numbers.
    assert len(nums) >= 2 * n + 1
    shuffled_out = nums[:n]
    sentinel = nums[n]
    sorted_out = nums[n + 1 : n + 1 + n]

    assert shuffled_out == expected_shuffled
    assert sentinel == 1234567890
    assert sorted_out == sorted(expected_shuffled)
