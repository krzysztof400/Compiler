from schemas import VariableSymbol, ArraySymbol, ProcedureSymbol, SemanticError, SourceLocation

class SemanticAnalyzer:
    def _loc_from_node(self, node):
        """
        Best-effort location extraction from AST tuples.
        Parser attaches lineno as the last element for many nodes.
        """
        try:
            if isinstance(node, tuple) and len(node) >= 2 and isinstance(node[-1], int):
                return SourceLocation(node[-1])
        except Exception:
            pass
        return None
    def __init__(self):
        self.scopes = {}
        self.current_scope_name = "global"
        self.memory_counter = 0

        # Maps id(for_node) -> hidden limit VariableSymbol for FOR loops.
        self.for_limits = {}
        
        self.scopes["global"] = {}
        self.procedures = {}

        # Stores parameter cell offsets for each procedure for codegen.
        self.proc_param_cells = {}

    def enter_scope(self, name):
        self.current_scope_name = name
        if name not in self.scopes:
            self.scopes[name] = {}

    def exit_scope(self):
        self.current_scope_name = "global"

    def get_symbol(self, name, node=None):
        current_scope = self.scopes[self.current_scope_name]
        if name in current_scope:
            return current_scope[name]
        
        global_scope = self.scopes["global"]
        if name in global_scope:
            return global_scope[name]
        
        raise SemanticError(
            f"Variable '{name}' not declared in scope '{self.current_scope_name}' or global scope.",
            location=self._loc_from_node(node),
        )

    def declare_variable(self, name, is_array=False, range_start=0, range_end=0, node=None):
        current_scope = self.scopes[self.current_scope_name]
        if name in current_scope:
            raise SemanticError(
                f"Variable '{name}' already declared in scope '{self.current_scope_name}'",
                location=self._loc_from_node(node),
            )

        if is_array:
            if range_start > range_end:
                raise SemanticError(
                    f"Invalid array range [{range_start}:{range_end}] for '{name}'",
                    location=self._loc_from_node(node),
                )
            
            size = range_end - range_start + 1
            symbol = ArraySymbol(name, self.current_scope_name, self.memory_counter, range_start, range_end)
            
            self.memory_counter += size 
        else:
            symbol = VariableSymbol(name, self.current_scope_name, self.memory_counter)
            
            self.memory_counter += 1

        current_scope[name] = symbol
        return symbol

