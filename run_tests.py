#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path


def iter_inputs(paths: list[str]) -> list[Path]:
    out: list[Path] = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            out.extend(sorted(path.glob("*.imp")))
        else:
            out.append(path)
    # keep only existing .imp files
    out = [p for p in out if p.exists() and p.suffix == ".imp"]
    return sorted(dict.fromkeys(out))  # de-dup, preserve order


def run_one(inp: Path, outdir: Path, uv: bool) -> int:
    outdir.mkdir(parents=True, exist_ok=True)
    outpath = outdir / f"{inp.stem}.out"

    cmd = (["uv", "run", "python", "./src/compiler.py"] if uv else [sys.executable, "./src/compiler.py"])
    cmd += [str(inp), str(outpath)]

    print(f"\n=== {inp} ===")
    print("+ " + " ".join(cmd))

    proc = subprocess.run(cmd, text=True, capture_output=True)

    if proc.stdout.strip():
        print("--- stdout ---")
        print(proc.stdout.rstrip())

    if proc.stderr.strip():
        print("--- stderr ---")
        print(proc.stderr.rstrip())

    print(f"exit code: {proc.returncode}")
    print(f"output file: {outpath}")
    return proc.returncode


def main() -> int:
    ap = argparse.ArgumentParser(description="Run compiler.py on all .imp files in given paths.")
    ap.add_argument(
        "paths",
        nargs="*",
        default=["tests", "programs_examples"],
        help="Files or directories to scan for .imp (default: tests programs_examples)",
    )
    ap.add_argument(
        "-o",
        "--outdir",
        default="output",
        help="Directory to write compiler outputs (default: output/)",
    )
    ap.add_argument(
        "--no-uv",
        action="store_true",
        help="Run with system python instead of `uv run python`",
    )
    args = ap.parse_args()

    inputs = iter_inputs(args.paths)
    if not inputs:
        print("No .imp files found in: " + ", ".join(args.paths), file=sys.stderr)
        return 2

    outdir = Path(args.outdir)
    failed = 0
    for inp in inputs:
        rc = run_one(inp, outdir, uv=not args.no_uv)
        if rc != 0:
            failed += 1

    print(f"\nDone. Total: {len(inputs)}, Failed: {failed}, Passed: {len(inputs) - failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())