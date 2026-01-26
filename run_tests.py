#!/usr/bin/env python3
"""Compatibility test runner.

This repository uses pytest.

Why keep this file?
- It preserves the old entrypoint (`python run_tests.py`) for convenience.
- It delegates to pytest so there's a single source of truth for test behavior.

Tip (recommended): run via uv so you always use the pinned dev dependencies:
- `uv run pytest`
- `uv run python run_tests.py`
"""

from __future__ import annotations

import sys


def main() -> int:
    try:
        import pytest  # type: ignore
    except Exception as e:  # pragma: no cover
        print(
            "pytest is not available in the current environment.\n"
            "Install dev dependencies (e.g. via uv/pip) and try again.\n"
            f"Import error: {e}",
            file=sys.stderr,
        )
        return 2

    # Forward any args to pytest.
    return pytest.main(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())