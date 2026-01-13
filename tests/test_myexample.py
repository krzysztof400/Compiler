from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "myexample.imp"

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

    mr_path = tmp_path / "myexample.mr"
    mr_path.write_text("\n".join(mr_lines) + "\n")
    return mr_path


def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


@pytest.mark.parametrize("n", [(8), (14), (5)])
def test_example1_terminates_and_outputs_gcd(tmp_path: Path, n: int):
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

    out = proc.stdout.decode(errors="replace")
    nums = [int(tok) for tok in out.replace("?", " ").replace(">", " ").split() if tok.isdigit()]

    z = nums[-1]
    assert z == n
