from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "example8.imp"

from tests.helpers import compile_fixture_to_mr_path, extract_ints


def _shuffle(n: int) -> list[int]:
    # Must match shuffle() procedure in fixture.
    q = 5
    w = 1
    t = [None] * (n + 1)
    for i in range(1, n + 1):
        w = w * q
        w = w % n
        t[i] = w
    t[n] = 0
    return t[1:]


def test_example8_shuffle_and_sort(tmp_path: Path):
    """example8 prints the shuffled sequence, a sentinel, then the sorted sequence."""

    mr_path = compile_fixture_to_mr_path(fixture_path=FIXTURE, tmp_path=tmp_path)

    vm = REPO_ROOT / "VM" / "maszyna-wirtualna"
    proc = subprocess.run(
        [str(vm), str(mr_path)],
        input=b"",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=2,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr.decode(errors="replace")
    nums = extract_ints(proc.stdout)

    n = 23
    expected_shuffled = _shuffle(n)
    # Output: n shuffled numbers, then sentinel 1234567890, then n sorted numbers.
    assert len(nums) >= 2 * n + 1
    shuffled_out = nums[:n]
    sentinel = nums[n]
    sorted_out = nums[n + 1 : n + 1 + n]

    assert shuffled_out == expected_shuffled
    assert sentinel == 1234567890
    assert sorted_out == sorted(expected_shuffled)
