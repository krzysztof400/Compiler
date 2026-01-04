from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
COMPILER = REPO_ROOT / "src" / "compiler.py"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def _run_compiler(inp: Path, out_dir: Path) -> subprocess.CompletedProcess[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{inp.stem}.out"

    # Use the current interpreter so tests work in any venv/uv context.
    cmd = [sys.executable, str(COMPILER), str(inp), str(out_path)]
    return subprocess.run(cmd, text=True, capture_output=True)


def _fail_with_compiler_output(inp: Path, proc: subprocess.CompletedProcess[str], *, header: str) -> None:
    # Print compiler output so pytest shows it as captured output, rather than
    # embedding it into an AssertionError representation.
    if proc.stdout:
        print("\n--- compiler stdout ---\n" + proc.stdout.rstrip() + "\n")
    if proc.stderr:
        print("\n--- compiler stderr ---\n" + proc.stderr.rstrip() + "\n")

    pytest.fail(f"{header} (rc={proc.returncode})", pytrace=False)


def _imp_files(dir_path: Path) -> list[Path]:
    return sorted(p for p in dir_path.glob("*.imp") if p.is_file())


def _fixture_expectations() -> dict[str, int]:
        names = [p.name for p in _imp_files(FIXTURES_DIR)]
        expectations = {name: (1 if name.startswith("error_") else 0) for name in names}

        return expectations


@pytest.mark.parametrize(
    "inp",
    _imp_files(FIXTURES_DIR),
    ids=lambda p: p.name,
)
def test_tests_fixture_exit_codes(inp: Path, tmp_path: Path) -> None:
    """Run compiler on all fixtures in ./tests/fixtures.

    Convention used by this repo:
    - files whose name starts with 'error_' should fail (non-zero)
    - all other .imp files should compile successfully (zero)
    """

    proc = _run_compiler(inp, tmp_path / "output")

    expected_rc = _fixture_expectations()[inp.name]
    if expected_rc == 0:
        if proc.returncode != 0:
            _fail_with_compiler_output(inp, proc, header=f"Expected success for {inp.name}")
    else:
        if proc.returncode == 0:
            _fail_with_compiler_output(inp, proc, header=f"Expected compilation error for {inp.name}")


@pytest.mark.parametrize(
    "inp",
    _imp_files(REPO_ROOT / "examples" / "programs"),
    ids=lambda p: p.name,
)
def test_programs_examples_compile(inp: Path, tmp_path: Path) -> None:
    """Example programs in ./examples/programs should compile.

    If an example stops compiling, we want a *real failure* so it's visible in CI
    and locally.
    """

    proc = _run_compiler(inp, tmp_path / "output")
    if proc.returncode != 0:
        _fail_with_compiler_output(
            inp,
            proc,
            header=f"Example does not compile with current compiler: {inp.name}",
        )
