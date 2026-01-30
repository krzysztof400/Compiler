# Imperative Language Compiler

## Project Description
This project is a compiler for a simple imperative programming language. The compiler translates source code written in a defined complete high-level language (supporting procedures, FOR/WHILE/REPEAT loops, conditional statements, and arrays) into assembly code for a specific Virtual Machine (VM).

Specifacation of language can be found in [language_spec](language_spec.md)
Specification of VM can be found in [vm_spec](vm_spec.md)

## Implementation Details
The compiler operates in several phases:
### 1. Lexical Analysis (Lexer): Source code is divided into tokens (keywords, identifiers, numbers).
### 2. Syntax Analysis (Parser): Tokens are matched against grammar rules to create an instruction structure or tree. Structural correctness is verified at this stage.
### 3. Abstract Syntax Trees:
- Variable scopes and type correctness are checked.
- Assembly code for the register machine is generated.
- Complex mathematical operations (multiplication/division) are expanded into bitwise algorithms (using SHL, SHR shifts) to ensure logarithmic complexity.
### 4. Code Generation: The final assembly code is produced, ready for execution on the target VM.
Used optimalisations:
- Constant folding
- Strength reduction
- Peephole optimizations
- Detection of specific patterns (e.g., increment/decrement, swap, power of two operations)
- In general, when writing I tried to reduce usage of high cost operations sch as LOAD/SAVE.


## Building and running
1. Compile the VM
```bash
cd vm
make
```

2. Install development dependencies
- python
- uv (https://pypi.org/project/uv/)

3. Run the compiler on an example program
```bash
uv run python compiler.py examples/programs/factorial.imp -o output.asm
```


### Tests

This repo uses **pytest**.

- Prefer running tests via `uv` so you use the pinned dev dependencies.

```bash
uv run pytest
```

Test inputs live in `tests/fixtures/` and `examples/programs/`.

Tests measure both correctness (by running the compiled code on the VM and checking output) and efficiency (by measuring the cost of generated assembly code).

### Efficiency measurements
Efficiency tests are located in `tests/efficency.md`. They track the cost of generated assembly code over time as optimizations are implemented. Each section documents the total cost after specific optimizations, allowing for comparison and verification of improvements.
