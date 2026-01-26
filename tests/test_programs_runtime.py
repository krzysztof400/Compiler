from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tests.helpers import compile_fixture_to_mr_path, extract_ints, record_koszt

REPO_ROOT = Path(__file__).resolve().parents[1]
PROGRAM_DIR = REPO_ROOT / "examples" / "programs"

PROGRAM0 = PROGRAM_DIR / "program0.imp"
PROGRAM1 = PROGRAM_DIR / "program1.imp"
PROGRAM2 = PROGRAM_DIR / "program2.imp"
PROGRAM3 = PROGRAM_DIR / "program3.imp"

VM = REPO_ROOT / "VM" / "maszyna-wirtualna"


def _run_vm(mr_path: Path, *, input_data: str = "") -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [str(VM), str(mr_path)],
        input=input_data.encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=2,
        check=False,
    )


def _bits_lsb(n: int) -> list[int]:
    if n == 0:
        return [0]
    bits: list[int] = []
    while True:
        bits.append(n % 2)
        n //= 2
        if n == 0:
            break
    return bits


@pytest.mark.parametrize("n", [0, 1, 2, 6, 13, 255])
def test_program0_outputs_binary_lsb_first(tmp_path: Path, n: int, request):
    mr_path = compile_fixture_to_mr_path(fixture_path=PROGRAM0, tmp_path=tmp_path)

    proc = _run_vm(mr_path, input_data=f"{n}\n")
    assert proc.returncode == 0, proc.stderr.decode(errors="replace")
    record_koszt(request, proc.stdout, proc.stderr)

    nums = extract_ints(proc.stdout, allow_negative=False)
    assert nums == _bits_lsb(n)


@pytest.mark.parametrize(
    "a,b,c,d",
    [
        (12, 18, 20, 30),
        (21, 14, 25, 10),
        (13, 5, 7, 11),
        (48, 64, 81, 108),
    ],
)
def test_program1_gcd_of_two_pairs(tmp_path: Path, a: int, b: int, c: int, d: int, request):
    mr_path = compile_fixture_to_mr_path(fixture_path=PROGRAM1, tmp_path=tmp_path)

    proc = _run_vm(mr_path, input_data=f"{a}\n{b}\n{c}\n{d}\n")
    assert proc.returncode == 0, proc.stderr.decode(errors="replace")
    record_koszt(request, proc.stdout, proc.stderr)

    nums = extract_ints(proc.stdout, allow_negative=False)
    assert nums, "Expected output from gcd program"

    def _gcd(x: int, y: int) -> int:
        while y:
            x, y = y, x % y
        return x

    expected = _gcd(_gcd(a, b), _gcd(c, d))
    assert nums[-1] == expected


def _primes_up_to(limit: int) -> list[int]:
    sieve = [True] * (limit + 1)
    sieve[0:2] = [False, False]
    for p in range(2, int(limit**0.5) + 1):
        if sieve[p]:
            for multiple in range(p * p, limit + 1, p):
                sieve[multiple] = False
    return [p for p in range(2, limit + 1) if sieve[p]]


def test_program2_outputs_primes_desc(tmp_path: Path, request):
    mr_path = compile_fixture_to_mr_path(fixture_path=PROGRAM2, tmp_path=tmp_path)

    proc = _run_vm(mr_path)
    assert proc.returncode == 0, proc.stderr.decode(errors="replace")
    record_koszt(request, proc.stdout, proc.stderr)

    nums = extract_ints(proc.stdout, allow_negative=False)
    expected = list(reversed(_primes_up_to(100)))
    assert nums == expected


def _factor_pairs(n: int) -> list[int]:
    if n <= 1:
        return []
    pairs: list[int] = []
    divisor = 2
    while divisor * divisor <= n:
        if n % divisor == 0:
            count = 0
            while n % divisor == 0:
                n //= divisor
                count += 1
            pairs.extend([divisor, count])
        divisor += 1
    if n != 1:
        pairs.extend([n, 1])
    return pairs


@pytest.mark.parametrize("n", [1, 2, 60, 72, 97, 100])
def test_program3_prime_factorization(tmp_path: Path, n: int, request):
    mr_path = compile_fixture_to_mr_path(fixture_path=PROGRAM3, tmp_path=tmp_path)

    proc = _run_vm(mr_path, input_data=f"{n}\n")
    assert proc.returncode == 0, proc.stderr.decode(errors="replace")
    record_koszt(request, proc.stdout, proc.stderr)

    nums = extract_ints(proc.stdout, allow_negative=False)
    assert nums == _factor_pairs(n)
