from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass(frozen=True)
class Instruction:
    op: str
    arg: Optional[str]
    source_index: Optional[int]

    def to_text(self) -> str:
        if self.arg is None:
            return self.op
        return f"{self.op} {self.arg}"


JUMP_OPS = {"JUMP", "JZERO", "JPOS", "CALL"}
READS_A = {"WRITE", "STORE", "RSTORE", "ADD", "SUB", "SWP", "JPOS", "JZERO", "RTRN"}
WRITES_A = {"READ", "LOAD", "RLOAD", "ADD", "SUB", "SWP", "CALL", "RST"}


def parse_instructions(lines: Iterable[str]) -> list[Instruction]:
    instructions = []
    for idx, line in enumerate(lines):
        parts = line.strip().split()
        if not parts:
            continue
        op = parts[0]
        arg = parts[1] if len(parts) > 1 else None
        instructions.append(Instruction(op=op, arg=arg, source_index=idx))
    return instructions


def reg_reads(instr: Instruction) -> set[str]:
    reads: set[str] = set()
    if instr.op in READS_A:
        reads.add("a")
    if instr.op in {"RLOAD", "RSTORE", "ADD", "SUB", "SWP"} and instr.arg is not None:
        reads.add(instr.arg)
    if instr.op in {"INC", "DEC", "SHL", "SHR"} and instr.arg is not None:
        reads.add(instr.arg)
    return reads


def reg_writes(instr: Instruction) -> set[str]:
    writes: set[str] = set()
    if instr.op in WRITES_A:
        writes.add("a")
    if instr.op in {"SWP", "RST", "INC", "DEC", "SHL", "SHR"} and instr.arg is not None:
        writes.add(instr.arg)
    return writes


def peephole_pass(instructions: list[Instruction]) -> list[Instruction]:
    optimized: list[Instruction] = []
    i = 0
    while i < len(instructions):
        curr = instructions[i]
        nxt = instructions[i + 1] if i + 1 < len(instructions) else None
        nxt2 = instructions[i + 2] if i + 2 < len(instructions) else None

        if curr.op == "RST" and nxt and nxt.op == "ADD" and curr.arg == nxt.arg:
            optimized.append(curr)
            i += 2
            continue

        if curr.op == "SWP" and nxt and nxt.op == "SWP" and curr.arg == nxt.arg:
            i += 2
            continue

        if (
            curr.op == "RST"
            and curr.arg == "a"
            and nxt
            and nxt.op == "ADD"
            and nxt2
            and nxt2.op == "SWP"
            and nxt2.arg == nxt.arg
        ):
            optimized.extend([curr, nxt])
            i += 3
            continue

        if (
            curr.op == "LOAD"
            and curr.arg is not None
            and nxt
            and nxt.op == "STORE"
            and nxt.arg == curr.arg
        ):
            if i + 2 < len(instructions):
                following = instructions[i + 2]
                if "a" not in reg_reads(following) and "a" in reg_writes(following):
                    i += 2
                    continue

        if (
            curr.op == "SHL"
            and nxt
            and nxt.op == "SHR"
            and curr.arg == nxt.arg
        ):
            i += 2
            continue

        if curr.op == "JUMP" and curr.arg is not None:
            try:
                target = int(curr.arg)
            except ValueError:
                target = None
            if target is not None and target == i + 1:
                i += 1
                continue

        optimized.append(curr)
        i += 1

    return optimized


def build_old_to_new_map(old_len: int, new_instructions: list[Instruction]) -> list[int]:
    old_to_new: list[Optional[int]] = [None] * old_len
    for new_idx, instr in enumerate(new_instructions):
        if instr.source_index is not None:
            old_to_new[instr.source_index] = new_idx

    next_known: Optional[int] = None
    for idx in range(old_len - 1, -1, -1):
        if old_to_new[idx] is None:
            if next_known is None:
                old_to_new[idx] = len(new_instructions) - 1
            else:
                old_to_new[idx] = next_known
        else:
            next_known = old_to_new[idx]

    return [value if value is not None else 0 for value in old_to_new]


def remap_jump_targets(instructions: list[Instruction], old_to_new: list[int]) -> list[Instruction]:
    remapped: list[Instruction] = []
    for instr in instructions:
        if instr.op in JUMP_OPS and instr.arg is not None:
            try:
                target = int(instr.arg)
            except ValueError:
                remapped.append(instr)
                continue
            if 0 <= target < len(old_to_new):
                remapped.append(
                    Instruction(op=instr.op, arg=str(old_to_new[target]), source_index=instr.source_index)
                )
            else:
                remapped.append(instr)
        else:
            remapped.append(instr)
    return remapped


def normalize_sources(instructions: list[Instruction]) -> list[Instruction]:
    return [Instruction(op=instr.op, arg=instr.arg, source_index=index) for index, instr in enumerate(instructions)]


def peephole_optimize(lines: Iterable[str], max_iterations: int = 3) -> list[str]:
    instructions = parse_instructions(lines)
    for _ in range(max_iterations):
        normalized = normalize_sources(instructions)
        optimized = peephole_pass(normalized)
        old_to_new = build_old_to_new_map(len(normalized), optimized)
        remapped = remap_jump_targets(optimized, old_to_new)
        if [instr.to_text() for instr in remapped] == [instr.to_text() for instr in normalized]:
            instructions = remapped
            break
        instructions = remapped
    return [instr.to_text() for instr in instructions]
