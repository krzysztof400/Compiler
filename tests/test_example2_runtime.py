from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "example2.imp"

from tests.helpers import compile_fixture_to_mr_path, extract_ints


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
def test_example2_nested_procs_swap_even_times(tmp_path: Path, a: int, b: int):
    """example2 applies nested procedures that repeatedly swap (a,b).

    pd() calls pa() 2^4 * 4 = 16 times total, so (a,b) should end up swapped
    compared to the input.
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

    nums = extract_ints(proc.stdout)
    assert len(nums) >= 2
    out_a, out_b = nums[-2], nums[-1]
    assert (out_a, out_b) == (b, a)
