class CodeGenerator:
    def __init__(self, semantic_analyzer):
        self.analyzer = semantic_analyzer
        self.code = []

        # One dedicated memory cell used as a pseudo "call stack" for return
        # addresses. This compiler forbids recursion (per language spec), so
        # a single slot is sufficient.
        self._retaddr_mem = None
        
    def generate(self, ast):
        # AST: ('PROGRAM', procedures, main)
        _, procedures, main = ast
        
        # Reserve a global cell for storing return addresses across CALL/RTRN.
        # Must be reserved before generating any code so offsets are stable.
        if self._retaddr_mem is None:
            self._retaddr_mem = self.analyzer.declare_variable("_retaddr").mem_offset

        # 1. Jump over procedures to start of main
        self.emit("JUMP main_start")
        
        # 2. Generate code for procedures
        for proc in procedures:
            self.visit_procedure(proc)
            
        # 3. Generate Main
        self.emit("main_start:", label=True)
        self.visit_main(main)
        self.emit("HALT")
        
        return self.resolve_labels()

    def emit(self, instr, label=False):
        # Just store the string, we'll format/resolve labels later
        if label:
            self.code.append(instr) # e.g. "label:"
        else:
            self.code.append(f"\t{instr}")

    def resolve_labels(self):
        # Map labels to line numbers, then remove labels from output
        label_map = {}
        clean_code = []
        current_line = 0
        
        # First pass: find label positions
        for line in self.code:
            if line.endswith(":"):
                label_name = line[:-1]
                label_map[label_name] = current_line
            else:
                current_line += 1
                
        # Second pass: replace jumps and filter labels
        final_output = []
        for line in self.code:
            if line.endswith(":"):
                continue
            
            # Check for JUMP/JPOS/JZERO/CALL label
            parts = line.split()
            if len(parts) > 1 and parts[0].strip() in ["JUMP", "JZERO", "JPOS", "CALL"]:
                op = parts[0].strip()
                target = parts[1]
                if target in label_map:
                    # Replace label with absolute line number
                    final_output.append(f"{op} {label_map[target]}")
                else:
                    # Keep as is (maybe it was already a number)
                    final_output.append(line.strip())
            else:
                final_output.append(line.strip())
                
        return final_output

    # --- CONSTANT GENERATION ---
    def gen_constant(self, value, register="a"):
        # Generates a number in a register using shift/inc logic
        # Cost: Log(n)
        self.emit(f"RST {register}")
        if value == 0:
            return
            
        bin_str = bin(value)[2:] # "101"
        for bit in bin_str:
            self.emit(f"SHL {register}")
            if bit == '1':
                self.emit(f"INC {register}")

    # --- MEMORY ADDRESS CALCULATION ---
    def load_variable_address_to_reg(self, sym, reg_idx_result="a", reg_idx_calc="b"):
        # Puts the MEMORY ADDRESS of the variable into reg_idx_result.
        # This is complex for arrays: Addr = offset + (index - start)
        pass 
        # Actually, for RLOAD/RSTORE we usually need the address in a register.
        # But VM has RLOAD x which means r_a <- Memory[r_x].
        
    # --- VISITOR METHODS ---

    def visit_procedure(self, node):
        # ('PROCEDURE', name, args, declarations, commands)
        proc_name = node[1]
        self.emit(f"{proc_name}:", label=True)

        # CALL clobbers r_a with return address. We must save it immediately,
        # because this compiler uses r_a for expression evaluation.
        self.emit(f"STORE {self._retaddr_mem}")
        
        # Parameters and locals live in the procedure scope.
        # Use SemanticAnalyzer scope so identifier->symbol resolution uses
        # the correct memory offsets.
        self.analyzer.enter_scope(proc_name)
        try:
            self.visit_commands(node[4])
        finally:
            self.analyzer.exit_scope()

        # Restore return address and return.
        self.emit(f"LOAD {self._retaddr_mem}")
        self.emit("RTRN")

    def visit_main(self, node):
        # ('MAIN', declarations, commands)
        self.analyzer.enter_scope("global")
        self.visit_commands(node[2])
        self.analyzer.exit_scope()

    def visit_commands(self, commands):
        for cmd in commands:
            self.visit_command(cmd)

    def visit_command(self, cmd):
        tag = cmd[0]
        if tag == 'ASSIGN': self.gen_assign(cmd)
        elif tag == 'IF': self.gen_if(cmd)
        elif tag == 'WHILE': self.gen_while(cmd)
        elif tag == 'REPEAT': self.gen_repeat(cmd)
        elif tag == 'FOR_TO': self.gen_for(cmd, down=False)
        elif tag == 'FOR_DOWNTO': self.gen_for(cmd, down=True)
        elif tag == 'READ': self.gen_read(cmd)
        elif tag == 'WRITE': self.gen_write(cmd)
        elif tag == 'PROC_CALL': self.gen_proc_call(cmd)

    # --- EXPRESSION & MATH ---

    def gen_expression(self, node):
        # Puts result of expression in r_a
        if isinstance(node, tuple):
            tag = node[0]
            if tag == 'NUMBER':
                self.gen_constant(node[1])
            elif tag in ['PIDENTIFIER', 'PIDENTIFIER_WITH_PID', 'PIDENTIFIER_WITH_NUM']:
                self.load_value(node)
            elif tag == 'ADD':
                self.gen_expression(node[1]) # LHS -> a
                self.emit("SWP b")          # a -> b
                self.gen_expression(node[2]) # RHS -> a
                self.emit("ADD b")          # a = a + b
            elif tag == 'SUB':
                self.gen_expression(node[1]) # LHS -> a
                self.emit("SWP b")
                self.gen_expression(node[2]) # RHS -> a
                # SUB in VM is a <- max(a-x, 0).
                # We want LHS - RHS. So we want b - a.
                # Current: b=LHS, a=RHS.
                self.emit("SWP b") # a=LHS, b=RHS
                self.emit("SUB b") # a = a - b
            elif tag == 'MUL':
                self.gen_mul(node[1], node[2])
            elif tag == 'DIV':
                self.gen_div(node[1], node[2])
            elif tag == 'MOD':
                self.gen_mod(node[1], node[2])
        else:
            # Fallback (shouldn't happen with correct AST)
            pass

    def load_value(self, identifier_node):
        # Loads variable value into r_a
        # Handles direct vars, reference vars, and arrays
        sym = self.analyzer.visit_identifier(identifier_node)
        
        if identifier_node[0] == 'PIDENTIFIER':
            # Scalar
            if sym.is_reference:
                # Indirect load: The mem cell contains an address
                self.emit(f"LOAD {sym.mem_offset}") # a = address pointing to data
                self.emit("SWP b")                  # b = address
                self.emit("RLOAD b")                # a = Memory[b]
            else:
                self.emit(f"LOAD {sym.mem_offset}")

        else:
            # Array access: tab[index]
            # Address = sym.mem_offset + (index_val - sym.start_idx)
            
            # 1. Calculate Index Value -> r_a
            if identifier_node[0] == 'PIDENTIFIER_WITH_NUM':
                idx = identifier_node[2]
                self.gen_constant(idx)
            else:
                # WITH_PID
                idx_var_name = identifier_node[2]
                idx_node = ('PIDENTIFIER', idx_var_name)
                self.load_value(idx_node)
            
            # 2. Subtract start_idx
            if sym.start_idx != 0:
                self.emit("SWP b")
                self.gen_constant(sym.start_idx)
                self.emit("SWP b")
                self.emit("SUB b") # a = index - start
            
            # 3. Add base offset
            self.emit("SWP b")
            self.gen_constant(sym.mem_offset)
            self.emit("ADD b") # a = mem_offset + (index-start)
            
            # 4. Load from calculated address
            self.emit("SWP b") # b = address
            self.emit("RLOAD b")

    def store_to_variable(self, identifier_node):
        # Assumes value to store is in r_a
        # Stores r_a into variable defined by node
        
        sym = self.analyzer.visit_identifier(identifier_node, is_write=True)
        
        self.emit("SWP d") # Save value to d temporarily
        
        if identifier_node[0] == 'PIDENTIFIER':
            if sym.is_reference:
                self.emit(f"LOAD {sym.mem_offset}") # a = address
                self.emit("SWP b") # b = address
                self.emit("SWP d") # a = value
                self.emit("RSTORE b") # Memory[b] = a
            else:
                self.emit("SWP d") # a = value
                self.emit(f"STORE {sym.mem_offset}")
        
        else:
            # Array Store
            # 1. Calculate Address (Reuse logic or simplify)
            # Need to be careful not to lose value in d
            
            # Recover value to stack or temp reg? 
            # We have plenty of registers. Let's use 'e' for value.
            self.emit("SWP d") 
            self.emit("SWP e") # Value is in e
            
            # Calc Index -> a
            if identifier_node[0] == 'PIDENTIFIER_WITH_NUM':
                self.gen_constant(identifier_node[2])
            else:
                idx_node = ('PIDENTIFIER', identifier_node[2])
                self.load_value(idx_node)
            
            # Subtract start
            if sym.start_idx != 0:
                self.emit("SWP b")
                self.gen_constant(sym.start_idx)
                self.emit("SWP b")
                self.emit("SUB b")
            
            # Add offset
            self.emit("SWP b")
            self.gen_constant(sym.mem_offset)
            self.emit("ADD b") # a = address
            
            self.emit("SWP b") # b = address
            self.emit("SWP e") # a = value
            self.emit("RSTORE b")

    def gen_proc_call(self, cmd):
        # ('PROC_CALL', proc_name, [arg1, arg2, ...])
        proc_name = cmd[1]
        arg_names = cmd[2]

        if proc_name not in self.analyzer.procedures:
            raise Exception(f"Error: Call to undefined procedure '{proc_name}'")

        proc_def = self.analyzer.procedures[proc_name]
        def_args = proc_def.args

        if len(arg_names) != len(def_args):
            raise Exception(
                f"Error: Procedure '{proc_name}' expects {len(def_args)} arguments, got {len(arg_names)}"
            )

        # Convention used by this compiler:
        # - Formal parameters were allocated as memory cells in the procedure scope
        #   (via SemanticAnalyzer.declare_variable during visit_procedure).
        # - Each formal parameter cell stores the ADDRESS of the actual argument.
        # - For scalar args: address of the variable cell.
        # - For array args: address of the first cell of the array.
        # - For actual arguments that are themselves references (params in caller),
        #   we must load the pointer stored in their cell.
        #
        # Therefore, at call site we write into each callee param cell.
        # NOTE: we must not rely on analyzer.scopes[proc_name] bindings here,
        # because SemanticAnalyzer exits procedure scopes after analysis.
        # We use the stable offsets recorded during analysis.
        try:
            param_cells = self.analyzer.proc_param_cells[proc_name]
        except Exception:
            raise Exception(f"Internal error: missing parameter layout for procedure '{proc_name}'")

        for i, ((def_arg, actual_name), param_cell_offset) in enumerate(zip(zip(def_args, arg_names), param_cells)):
            def_type, def_name = def_arg[0], def_arg[1]

            # Locate actual argument symbol in caller scope/global
            actual_sym = self.analyzer.get_symbol(actual_name)

            # If the callee parameter is a by-value constant (I), copy the value.
            if def_type == 'ARG_INPUT':
                # Pass by VALUE
                # Arrays can't be I by spec grammar in this repo (T is separate),
                # but keep a defensive check.
                if actual_sym.is_array:
                    raise Exception(
                        f"Error: Procedure '{proc_name}' expects scalar argument '{def_name}', got array '{actual_name}'"
                    )
                # Load actual value, then store into callee param cell.
                self.load_value(('PIDENTIFIER', actual_name))
                self.emit(f"STORE {param_cell_offset}")
                continue

            if def_type == 'ARG_ARRAY':
                # Expect array
                if not actual_sym.is_array:
                    raise Exception(
                        f"Error: Procedure '{proc_name}' expects array argument '{def_name}', got '{actual_name}'"
                    )
                # Address of array base is its mem_offset.
                # If the array is passed as reference (param), load the pointer first.
                if getattr(actual_sym, 'is_reference', False):
                    self.emit(f"LOAD {actual_sym.mem_offset}")
                else:
                    self.gen_constant(actual_sym.mem_offset)

            else:
                # Expect scalar variable
                if actual_sym.is_array:
                    raise Exception(
                        f"Error: Procedure '{proc_name}' expects scalar argument '{def_name}', got array '{actual_name}'"
                    )
                if getattr(actual_sym, 'is_reference', False):
                    # actual_sym.mem_offset points to a cell holding the real address
                    self.emit(f"LOAD {actual_sym.mem_offset}")
                else:
                    self.gen_constant(actual_sym.mem_offset)

            # Store computed address into callee parameter cell
            self.emit(f"STORE {param_cell_offset}")

        self.emit(f"CALL {proc_name}")

    # --- COMMAND GENERATORS ---

    def gen_assign(self, cmd):
        # ('ASSIGN', identifier, expression)
        self.gen_expression(cmd[2])
        self.store_to_variable(cmd[1])

    def gen_read(self, cmd):
        self.emit("READ")
        self.store_to_variable(cmd[1])

    def gen_write(self, cmd):
        val = cmd[1]
        if isinstance(val, tuple):
            self.load_value(val)
        else: # NUMBER
            self.gen_constant(val)
        self.emit("WRITE")

    def gen_if(self, cmd):
        # ('IF', condition, cmd_true, cmd_false)
        cond = cmd[1]
        false_label = f"else_{id(cmd)}"
        end_label = f"endif_{id(cmd)}"
        
        # Generates code for condition, JUMPS to false_label if false
        self.gen_condition(cond, false_label)
        
        self.visit_commands(cmd[2])
        if len(cmd) > 3:
            self.emit(f"JUMP {end_label}")
            
        self.emit(f"{false_label}:", label=True)
        if len(cmd) > 3:
            self.visit_commands(cmd[3])
            self.emit(f"{end_label}:", label=True)

    def gen_while(self, cmd):
        start_label = f"while_start_{id(cmd)}"
        end_label = f"while_end_{id(cmd)}"
        
        self.emit(f"{start_label}:", label=True)
        self.gen_condition(cmd[1], end_label)
        
        self.visit_commands(cmd[2])
        self.emit(f"JUMP {start_label}")
        self.emit(f"{end_label}:", label=True)

    def gen_repeat(self, cmd):
        start_label = f"repeat_start_{id(cmd)}"
        self.emit(f"{start_label}:", label=True)
        self.visit_commands(cmd[1])
        # REPEAT ... UNTIL cond
        # If cond is TRUE, we stop. So if FALSE, we jump back.
        # gen_condition jumps if FALSE. So we invert logic?
        # My gen_condition jumps to target if FALSE.
        # We want: If FALSE, JUMP start.
        self.gen_condition(cmd[2], start_label) 

    def gen_for(self, cmd, down=False):
        # ('FOR_TO', iterator_name, start_val, end_val, commands)
        # Note: Spec says iterator is local and calc'd once.
        # Implementation:
        # 1. Calc start -> Iterator
        # 2. Calc end -> Temp Limit Register/Mem
        # 3. Loop Check
        # 4. Body
        # 5. Inc/Dec Iterator

        iterator_name = cmd[1]
        start_val = cmd[2]
        end_val = cmd[3]

        # The semantic analyzer in this repo doesn't traverse command bodies.
        # That means FOR iterators are not guaranteed to exist in scopes during
        # code generation. We therefore reserve the iterator + limit cells here.
        # They are local to the generated code, consistent with spec.

        # Reserve an internal cell for iterator storage (must not clash with
        # user-declared names; iterator is local by spec).
        iter_storage_name = f"_iter_{iterator_name}_{id(cmd)}"
        iter_sym = self.analyzer.declare_variable(iter_storage_name)
        iter_sym.is_iterator = True
        iter_sym.is_const = True
        iter_sym.is_initialized = True

        limit_name = f"_limit_{iterator_name}_{id(cmd)}"
        limit_sym = self.analyzer.declare_variable(limit_name)
        limit_sym.is_initialized = True

        # Temporarily bind the user-visible iterator name to the internal
        # storage symbol for the duration of loop body generation.
        scope = self.analyzer.scopes[self.analyzer.current_scope_name]
        prev_iter_binding = scope.get(iterator_name)
        scope[iterator_name] = iter_sym
        
        # 1. Init Iterator
        self.gen_expression(start_val)
        self.emit(f"STORE {iter_sym.mem_offset}")

        # 2. Evaluate and store loop limit ONCE (spec requirement).
        if limit_sym is not None:
            self.gen_expression(end_val)
            self.emit(f"STORE {limit_sym.mem_offset}")
        
        start_label = f"for_start_{id(cmd)}"
        end_label = f"for_end_{id(cmd)}"
        
        self.emit(f"{start_label}:", label=True)
        
        # Load Iterator -> a
        self.emit(f"LOAD {iter_sym.mem_offset}")

        # Load Limit -> b (from hidden limit variable, no re-evaluation)
        if limit_sym is None:
            # Backwards compatibility fallback (shouldn't happen after SA fix).
            self.emit("SWP b")
            self.gen_expression(end_val)
            self.emit("SWP b")
        else:
            self.emit("SWP b")
            self.emit(f"LOAD {limit_sym.mem_offset}")
            self.emit("SWP b")
        
        # Check Condition
        # UP: iter <= limit  => continue. Else jump end.
        # VM: SUB b (a - b). If a > b (result > 0) -> Stop.
        # But SUB is max(a-b, 0).
        # If iter > limit, iter - limit > 0.
        
        self.emit("SWP c") # c = b (limit)
        self.emit("SWP b") # b = a (iter), a = c (limit)
        # a=limit, b=iter
        
        if down:
             # DOWN: iter >= limit. Stop if iter < limit.
             # Stop if limit > iter.
             # limit - iter > 0
             self.emit("SUB b") # limit - iter
             self.emit(f"JPOS {end_label}")
        else:
             # UP: iter <= limit. Stop if iter > limit.
             # iter - limit > 0
             self.emit("SWP b") # a=iter, b=limit
             self.emit("SUB b") # iter - limit
             self.emit(f"JPOS {end_label}")
             
        # Body
        self.visit_commands(cmd[4])
        
        # Increment/Decrement
        self.emit(f"LOAD {iter_sym.mem_offset}")
        if down:
            self.emit("DEC a")
        else:
            self.emit("INC a")
        self.emit(f"STORE {iter_sym.mem_offset}")
        
        self.emit(f"JUMP {start_label}")
        self.emit(f"{end_label}:", label=True)

        # Restore previous iterator binding (if any) and release our temp cells.
        if prev_iter_binding is None:
            del scope[iterator_name]
        else:
            scope[iterator_name] = prev_iter_binding

        del scope[iter_storage_name]
        del scope[limit_name]
        self.analyzer.memory_counter -= 2

    def gen_condition(self, node, jump_target_if_false):
        # ('EQ', val1, val2) etc.
        # Generates code that JUMPS to jump_target_if_false if condition is FALSE.
        
        op = node[0]
        # Parser/AST tag normalization
        op_map = {
            'EQUAL': 'EQ',
            'NE': 'NEQ',
            'NEQ': 'NEQ',
            'LEQ': 'LE',
            'GEQ': 'GE',
            'LT': 'LT',
            'GT': 'GT',
            'LE': 'LE',
            'GE': 'GE',
            'EQ': 'EQ',
        }
        op = op_map.get(op, op)
        # Evaluate LHS -> c, RHS -> d (preserved copies)
        self.gen_expression(node[1])
        self.emit("SWP c")
        self.gen_expression(node[2])
        self.emit("SWP d")

        # Helper: compute (x - y) with x in reg_x, y in reg_y.
        # We do: a = x; b = y; a = a - b
        def sub_regs(reg_x, reg_y):
            self.emit("RST a")
            self.emit(f"ADD {reg_x}")
            self.emit(f"SWP b")
            self.emit("RST a")
            self.emit(f"ADD {reg_y}")
            self.emit("SUB b")

        # Semantics: jump when condition is FALSE.
        if op == 'EQ':
            # False when c != d.
            sub_regs('c', 'd')
            self.emit(f"JPOS {jump_target_if_false}")  # c > d
            sub_regs('d', 'c')
            self.emit(f"JPOS {jump_target_if_false}")  # d > c

        elif op == 'NEQ':
            # False when c == d.
            true_label = f"cond_neq_true_{id(node)}"
            sub_regs('c', 'd')
            self.emit(f"JPOS {true_label}")
            sub_regs('d', 'c')
            self.emit(f"JPOS {true_label}")
            # equal => false
            self.emit(f"JUMP {jump_target_if_false}")
            self.emit(f"{true_label}:", label=True)

        elif op == 'LT':
            # c < d; false when c >= d.
            # If c - d > 0 => c > d (false). If c - d == 0 => equal (false).
            sub_regs('c', 'd')
            self.emit(f"JPOS {jump_target_if_false}")
            self.emit(f"JZERO {jump_target_if_false}")

        elif op == 'GT':
            # c > d; false when c <= d.
            # If d - c > 0 => d > c (false). If d - c == 0 => equal (false).
            sub_regs('d', 'c')
            self.emit(f"JPOS {jump_target_if_false}")
            self.emit(f"JZERO {jump_target_if_false}")

        elif op == 'LE':
            # c <= d; false when c > d.
            sub_regs('c', 'd')
            self.emit(f"JPOS {jump_target_if_false}")

        elif op == 'GE':
            # c >= d; false when c < d.
            sub_regs('d', 'c')
            self.emit(f"JPOS {jump_target_if_false}")

        else:
            raise Exception(f"Unknown condition op: {op}")

    # --- MATH HELPERS (Logarithmic) ---
    def gen_mul(self, node1, node2):
        # a * b
        # Hardest part: Registers are limited and we don't have a stack.
        # We need to perform a*b -> a.
        # Use registers: 
        # r_c = multiplier (a)
        # r_d = multiplicand (b)
        # r_e = result (0)
        
        self.gen_expression(node1)
        self.emit("SWP c") # c = a
        self.gen_expression(node2)
        self.emit("SWP d") # d = a
        
        self.emit("RST e") # res = 0
        
        # Loop Label
        start = f"mul_start_{id(node1)}"
        end = f"mul_end_{id(node1)}"
        
        self.emit(f"{start}:", label=True)
        # if c == 0 jump end
        self.emit("RST a")
        self.emit("ADD c")
        self.emit(f"JZERO {end}")
        
        # if c % 2 != 0: res += d
        # check parity of c:
        # copy c to a, div by 2, mul by 2, sub from orig?
        # or simpler: c is shifted right every time. 
        # Check lowest bit?
        # Standard VM trick for parity:
        # tmp = c / 2
        # tmp = tmp * 2
        # diff = c - tmp
        # if diff > 0 -> odd.
        
        self.emit("SWP a") # a = c
        self.emit("SWP f") # f = c (save)
        self.emit("SHR a") # a = c/2
        self.emit("SWP a") # a=0?, swp a is c/2
        self.emit("SHL a") # a = (c/2)*2
        self.emit("SWP b") # b = floor
        self.emit("RST a")
        self.emit("ADD f") # a = c
        self.emit("SUB b") # a = c - floor
        
        skip_add = f"mul_skip_{id(node1)}_{id(node2)}"
        self.emit(f"JZERO {skip_add}")
        
        # Add d to res
        self.emit("RST a")
        self.emit("ADD e")
        self.emit("ADD d")
        self.emit("SWP e") # e = new res
        
        self.emit(f"{skip_add}:", label=True)
        
        # d *= 2
        self.emit("RST a")
        self.emit("ADD d")
        self.emit("SHL a")
        self.emit("SWP d")
        
        # c /= 2
        self.emit("RST a")
        self.emit("ADD f") # recover c
        self.emit("SHR a")
        self.emit("SWP c")
        
        self.emit(f"JUMP {start}")
        self.emit(f"{end}:", label=True)
        
        self.emit("RST a")
        self.emit("ADD e") # result to a

    def _gen_divmod(self, node1, node2, want_quotient: bool):
        """Compute quotient or remainder of integer division in O(log a).

        Contract:
        - Inputs: expression nodes node1 (dividend), node2 (divisor)
        - Output: result in r_a
          - if want_quotient: floor(dividend/divisor)
          - else: dividend % divisor
        - Division by zero: returns 0 (both quotient and remainder)

        Register plan (kept local to this routine):
        - c: dividend (will be reduced)
        - d: divisor
        - e: quotient
        - f: "current" divisor multiple (dv)
        - g: "current" power-of-two multiple (pow)
        - b: scratch
        """

        # Evaluate dividend/divisor
        self.gen_expression(node1)
        self.emit("SWP c")  # c = dividend
        self.gen_expression(node2)
        self.emit("SWP d")  # d = divisor

        # If divisor == 0 => result 0
        div_by_zero = f"divmod_div0_{id(node1)}_{id(node2)}_{'q' if want_quotient else 'r'}"
        divmod_end = f"divmod_end_{id(node1)}_{id(node2)}_{'q' if want_quotient else 'r'}"
        self.emit("RST a")
        self.emit("ADD d")
        self.emit(f"JZERO {div_by_zero}")

        # quotient = 0
        self.emit("RST e")

        # Main loop: while dividend >= divisor
        outer = f"divmod_outer_{id(node1)}_{id(node2)}_{'q' if want_quotient else 'r'}"
        outer_end = f"divmod_outer_end_{id(node1)}_{id(node2)}_{'q' if want_quotient else 'r'}"
        self.emit(f"{outer}:", label=True)

        # Continue while dividend >= divisor.
        # Note: VM SUB is saturating (a <- max(a-x,0)), so we cannot infer
        # a negative result. We instead use:
        #   if dividend == divisor -> handle once in the eq handler
        #   if dividend > divisor  -> proceed with main subtraction step
        #   else (dividend < divisor) -> stop
        self.emit("RST a")
        self.emit("ADD c")
        self.emit("SUB d")
        self.emit(f"JZERO {outer_end}_eq")  # dividend == divisor
        self.emit(f"JPOS {outer}_cont")     # dividend > divisor
        self.emit(f"JUMP {outer_end}")      # dividend < divisor
        self.emit(f"{outer}_cont:", label=True)

        # Setup dv = divisor, pow = 1
        self.emit("RST a")
        self.emit("ADD d")
        self.emit("SWP f")  # f = dv
        self.emit("RST g")
        self.emit("INC g")  # g = pow

        # Find the largest dv <= dividend by doubling.
        # We keep doubling while (dividend - (dv*2)) >= 0.
        grow = f"divmod_grow_{id(node1)}_{id(node2)}_{'q' if want_quotient else 'r'}"
        grow_end = f"divmod_grow_end_{id(node1)}_{id(node2)}_{'q' if want_quotient else 'r'}"
        self.emit(f"{grow}:", label=True)
        # b = dv*2
        self.emit("RST a")
        self.emit("ADD f")
        self.emit("SHL a")
        self.emit("SWP b")
        # if dividend - b >= 0 then we can grow
        self.emit("RST a")
        self.emit("ADD c")
        self.emit("SUB b")
        self.emit(f"JPOS {grow}_do")
        self.emit(f"JZERO {grow}_do")
        self.emit(f"JUMP {grow_end}")
        self.emit(f"{grow}_do:", label=True)
        # dv = dv*2, pow = pow*2
        self.emit("RST a")
        self.emit("ADD b")
        self.emit("SWP f")
        self.emit("SHL g")
        self.emit(f"JUMP {grow}")
        self.emit(f"{grow_end}:", label=True)

        # Subtract dv from dividend and add pow to quotient
        self.emit("RST a")
        self.emit("ADD c")
        self.emit("SUB f")
        self.emit("SWP c")  # c = dividend - dv

        self.emit("RST a")
        self.emit("ADD e")
        self.emit("ADD g")
        self.emit("SWP e")  # e += pow

        # Loop again
        self.emit(f"JUMP {outer}")


        # Handle dividend == divisor case (one last subtraction)
        self.emit(f"{outer_end}_eq:", label=True)
        # dividend == divisor => subtract once:
        # - remainder becomes 0
        # - quotient increments by 1
        self.emit("RST c")
        self.emit("INC e")

        # Common exit point for outer loop
        self.emit(f"{outer_end}:", label=True)

        # Return selected result
        if want_quotient:
            self.emit("RST a")
            self.emit("ADD e")
        else:
            self.emit("RST a")
            self.emit("ADD c")
        self.emit(f"JUMP {divmod_end}")

        self.emit(f"{div_by_zero}:", label=True)
        self.emit("RST a")
        self.emit(f"{divmod_end}:", label=True)

    def gen_div(self, node1, node2):
        # a / b (floor), logarithmic time
        self._gen_divmod(node1, node2, want_quotient=True)

    def gen_mod(self, node1, node2):
        # a % b, logarithmic time
        self._gen_divmod(node1, node2, want_quotient=False)