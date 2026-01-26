from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "example2.imp"

from tests.helpers import compile_fixture_to_mr_path, extract_ints, record_koszt


@pytest.mark.parametrize(
    "a,b",
    [
        (0, 1),
        (1, 0),
        (12, 8),
        (123, 456),
        (46368, 28657),
    ],
)
def test_example2_nested_procs_swap_even_times(tmp_path: Path, a: int, b: int, request):
    """example2 applies nested procedures that repeatedly transform (a,b).

    pa(a,b) computes: a := a + b; b := a - b
    That is equivalent to (a,b) -> (a+b, a).

    pd() calls pa() 24 times total (2 * 3 * 4), so we simulate that here.
    """

    mr_path = compile_fixture_to_mr_path(fixture_path=FIXTURE, tmp_path=tmp_path)

    vm = REPO_ROOT / "VM" / "maszyna-wirtualna"
    proc = subprocess.run(
        [str(vm), str(mr_path)],
        input=f"{a}\n{b}\n".encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=2,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr.decode(errors="replace")
    record_koszt(request, proc.stdout, proc.stderr)

    nums = extract_ints(proc.stdout)
    assert len(nums) >= 2
    out_a, out_b = nums[-2], nums[-1]
    exp_a, exp_b = a, b
    for _ in range(24):
        exp_a, exp_b = exp_a + exp_b, exp_a
    assert (out_a, out_b) == (exp_a, exp_b)
