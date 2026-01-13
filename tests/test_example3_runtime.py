from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "example3.imp"

from tests.helpers import compile_fixture_to_mr_path, extract_ints


@pytest.mark.parametrize("a", [1, 2, 5, 10, 26])
def test_example3_outputs_fibonacci_26_in_straight_line_code(tmp_path: Path, a: int):
    """example3 computes Fibonacci numbers by explicitly unrolling additions.

    For input 'a', it builds the sequence up to F(26) and writes it.
    When a==1, it should match the reference comment: 121393.
    """

    mr_path = compile_fixture_to_mr_path(fixture_path=FIXTURE, tmp_path=tmp_path)

    vm = REPO_ROOT / "VM" / "maszyna-wirtualna"
    proc = subprocess.run(
        [str(vm), str(mr_path)],
        input=f"{a}\n".encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=2,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr.decode(errors="replace")

    nums = extract_ints(proc.stdout)
    assert len(nums) >= 1
    assert nums[-1] == 121393 * a
