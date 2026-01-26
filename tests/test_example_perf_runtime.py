from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tests.helpers import compile_fixture_to_mr_path, extract_ints, record_koszt

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures"


@pytest.mark.parametrize(
    "fixture_name,a,b,expected",
    [
        ("perf_mul.imp", 123456, 789012, 123456 * 789012),
        ("perf_mul.imp", 99991, 99991, 99991 * 99991),
    ],
)
def test_perf_mul_runtime(tmp_path: Path, fixture_name: str, a: int, b: int, expected: int, request):
    mr_path = compile_fixture_to_mr_path(
        fixture_path=FIXTURES / fixture_name,
        tmp_path=tmp_path,
        out_name=f"{fixture_name}.mr",
    )

    vm = REPO_ROOT / "VM" / "maszyna-wirtualna"
    proc = subprocess.run(
        [str(vm), str(mr_path)],
        input=f"{a}\n{b}\n".encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=1,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr.decode(errors="replace")
    record_koszt(request, proc.stdout, proc.stderr)

    nums = extract_ints(proc.stdout, allow_negative=False)
    assert nums, f"No numeric output for {fixture_name}: {proc.stdout.decode(errors='replace')!r}"
    assert nums[-1] == expected


@pytest.mark.parametrize(
    "a,b,expected_q,expected_r",
    [
        (987654321, 12345, 987654321 // 12345, 987654321 % 12345),
        (123456789012, 97, 123456789012 // 97, 123456789012 % 97),
    ],
)
def test_perf_div_runtime(tmp_path: Path, a: int, b: int, expected_q: int, expected_r: int, request):
    mr_path = compile_fixture_to_mr_path(
        fixture_path=FIXTURES / "perf_div.imp",
        tmp_path=tmp_path,
        out_name="perf_div.mr",
    )

    vm = REPO_ROOT / "VM" / "maszyna-wirtualna"
    proc = subprocess.run(
        [str(vm), str(mr_path)],
        input=f"{a}\n{b}\n".encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=1,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr.decode(errors="replace")
    record_koszt(request, proc.stdout, proc.stderr)

    nums = extract_ints(proc.stdout, allow_negative=False)
    assert len(nums) >= 2, f"Expected quotient+remainder, got {nums}"
    assert nums[-2] == expected_q
    assert nums[-1] == expected_r
