# Imperative Language Compiler

## Project Description
This project is a compiler for a simple imperative programming language. The compiler translates source code written in a defined high-level language (supporting procedures, FOR/WHILE/REPEAT loops, conditional statements, and arrays) into assembly code for a specific Virtual Machine (VM).

Specifacation of language can be found in [language_spec](language_spec.md)
Specification of VM can be found in [vm_spec](vm_spec.md)

## Implementation Details
The compiler operates in several phases:
### 1. Lexical Analysis (Lexer): Source code is divided into tokens (keywords, identifiers, numbers).
### 2. Syntax Analysis (Parser): Tokens are matched against grammar rules to create an instruction structure or tree. Structural correctness is verified at this stage.
### 3. Semantic Analysis and Code Generation:
- Variable scopes and type correctness are checked.
- Assembly code for the register machine is generated.
- Complex mathematical operations (multiplication/division) are expanded into bitwise algorithms (using SHL, SHR shifts) to ensure logarithmic complexity.

## Building and running


## Requirements
- Python 3.6+
- SLY library

## Project Structure

