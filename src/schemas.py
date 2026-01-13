"""Shared schema objects used across compiler stages.

This project relies on runtime mutation of symbol objects (e.g. flags like
`is_initialized`) and, importantly, the semantic analyzer currently *changes a
parameter symbol's class* via ``sym.__class__ = ArraySymbol``.

That means these symbol types must remain "classic" Python classes with
compatible `__dict__` layouts (avoid `@dataclass(slots=True)`), otherwise
`__class__` reassignment will fail.
"""


class Symbol:
    def __init__(self, name, scope_level):
        self.name = name
        self.scope_level = scope_level


class VariableSymbol(Symbol):
    def __init__(self, name, scope_level, mem_offset):
        super().__init__(name, scope_level)
        self.mem_offset = mem_offset

        self.is_array = False
        self.is_param = False
        self.is_reference = False
        self.is_const = False
        self.is_initialized = False
        self.is_iterator = False


class ArraySymbol(Symbol):
    def __init__(self, name, scope_level, mem_offset, start_idx=0, end_idx=0):
        super().__init__(name, scope_level)
        self.mem_offset = mem_offset
        self.start_idx = start_idx
        self.end_idx = end_idx

        self.is_array = True
        self.is_param = False
        self.is_reference = False

    @property
    def size(self):
        return self.end_idx - self.start_idx + 1


class ProcedureSymbol(Symbol):
    def __init__(self, name, args):
        super().__init__(name, 'global')
        self.args = args

# Structured user-facing errors


class SourceLocation:
    def __init__(self, line: int, column: int | None = None):
        self.line = int(line)
        self.column = None if column is None else int(column)

    def __str__(self) -> str:
        if self.column is None:
            return f"line {self.line}"
        return f"line {self.line}, col {self.column}"


class CompilationError(Exception):
    def __init__(
        self,
        kind: str,
        message: str,
        location: SourceLocation | None = None,
    ):
        super().__init__(message)
        self.kind = kind
        self.message = message
        self.location = location

    def __str__(self) -> str:
        if self.location is None:
            return f"{self.kind}: {self.message}"
        return f"{self.location}: {self.kind}: {self.message}"

class LexicalError(CompilationError):
    def __init__(self, message: str, location: SourceLocation | None = None):
        super().__init__("LexicalError", message, location)


class SyntaxError(CompilationError):
    def __init__(self, message: str, location: SourceLocation | None = None):
        super().__init__("SyntaxError", message, location)


class SemanticError(CompilationError):
    def __init__(self, message: str, location: SourceLocation | None = None):
        super().__init__("SemanticError", message, location)