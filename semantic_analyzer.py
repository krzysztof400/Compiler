from schemas import VariableSymbol, ArraySymbol, ProcedureSymbol

class SemanticAnalyzer:
    def __init__(self):
        self.scopes = {}
        self.current_scope_name = "global"
        self.memory_counter = 0
        
        self.scopes["global"] = {}
        self.procedures = {}

    def enter_scope(self, name):
        self.current_scope_name = name
        if name not in self.scopes:
            self.scopes[name] = {}

    def exit_scope(self):
        self.current_scope_name = "global"

    def declare_variable(self, name, is_array=False, range_start=0, range_end=0):
        current_scope = self.scopes[self.current_scope_name]
        if name in current_scope:
            raise Exception(f"Error: Variable '{name}' already declared in scope '{self.current_scope_name}'")

        if is_array:
            if range_start > range_end:
                raise Exception(f"Error: Invalid array range [{range_start}:{range_end}] for '{name}'")
            
            size = range_end - range_start + 1
            symbol = ArraySymbol(name, self.current_scope_name, self.memory_counter, range_start, range_end)
            
            self.memory_counter += size 
        else:
            symbol = VariableSymbol(name, self.current_scope_name, self.memory_counter)
            
            self.memory_counter += 1

        current_scope[name] = symbol
        return symbol

    def analyze(self, ast):
        _, procedures, main = ast
        
        for proc in procedures:
            self.visit_procedure(proc)
            
        self.visit_main(main)
        
        print(f"Analysis Complete. Total Memory Used: {self.memory_counter} cells.")

    def visit_procedure(self, node):
        proc_name = node[1]
        args = node[2]
        declarations = node[3]
        
        if proc_name in self.procedures:
            raise Exception(f"Error: Procedure '{proc_name}' already defined.")
        
        self.procedures[proc_name] = ProcedureSymbol(proc_name, args)
        self.enter_scope(proc_name)

        for arg in args:
            arg_type = arg[0]
            arg_name = arg[1]

            sym = self.declare_variable(arg_name) 
            sym.is_param = True
            sym.is_reference = True
            
            if "ARRAY" in arg_type:
                 sym.__class__ = ArraySymbol

        for decl in declarations:
            if decl[0] == 'VAR':
                self.declare_variable(decl[1])
            elif decl[0] == 'ARRAY':
                self.declare_variable(decl[1], is_array=True, range_start=decl[2], range_end=decl[3])
        
        self.exit_scope()

    def visit_main(self, node):
        self.enter_scope("global")
        
        declarations = node[1]
        for decl in declarations:
            if decl[0] == 'VAR':
                self.declare_variable(decl[1])
            elif decl[0] == 'ARRAY':
                self.declare_variable(decl[1], is_array=True, range_start=decl[2], range_end=decl[3])

        self.exit_scope()