from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "example1.imp"

from tests.helpers import compile_fixture_to_mr_path, extract_ints


def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


@pytest.mark.parametrize("m,n", [(12, 8), (21, 14), (13, 5)])
def test_example1_terminates_and_outputs_gcd(tmp_path: Path, m: int, n: int):
    mr_path = compile_fixture_to_mr_path(fixture_path=FIXTURE, tmp_path=tmp_path)

    vm = REPO_ROOT / "VM" / "maszyna-wirtualna"
    proc = subprocess.run(
        [str(vm), str(mr_path)],
        input=f"{m}\n{n}\n".encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=2,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr.decode(errors="replace")

    nums = extract_ints(proc.stdout, allow_negative=False)
    assert len(nums) >= 3

    x, y, z = nums[-3], nums[-2], nums[-1]
    assert z == _gcd(m, n)
