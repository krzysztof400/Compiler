from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
from tests.helpers import compile_source_to_mr, extract_ints


@pytest.fixture
def compiled_program(tmp_path: Path):
    prog = """
PROGRAM IS
    a,b,r,q,s,t
IN
  READ a;
  READ b;
  r:=a%b;
  q:=a/b;
  s:=a+b;
  t:=a-b;
  WRITE r;
  WRITE q;
  WRITE s;
  WRITE t;
END
"""
    mr = compile_source_to_mr(prog)
    mr_path = tmp_path / "prog.mr"
    mr_path.write_text(mr)
    return mr_path


def run_program(mr_path: Path, a: int, b: int):
    import subprocess

    vm = REPO_ROOT / "VM" / "maszyna-wirtualna"
    res = subprocess.run(
        [str(vm), str(mr_path)],
        input=f"{a}\n{b}\n".encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=1,
        check=False,
    )
    nums = extract_ints(res.stdout, allow_negative=False)
    assert len(nums) >= 4, (
        f"Expected at least 4 numeric outputs, got {len(nums)}. "
        f"Raw output: {res.stdout.decode(errors='replace')!r}"
    )
    return nums[-4], nums[-3], nums[-2], nums[-1]


@pytest.mark.parametrize("a,b", [(12, 8), (21, 14), (13, 5), (100, 3), (0, 1), (7, 7), (10, 0), (5, 2), (0, 0), (9, 4)])
def test_addition(compiled_program, a: int, b: int):
    _, _, s, _ = run_program(compiled_program, a, b)
    assert s == a + b, f"Sum mismatch: {s} != {a} + {b} (expected {a + b})"


@pytest.mark.parametrize("a,b", [(12, 8), (21, 14), (13, 5), (100, 3), (0, 1), (7, 7), (10, 0), (5, 2), (0, 0), (9, 4)])
def test_subtraction(compiled_program, a: int, b: int):
    _, _, _, t = run_program(compiled_program, a, b)
    assert t == max(a - b, 0), f"Difference mismatch: {t} != max({a} - {b}, 0) (expected {max(a - b, 0)})"


@pytest.mark.parametrize("a,b", [(12, 8), (21, 14), (13, 5), (100, 3), (0, 1), (7, 7), (10, 0), (5, 2), (0, 0), (9, 4)])
def test_division(compiled_program, a: int, b: int):
    _, q, _, _ = run_program(compiled_program, a, b)
    if b == 0:
        assert q == 0, f"Quotient mismatch when b=0: {q} != 0"
    else:
        assert q == a // b, f"Quotient mismatch: {q} != {a} // {b} (expected {a // b})"


@pytest.mark.parametrize("a,b", [(12, 8), (21, 14), (13, 5), (100, 3), (0, 1), (7, 7), (10, 0), (5, 2), (0, 0), (9, 4)])
def test_modulus(compiled_program, a: int, b: int):
    r, _, _, _ = run_program(compiled_program, a, b)
    if b == 0:
        assert r == 0, f"Remainder mismatch when b=0: {r} != 0"
    else:
        assert r == a % b, f"Remainder mismatch: {r} != {a} % {b} (expected {a % b})"