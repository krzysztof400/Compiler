from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "myexample.imp"

from tests.helpers import compile_fixture_to_mr_path, extract_ints, record_koszt


def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


@pytest.mark.parametrize("n", [(8), (14), (5)])
def test_example1_terminates_and_outputs_gcd(tmp_path: Path, n: int, request):
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
    record_koszt(request, proc.stdout, proc.stderr)

    nums = extract_ints(proc.stdout, allow_negative=False)

    z = nums[-1]
    assert z == n
