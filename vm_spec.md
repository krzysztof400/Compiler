# Virtual Machine Specification

## 1. Architecture
* **Registers:** 8 registers named $r_a, r_b, r_c, r_d, r_e, r_f, r_g, r_h$.
* **Instruction Counter:** $k$ (initialized to 0).
* **Memory:** Infinite sequence of cells $p_i$ for $i=0, 1, 2, ...$ (technically $i \le 2^{62}$).
* **Data Type:** Natural numbers.
* **Initialization:** Initial content of registers and memory is undefined.
* **Errors:** Transitioning to a non-existent instruction or accessing a non-existent register is treated as an error.

## 2. Execution Cycle
* Instructions are implicitly numbered from 0.
* The machine executes the instruction at index $k$.
* Stops upon encountering the `HALT` instruction.
* **Optimization Requirement:** Multiplication and division operations in the generated code must be performed in logarithmic time relative to the size of the arguments.

## 3. Instruction Set
* $x$ denotes a register identifier ($x \in \{a, b, c, d, e, f, g, h\}$).
* $j$ denotes a jump target/memory address ($j \in \mathbb{N}$).
* Cost indicates the execution time penalty.

| Command | Interpretation | Cost |
| :--- | :--- | :--- |
| **READ** | Read a value into $r_a$; $k \leftarrow k+1$ | 100 |
| **WRITE** | Print the content of $r_a$; $k \leftarrow k+1$ | 100 |
| **LOAD** $j$ | $r_a \leftarrow p_j$; $k \leftarrow k+1$ | 50 |
| **STORE** $j$ | $p_j \leftarrow r_a$; $k \leftarrow k+1$ | 50 |
| **RLOAD** $x$ | $r_a \leftarrow p_{r_x}$; $k \leftarrow k+1$ (Indirect Load) | 50 |
| **RSTORE** $x$| $p_{r_x} \leftarrow r_a$; $k \leftarrow k+1$ (Indirect Store) | 50 |
| **ADD** $x$ | $r_a \leftarrow r_a + r_x$; $k \leftarrow k+1$ | 5 |
| **SUB** $x$ | $r_a \leftarrow \max\{r_a - r_x, 0\}$; $k \leftarrow k+1$ | 5 |
| **SWP** $x$ | Swap $r_a \leftrightarrow r_x$; $k \leftarrow k+1$ | 5 |
| **RST** $x$ | $r_x \leftarrow 0$; $k \leftarrow k+1$ | 1 |
| **INC** $x$ | $r_x \leftarrow r_x + 1$; $k \leftarrow k+1$ | 1 |
| **DEC** $x$ | $r_x \leftarrow \max\{r_x - 1, 0\}$; $k \leftarrow k+1$ | 1 |
| **SHL** $x$ | $r_x \leftarrow 2 * r_x$; $k \leftarrow k+1$ (Shift Left) | 1 |
| **SHR** $x$ | $r_x \leftarrow \lfloor r_x / 2 \rfloor$; $k \leftarrow k+1$ (Shift Right) | 1 |
| **JUMP** $j$ | $k \leftarrow j$ | 1 |
| **JPOS** $j$ | If $r_a > 0$ then $k \leftarrow j$, else $k \leftarrow k+1$ | 1 |
| **JZERO** $j$ | If $r_a = 0$ then $k \leftarrow j$, else $k \leftarrow k+1$ | 1 |
| **CALL** $j$ | $r_a \leftarrow k+1$; $k \leftarrow j$ | 1 |
| **RTRN** | $k \leftarrow r_a$ | 1 |
| **HALT** | Stop program | 0 |

## 4. Syntax & Format
* **Comments:** Use `#` for comments extending to the end of the line.
* **Whitespace:** Ignored.
* **Format:** `INSTRUCTION [operand]` (e.g., `STORE 5`, `ADD b`).