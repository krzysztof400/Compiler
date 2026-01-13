from __future__ import annotations

import math
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "example6.imp"

from tests.helpers import compile_fixture_to_mr_path, extract_ints


def _fib(n: int) -> int:
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


@pytest.mark.parametrize("n", [2, 3, 5, 10, 20])
def test_example6_factorial_and_fibonacci(tmp_path: Path, n: int):
    mr_path = compile_fixture_to_mr_path(fixture_path=FIXTURE, tmp_path=tmp_path)

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

    nums = extract_ints(proc.stdout)
    assert len(nums) >= 2
    fact_out, fib_out = nums[-2], nums[-1]
    assert fact_out == math.factorial(n)
    assert fib_out == _fib(n)
