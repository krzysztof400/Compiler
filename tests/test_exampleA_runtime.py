from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "exampleA.imp"

from tests.helpers import compile_fixture_to_mr_path, extract_ints, record_koszt


def test_exampleA_array_indexing_and_arithmetic(tmp_path: Path, request):
    """exampleA builds arrays ta,tb then uses them to fill tc and prints tc[0..24]."""

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
    record_koszt(request, proc.stdout, proc.stderr)
    nums = extract_ints(proc.stdout)

    # Recompute expected output from the program semantics.
    n = 24
    tc0 = n
    tcn = n - tc0
    j = tc0 + 1
    ta = [0] * (n + 1)
    tb = [0] * (n + 1)
    tc = [0] * (n + 1)
    tc[0] = tc0
    tc[n] = tcn

    for i in range(tc0, tcn - 1, -1):
        ta[i] = i + 1
        tb[i] = j - i

    j = tcn
    for i in range(tcn, tc0 + 1):
        tc[i] = ta[i] * tb[i]

    expected = tc

    assert len(nums) >= n + 1
    assert nums[-(n + 1) :] == expected
