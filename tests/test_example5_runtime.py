from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "example5.imp"

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

    mr_path = tmp_path / "example5.mr"
    mr_path.write_text("\n".join(mr_lines) + "\n")
    return mr_path


def _extract_ints(stdout: bytes) -> list[int]:
    out = stdout.decode(errors="replace")
    return [int(tok) for tok in out.replace("?", " ").replace(">", " ").split() if tok.lstrip("-").isdigit()]


@pytest.mark.parametrize(
    "a,b,c",
    [
        (2, 10, 7),
        (1234567890, 1234567890987654321, 987654321),
        (5, 0, 13),
        (0, 5, 13),
        (17, 1, 17),
    ],
)
def test_example5_powmod(tmp_path: Path, a: int, b: int, c: int):
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
    assert len(nums) >= 1
    assert nums[-1] == pow(a, b, c)

