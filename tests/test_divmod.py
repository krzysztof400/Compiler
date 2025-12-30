import sys
from pathlib import Path

import pytest

# Ensure we can import the compiler entrypoint modules (they use flat imports)
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(REPO_ROOT / "src"))

from my_lexer import MyLexer  # noqa: E402
from my_parser import MyParser  # noqa: E402
from semantic_analyzer import SemanticAnalyzer  # noqa: E402
from code_generator import CodeGenerator  # noqa: E402


def _compile_to_mr(source: str) -> str:
    lexer = MyLexer()
    parser = MyParser()
    ast = parser.parse(lexer.tokenize(source))
    assert ast is not None

    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)

    gen = CodeGenerator(analyzer)
    code = gen.generate(ast)
    return "\n".join(code) + "\n"


def test_divmod_terminates_smoke(tmp_path: Path):
    """A small program that uses / and % in a loop should at least halt.

    This is a regression guard against div/mod codegen producing non-terminating code.
    """

    prog = """
PROGRAM IS
  a,b,r,q
IN
  a:=12;
  b:=8;
  r:=a%b;
  q:=a/b;
  WRITE r;
  WRITE q;
END
"""

    mr = _compile_to_mr(prog)
    mr_path = tmp_path / "prog.mr"
    mr_path.write_text(mr)

    # Run on the bundled VM with a short timeout.
    import subprocess

    vm = REPO_ROOT / "VM" / "maszyna-wirtualna"
    res = subprocess.run(
        [str(vm), str(mr_path)],
        input=b"",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=1,
        check=False,
    )

    assert res.returncode == 0, res.stderr.decode(errors="replace")
