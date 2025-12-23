# schemas.py

class Symbol:
    def __init__(self, name, scope_level):
        self.name = name
        self.scope_level = scope_level

class VariableSymbol(Symbol):
    def __init__(self, name, scope_level, mem_offset):
        super().__init__(name, scope_level)
        self.mem_offset = mem_offset
        self.is_array = False       # <--- Crucial fix
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
        self.is_array = True        # <--- Crucial fix
        self.is_param = False
        self.is_reference = False

class ProcedureSymbol(Symbol):
    def __init__(self, name, args):
        super().__init__(name, 'global')
        self.args = args