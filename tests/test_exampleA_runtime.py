from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "exampleA.imp"

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

    mr_path = tmp_path / "exampleA.mr"
    mr_path.write_text("\n".join(mr_lines) + "\n")
    return mr_path


def _extract_ints(stdout: bytes) -> list[int]:
    out = stdout.decode(errors="replace")
    return [int(tok) for tok in out.replace("?", " ").replace(">", " ").split() if tok.lstrip("-").isdigit()]


def test_exampleA_array_indexing_and_arithmetic(tmp_path: Path):
    """exampleA builds arrays ta,tb then uses them to fill tc and prints tc[0..24]."""

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

    # Recompute expected output from the program semantics.
    n = 24
    tc0 = n
    tcn = n - tc0
    j = tc0 + 1
    ta = [0] * (n + 1)
    tb = [0] * (n + 1)
    tc = [0] * (n + 1)
    tc[0] = tc0
    tc[n] = tcn

    for i in range(tc0, tcn - 1, -1):
        ta[i] = i + 1
        tb[i] = j - i

    j = tcn
    for i in range(tcn, tc0 + 1):
        tc[i] = ta[i] * tb[i]

    expected = tc

    assert len(nums) >= n + 1
    assert nums[-(n + 1) :] == expected