# --- COMMAND VISITOR ---

    def visit_commands(self, commands):
        for cmd in commands:
            self.visit_command(cmd)

    def visit_command(self, cmd):
        c_type = cmd[0]
        
        if c_type == 'ASSIGN':
            self.visit_assign(cmd)
        elif c_type == 'IF':
            self.visit_if(cmd)
        elif c_type == 'WHILE':
            self.visit_while(cmd)
        elif c_type == 'REPEAT':
            self.visit_repeat(cmd)
        elif c_type == 'FOR_TO' or c_type == 'FOR_DOWNTO':
            self.visit_for(cmd)
        elif c_type == 'PROC_CALL':
            self.visit_proc_call(cmd)
        elif c_type == 'READ':
            self.visit_read(cmd)
        elif c_type == 'WRITE':
            self.visit_write(cmd)

    def visit_assign(self, node):
        identifier_node = node[1]
        expression = node[2]
        
        target_sym = self.visit_identifier(identifier_node, is_write=True)
        
        if target_sym.is_const:
            raise SemanticError(
                f"Cannot modify constant or iterator '{target_sym.name}'",
                location=self._loc_from_node(node),
            )

        self.visit_expression(expression)
        
        if hasattr(target_sym, 'is_initialized'):
            target_sym.is_initialized = True

    def visit_read(self, node):
        target_sym = self.visit_identifier(node[1], is_write=True)
        if target_sym.is_const:
            raise SemanticError(
                f"Cannot READ into constant '{target_sym.name}'",
                location=self._loc_from_node(node),
            )
        target_sym.is_initialized = True

    def visit_write(self, node):
        val = node[1]
        if isinstance(val, tuple):
             self.visit_expression(val)

    def visit_if(self, node):
        self.visit_condition(node[1])
        self.visit_commands(node[2])
        # node shape:
        # - ('IF', cond, then_cmds, else_cmds, lineno)
        else_cmds = node[3] if len(node) >= 4 and isinstance(node[3], list) else []
        if else_cmds:
            self.visit_commands(else_cmds)

    def visit_while(self, node):
        self.visit_condition(node[1])
        self.visit_commands(node[2])

    def visit_repeat(self, node):
        self.visit_commands(node[1])
        self.visit_condition(node[2])

    def visit_for(self, node):
        iterator_name = node[1]
        val_start = node[2]
        val_end = node[3]
        commands = node[4]
        
        self.visit_value(val_start)
        self.visit_value(val_end)
        
        iter_sym = self.declare_variable(iterator_name)
        iter_sym.is_iterator = True
        iter_sym.is_const = True
        iter_sym.is_initialized = True

        # Spec compliance: iteration count is calculated once at loop entry.
        # We reserve a hidden scalar cell that will hold the evaluated end bound.
        limit_name = f"_limit_{iterator_name}_{id(node)}"
        limit_sym = self.declare_variable(limit_name)
        limit_sym.is_initialized = True

        # Expose the hidden variable to codegen via analyzer mapping.
        self.for_limits[id(node)] = limit_sym

        try:
            self.visit_commands(commands)
        finally:
            # Remove both symbols from current scope and roll back virtual memory.
            self.for_limits.pop(id(node), None)
            del self.scopes[self.current_scope_name][iterator_name]
            del self.scopes[self.current_scope_name][limit_name]
            self.memory_counter -= 2

    def visit_proc_call(self, node):
        pname = node[1]
        call_args = node[2]
        
        if pname not in self.procedures:
            raise SemanticError(
                f"Call to undefined procedure '{pname}'",
                location=self._loc_from_node(node),
            )
        
        proc_def = self.procedures[pname]
        def_args = proc_def.args
        
        if len(call_args) != len(def_args):
            raise SemanticError(
                f"Procedure '{pname}' expects {len(def_args)} arguments, got {len(call_args)}",
                location=self._loc_from_node(node),
            )

        for i, (call_arg_name, def_arg_tuple) in enumerate(zip(call_args, def_args)):
            def_type = def_arg_tuple[0]
            
            sym = self.get_symbol(call_arg_name)
            
            if def_type == 'ARG_ARRAY':
                if not sym.is_array:
                    raise SemanticError(
                        f"Argument {i+1} of '{pname}' expects an Array, got variable '{call_arg_name}'",
                        location=self._loc_from_node(node),
                    )
            else:
                if sym.is_array:
                    raise SemanticError(
                        f"Argument {i+1} of '{pname}' expects a Variable, got Array '{call_arg_name}'",
                        location=self._loc_from_node(node),
                    )

            if not sym.is_array and not sym.is_initialized:
                 if def_type != 'ARG_OUTPUT':
                     pass 

    # --- EXPRESSIONS & IDENTIFIERS ---

    def visit_expression(self, node):
        if isinstance(node, tuple):
            tag = node[0]
            if tag in ['ADD', 'SUB', 'MUL', 'DIV', 'MOD']:
                self.visit_expression(node[1])
                self.visit_expression(node[2])
            elif tag in ['PIDENTIFIER', 'PIDENTIFIER_WITH_PID', 'PIDENTIFIER_WITH_NUM']:
                sym = self.visit_identifier(node, is_write=False)
                if not sym.is_array and not sym.is_initialized:
                    raise SemanticError(
                        f"Usage of uninitialized variable '{sym.name}'",
                        location=self._loc_from_node(node),
                    )
            elif tag == 'NUMBER':
                pass

    def visit_condition(self, node):
        self.visit_expression(node[1])
        self.visit_expression(node[2])

    def visit_value(self, node):
        if isinstance(node, tuple) and node[0] != 'NUMBER':
             self.visit_expression(node)

    def visit_identifier(self, node, is_write=False, enforce_checks=True):
        tag = node[0]
        name = node[1]
        sym = self.get_symbol(name, node=node)
        
        if tag == 'PIDENTIFIER':
            if sym.is_array:
                 raise SemanticError(
                     f"Array '{name}' used without index",
                     location=self._loc_from_node(node),
                 )
        
        else:
            if not sym.is_array:
                raise SemanticError(
                    f"Variable '{name}' accessed as array",
                    location=self._loc_from_node(node),
                )
            
            if tag == 'PIDENTIFIER_WITH_PID':
                index_var_name = node[2]
                idx_sym = self.get_symbol(index_var_name, node=node)
                
                # === CHANGE START ===
                # Only check initialization if we are in the analysis phase
                if enforce_checks and not idx_sym.is_initialized:
                     raise SemanticError(
                         f"Array index '{index_var_name}' is uninitialized",
                         location=self._loc_from_node(node),
                     )
                # === CHANGE END ===
        
        return sym

    def analyze(self, ast):
        _, procedures, main = ast
        
        for proc in procedures:
            self.visit_procedure(proc)
            
        self.visit_main(main)
        
    # Keep analyzer silent by default; the CLI can print memory usage if needed.

    def visit_procedure(self, node):
        proc_name = node[1]
        args = node[2]
        declarations = node[3]
        
        if proc_name in self.procedures:
            raise SemanticError(f"Procedure '{proc_name}' already defined.")
        
        self.procedures[proc_name] = ProcedureSymbol(proc_name, args)
        self.enter_scope(proc_name)

        # Reserve memory for procedure parameters.
        self.proc_param_cells[proc_name] = []

        for arg in args:
            arg_type = arg[0]
            arg_name = arg[1]

            sym = self.declare_variable(arg_name) 
            sym.is_param = True
            # Parameter semantics:
            # - Default (IN-OUT) and 'O' params: passed by reference.
            # - 'I' params: read-only, passed by value.
            sym.is_reference = arg_type != 'ARG_INPUT'
            if arg_type == 'ARG_INPUT':
                sym.is_const = True
                sym.is_initialized = True

            self.proc_param_cells[proc_name].append(sym.mem_offset)
            
            if "ARRAY" in arg_type:
                sym.__class__ = ArraySymbol
                sym.is_array = True
                sym.start_idx = 0 # Initialize attributes required by CodeGen
                sym.end_idx = 0 # Bounds are unknown for references, assume 0-based or handled via pointer arithmetic

        for decl in declarations:
            if decl[0] == 'VAR':
                self.declare_variable(decl[1], node=decl)
            elif decl[0] == 'ARRAY':
                self.declare_variable(decl[1], is_array=True, range_start=decl[2], range_end=decl[3], node=decl)
        
        self.exit_scope()

    def visit_main(self, node):
        self.enter_scope("global")
        
        declarations = node[1]
        for decl in declarations:
            if decl[0] == 'VAR':
                self.declare_variable(decl[1], node=decl)
            elif decl[0] == 'ARRAY':
                self.declare_variable(decl[1], is_array=True, range_start=decl[2], range_end=decl[3], node=decl)

        self.exit_scope()