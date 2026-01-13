from __future__ import annotations

import math
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "example9.imp"

from tests.helpers import compile_fixture_to_mr_path, extract_ints


@pytest.mark.parametrize(
    "n,k",
    [
        (5, 2),
        (6, 3),
        (20, 9),
        (10, 0),
        (10, 10),
    ],
)
def test_example9_binomial_coefficient_array_factorial(tmp_path: Path, n: int, k: int):
    mr_path = compile_fixture_to_mr_path(fixture_path=FIXTURE, tmp_path=tmp_path)

    vm = REPO_ROOT / "VM" / "maszyna-wirtualna"
    proc = subprocess.run(
        [str(vm), str(mr_path)],
        input=f"{n}\n{k}\n".encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=2,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr.decode(errors="replace")

    nums = extract_ints(proc.stdout)
    assert len(nums) >= 1
    assert nums[-1] == math.comb(n, k)
