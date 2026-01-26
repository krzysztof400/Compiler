from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tests.helpers import compile_fixture_to_mr_path, extract_ints, record_koszt

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "perf_pow_via_mul.imp"


@pytest.mark.parametrize(
    "base,exp,expected",
    [
        (2, 20, 2**20),
        (3, 12, 3**12),
    ],
)
def test_pow_via_mul_runtime(tmp_path: Path, base: int, exp: int, expected: int, request):
    mr_path = compile_fixture_to_mr_path(fixture_path=FIXTURE, tmp_path=tmp_path)

    vm = REPO_ROOT / "VM" / "maszyna-wirtualna"
    proc = subprocess.run(
        [str(vm), str(mr_path)],
        input=f"{base}\n{exp}\n".encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=1,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr.decode(errors="replace")
    record_koszt(request, proc.stdout, proc.stderr)

    nums = extract_ints(proc.stdout, allow_negative=False)
    assert nums, f"No numeric output: {proc.stdout.decode(errors='replace')!r}"
    assert nums[-1] == expected
