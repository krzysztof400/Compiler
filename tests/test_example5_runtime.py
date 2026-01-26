from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "example5.imp"

from tests.helpers import compile_fixture_to_mr_path, extract_ints, record_koszt


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
def test_example5_powmod(tmp_path: Path, a: int, b: int, c: int, request):
    mr_path = compile_fixture_to_mr_path(fixture_path=FIXTURE, tmp_path=tmp_path)

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
    record_koszt(request, proc.stdout, proc.stderr)

    nums = extract_ints(proc.stdout)
    assert len(nums) >= 1
    assert nums[-1] == pow(a, b, c)

