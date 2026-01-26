from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(REPO_ROOT / "src"))

from peephole_optimizer import peephole_optimize


def test_rst_add_same_register_removed():
    code = ["RST b", "ADD b", "HALT"]
    assert peephole_optimize(code) == ["RST b", "HALT"]


def test_double_swap_removed():
    code = ["SWP c", "SWP c", "HALT"]
    assert peephole_optimize(code) == ["HALT"]


def test_load_store_same_cell_removed_when_a_dead():
    code = ["LOAD 1", "STORE 1", "RST a", "HALT"]
    assert peephole_optimize(code) == ["RST a", "HALT"]


def test_shift_pair_removed_when_register_dead():
    code = ["SHL b", "SHR b", "WRITE", "HALT"]
    assert peephole_optimize(code) == ["WRITE", "HALT"]


def test_jump_to_next_removed():
    code = ["JUMP 1", "HALT"]
    assert peephole_optimize(code) == ["HALT"]


def test_jump_target_remap_after_removal():
    code = ["JUMP 2", "SWP b", "SWP b", "HALT"]
    assert peephole_optimize(code) == ["HALT"]


def test_redundant_swap_after_copy_removed():
    code = ["RST a", "ADD b", "SWP b", "HALT"]
    assert peephole_optimize(code) == ["RST a", "ADD b", "HALT"]
