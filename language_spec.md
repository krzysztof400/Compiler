# Language Specification: Simple Imperative Language

## 1. General Characteristics
* **Arithmetic:** Operations are performed on natural numbers.
    * The result of subtracting a larger number from a smaller one is `0`.
    * Division by zero yields a result of `0` and a remainder of `0`.
* **Case Sensitivity:** Lowercase and uppercase letters are distinguished.
* **Comments:** Start with `#` and extend to the end of the line.
* **Numbers:**
    * Natural numbers in decimal format (`num`).
    * Constants in source code are limited to 64-bit integers, but the VM has no size limit (calculations can generate arbitrary natural numbers).
* **Identifiers:** Described by the regular expression `[_a-z]+` (`pidentifier`).

## 2. Data Types and Variables
* **Arrays:**
    * Declaration syntax: `tab[10:30]` declares an array indexed from 10 to 30 (size 21).
    * Access syntax: `tab[i]` refers to the i-th element.
    * Error: Declaring a range where the first number is greater than the second is an error.
* **Variables:** Can be simple identifiers or array elements.

## 3. Procedures
* **Recursion:** Procedures **cannot** contain recursive calls.
* **Parameters:**
    * Passed by reference (IN-OUT default mode).
    * Array names in formal parameters must be preceded by `T`.
    * `I` prefix: Variable is treated as a **constant** (read-only). It cannot be modified or passed to sub-procedures except in positions also marked with `I`.
    * `O` prefix: Variable has an **undefined value** initially (write-only). It cannot be read before assignment and cannot be passed to sub-procedures in positions marked with `I`.
* **Scope:** Variables used in a procedure must be formal parameters or declared locally.
* **Calls:** Procedures can only call previously defined procedures. Arguments can be local variables or parameters of the calling procedure.

## 4. Control Structures
* **FOR Loop:**
    * Iterator is local.
    * Ranges: `FROM value TO value` (increment +1) or `FROM value DOWNTO value` (decrement -1).
    * Iteration Count: Calculated once at the start. Changing loop bounds during execution does not affect the number of iterations.
    * Iterator Modification: The iterator cannot be modified inside the loop (compiler error).
* **REPEAT-UNTIL:** Executes at least once. Ends when the condition after `UNTIL` is met.
* **WHILE:** Standard execution while the condition is true.
* **IF-THEN-ELSE:** Standard conditional execution.

## 5. Input/Output
* **READ:** Reads a value into a variable.
* **WRITE:** Prints the value of a variable or number.

## 6. Optimization Requirements
* The target code should be as short as possible and execute as fast as possible.
* **Multiplication and Division:** Must be performed in logarithmic time relative to the value of the arguments (cannot be simple addition/subtraction loops).

## 7. Grammar (BNF Reconstruction)

**Program Structure:**
```text
program_all -> procedures main

procedures  -> procedures PROCEDURE proc_head IS declarations IN commands END
            | procedures PROCEDURE proc_head IS IN commands END
            | (empty)

main        -> PROGRAM IS declarations IN commands END
            | PROGRAM IS IN commands END

commands    -> commands command
            | command

command     -> identifier := expression;
            | IF condition THEN commands ELSE commands ENDIF
            | IF condition THEN commands ENDIF
            | WHILE condition DO commands ENDWHILE
            | REPEAT commands UNTIL condition;
            | FOR pidentifier FROM value TO value DO commands ENDFOR
            | FOR pidentifier FROM value DOWNTO value DO commands ENDFOR
            | proc_call;
            | READ identifier;
            | WRITE value;

proc_head   -> pidentifier ( args_decl )

proc_call   -> pidentifier ( args )

args_decl   -> args_decl, pidentifier
            | args_decl, T pidentifier
            | pidentifier
            | T pidentifier
            | args_decl, I pidentifier   (Const)
            | args_decl, O pidentifier   (Uninitialized)

args        -> args, pidentifier
            | pidentifier

declarations -> declarations, pidentifier
             | declarations, pidentifier [num:num]
             | pidentifier
             | pidentifier [num:num]
            
expression  -> value + value
            | value - value
            | value * value
            | value / value
            | value % value

condition   -> value = value
            | value != value
            | value > value
            | value < value
            | value >= value
            | value <= value

value       -> num
            | identifier

identifier  -> pidentifier
            | pidentifier [ pidentifier ]
            | pidentifier [ num ]