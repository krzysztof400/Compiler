class Symbol:
    def __init__(self, name, scope_level):
        self.name = name
        self.scope_level = scope_level

class VariableSymbol(Symbol):
    def __init__(self, name, scope_level, mem_offset, is_initialized=False):
        super().__init__(name, scope_level)
        self.mem_offset = mem_offset
        self.is_initialized = is_initialized
        self.is_iterator = False
        self.is_param = False
        self.is_reference = False

class ArraySymbol(Symbol):
    def __init__(self, name, scope_level, mem_offset, start_idx, end_idx):
        super().__init__(name, scope_level)
        self.mem_offset = mem_offset
        self.start_idx = start_idx
        self.end_idx = end_idx
        self.is_param = False
        self.is_reference = False

class ProcedureSymbol(Symbol):
    def __init__(self, name, args):
        super().__init__(name, 'global')
        self.args = args