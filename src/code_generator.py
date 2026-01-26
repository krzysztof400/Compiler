from peephole_optimizer import peephole_optimize


class CodeGenerator:
    def __init__(self, semantic_analyzer):
        self.analyzer = semantic_analyzer
        self.code = []
        self.proc_ret_offsets = {}
        self.verbose = False

    @staticmethod
    def _is_power_of_two(value):
        return value > 0 and (value & (value - 1)) == 0

    @staticmethod
    def _power_of_two_shift(value):
        return value.bit_length() - 1

    def generate(self, ast):
        # AST: ('PROGRAM', procedures, main)
        _, procedures, main = ast
        
        self.emit("JUMP main_start")
        
        for proc in procedures:
            self.visit_procedure(proc)
            
        self.emit("main_start:", label=True)
        self.visit_main(main)
        self.emit("HALT")
        
        if self.verbose:
            for line in self.code:
                print(line)
        resolved = self.resolve_labels()
        return peephole_optimize(resolved)

    def emit(self, instr, label=False):
        if label:
            self.code.append(instr)
        else:
            self.code.append(f"\t{instr}")

    def resolve_labels(self):
        label_map = {}
        clean_code = []
        current_line = 0
        
        for line in self.code:
            if line.endswith(":"):
                label_name = line[:-1]
                label_map[label_name] = current_line
            else:
                current_line += 1
                
        final_output = []
        for line in self.code:
            if line.endswith(":"):
                continue
            
            parts = line.split()
            if len(parts) > 1 and parts[0].strip() in ["JUMP", "JZERO", "JPOS", "CALL"]:
                op = parts[0].strip()
                target = parts[1]
                if target in label_map:
                    final_output.append(f"{op} {label_map[target]}")
                else:
                    final_output.append(line.strip())
            else:
                final_output.append(line.strip())
                
        return final_output

    def gen_constant(self, value, register="a"):
        # Generates code to create a constant number in a register
        self.emit(f"RST {register}")
        if value == 0:
            return
            
        bin_str = bin(value)[2:] 
        for bit in bin_str:
            self.emit(f"SHL {register}")
            if bit == '1':
                self.emit(f"INC {register}")

    # --- VISITOR METHODS ---

    def visit_procedure(self, node):
        proc_name = node[1]
        self.emit(f"{proc_name}:", label=True)

        ret_var_name = f"_retaddr_{proc_name}"
        ret_sym = self.analyzer.declare_variable(ret_var_name)
        self.proc_ret_offsets[proc_name] = ret_sym.mem_offset

        self.emit(f"STORE {ret_sym.mem_offset}")
        
        self.analyzer.enter_scope(proc_name)
        try:
            self.visit_commands(node[4])
        finally:
            self.analyzer.exit_scope()

        # Restore specific return address and return
        self.emit(f"LOAD {ret_sym.mem_offset}")
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
        if isinstance(node, tuple):
            tag = node[0]
            def is_number(n):
                return isinstance(n, tuple) and n[0] == 'NUMBER'

            if tag == 'NUMBER':
                self.gen_constant(node[1])
            elif tag in ['PIDENTIFIER', 'PIDENTIFIER_WITH_PID', 'PIDENTIFIER_WITH_NUM']:
                self.load_value(node)
            elif tag == 'ADD':
                left, right = node[1], node[2]
                if is_number(left) and is_number(right):
                    self.gen_constant(left[1] + right[1])
                    return
                if is_number(left) and left[1] == 0:
                    self.gen_expression(right)
                    return
                if is_number(right) and right[1] == 0:
                    self.gen_expression(left)
                    return
                self.gen_expression(node[1])
                self.emit("SWP h")
                self.gen_expression(node[2])
                self.emit("ADD h")
            elif tag == 'SUB':
                left, right = node[1], node[2]
                if is_number(left) and is_number(right):
                    self.gen_constant(max(left[1] - right[1], 0))
                    return
                if is_number(right) and right[1] == 0:
                    self.gen_expression(left)
                    return
                # max(a-b, 0)
                self.gen_expression(node[1])
                self.emit("SWP h")
                self.gen_expression(node[2])
                self.emit("SWP h")
                self.emit("SUB h")
            elif tag == 'MUL':
                left, right = node[1], node[2]
                if (is_number(left) and left[1] == 0) or (is_number(right) and right[1] == 0):
                    self.gen_constant(0)
                    return
                if is_number(left) and left[1] == 1:
                    self.gen_expression(right)
                    return
                if is_number(right) and right[1] == 1:
                    self.gen_expression(left)
                    return
                if is_number(left) and is_number(right):
                    self.gen_constant(left[1] * right[1])
                    return
                if is_number(right) and self._is_power_of_two(right[1]):
                    self.gen_expression(left)
                    shift = self._power_of_two_shift(right[1])
                    for _ in range(shift):
                        self.emit("SHL a")
                    return
                self.gen_mul(node[1], node[2])
            elif tag == 'DIV':
                left, right = node[1], node[2]
                if is_number(left) and is_number(right):
                    if right[1] == 0:
                        self.gen_constant(0)
                    else:
                        self.gen_constant(left[1] // right[1])
                    return
                if is_number(right) and right[1] == 1:
                    self.gen_expression(left)
                    return
                if is_number(right) and self._is_power_of_two(right[1]):
                    self.gen_expression(left)
                    shift = self._power_of_two_shift(right[1])
                    for _ in range(shift):
                        self.emit("SHR a")
                    return
                self.gen_div(node[1], node[2])
            elif tag == 'MOD':
                left, right = node[1], node[2]
                if is_number(left) and is_number(right):
                    if right[1] == 0:
                        self.gen_constant(0)
                    else:
                        self.gen_constant(left[1] % right[1])
                    return
                if is_number(right) and right[1] == 1:
                    self.gen_constant(0)
                    return
                if is_number(right) and self._is_power_of_two(right[1]):
                    shift = self._power_of_two_shift(right[1])
                    self.gen_expression(left)
                    self.emit("SWP b")
                    self.emit("RST a")
                    self.emit("ADD b")
                    for _ in range(shift):
                        self.emit("SHR a")
                    for _ in range(shift):
                        self.emit("SHL a")
                    self.emit("SWP c")
                    self.emit("RST a")
                    self.emit("ADD b")
                    self.emit("SUB c")
                    return
                self.gen_mod(node[1], node[2])

    def load_value(self, identifier_node):
        # Result ends up in r_a
        sym = self.analyzer.visit_identifier(identifier_node, enforce_checks=False)
        
        if identifier_node[0] == 'PIDENTIFIER':
            if getattr(sym, 'is_reference', False):
                self.emit(f"LOAD {sym.mem_offset}") # a = address
                self.emit("SWP b")                  
                self.emit("RLOAD b")                # a = Mem[b]
            else:
                self.emit(f"LOAD {sym.mem_offset}")
        else:
            # Array Logic
            # 1. Calc Index -> r_a
            if identifier_node[0] == 'PIDENTIFIER_WITH_NUM':
                self.gen_constant(identifier_node[2])
            else:
                idx_name = identifier_node[2]
                self.load_value(('PIDENTIFIER', idx_name))
            
            # 2. Subtract start_idx
            if getattr(sym, "start_idx_offset", None) is not None:
                self.emit("SWP b")
                self.emit(f"LOAD {sym.start_idx_offset}")
                self.emit("SWP b")
                self.emit("SUB b")
            elif sym.start_idx != 0:
                self.emit("SWP b")
                self.gen_constant(sym.start_idx)
                self.emit("SWP b")
                self.emit("SUB b") 
            
            # 3. Add base offset
            self.emit("SWP b")
            if getattr(sym, 'is_reference', False):
                self.emit(f"LOAD {sym.mem_offset}")
            else:
                self.gen_constant(sym.mem_offset)
            self.emit("ADD b") 
            
            # 4. Indirect Load
            self.emit("SWP b") 
            self.emit("RLOAD b")

    def store_to_variable(self, identifier_node):
        # Value to store is in r_a
        sym = self.analyzer.visit_identifier(identifier_node, is_write=True, enforce_checks=False)
        self.emit("SWP d") # Save value to d
        
        if identifier_node[0] == 'PIDENTIFIER':
            if getattr(sym, 'is_reference', False):
                self.emit(f"LOAD {sym.mem_offset}") # a = address pointer
                self.emit("SWP b") 
                self.emit("SWP d") # a = value
                self.emit("RSTORE b")
            else:
                self.emit("SWP d") 
                self.emit(f"STORE {sym.mem_offset}")
        else:
            # Array Store
            self.emit("SWP d") 
            self.emit("SWP e") # Value in e
            
            # Index -> a
            if identifier_node[0] == 'PIDENTIFIER_WITH_NUM':
                self.gen_constant(identifier_node[2])
            else:
                self.load_value(('PIDENTIFIER', identifier_node[2]))
            
            # Subtract start
            if getattr(sym, "start_idx_offset", None) is not None:
                self.emit("SWP b")
                self.emit(f"LOAD {sym.start_idx_offset}")
                self.emit("SWP b")
                self.emit("SUB b")
            elif sym.start_idx != 0:
                self.emit("SWP b")
                self.gen_constant(sym.start_idx)
                self.emit("SWP b")
                self.emit("SUB b")
            
            # Add offset
            self.emit("SWP b")
            if getattr(sym, 'is_reference', False):
                self.emit(f"LOAD {sym.mem_offset}")
            else:
                self.gen_constant(sym.mem_offset)
            self.emit("ADD b") 
            
            self.emit("SWP b") # b = address
            self.emit("SWP e") # a = value
            self.emit("RSTORE b")

    def gen_proc_call(self, cmd):
        proc_name = cmd[1]
        arg_names = cmd[2]
        proc_def = self.analyzer.procedures[proc_name]
        
        # Get parameter memory cells for the CALLEE
        try:
            param_cells = self.analyzer.proc_param_cells[proc_name]
        except KeyError:
             raise Exception(f"Internal Error: No memory map for {proc_name}")

        for i, ((def_arg, actual_name), param_info) in enumerate(zip(zip(proc_def.args, arg_names), param_cells)):
            def_type = def_arg[0]
            actual_sym = self.analyzer.get_symbol(actual_name)

            if def_type == 'ARG_INPUT': 
                # Pass by Value (Copy)
                self.load_value(('PIDENTIFIER', actual_name))
                self.emit(f"STORE {param_info['base']}")
            else:
                # Pass by Reference (Pass Address)
                if actual_sym.is_array:
                    # Array Ref: load or compute base address
                    if getattr(actual_sym, 'is_reference', False):
                        self.emit(f"LOAD {actual_sym.mem_offset}")
                    else:
                        self.gen_constant(actual_sym.mem_offset)
                    self.emit(f"STORE {param_info['base']}")

                    if param_info.get('start') is not None:
                        if getattr(actual_sym, 'start_idx_offset', None) is not None:
                            self.emit(f"LOAD {actual_sym.start_idx_offset}")
                        else:
                            self.gen_constant(actual_sym.start_idx)
                        self.emit(f"STORE {param_info['start']}")
                else:
                    # Scalar Ref
                    if getattr(actual_sym, 'is_reference', False):
                        self.emit(f"LOAD {actual_sym.mem_offset}")
                    else:
                        self.gen_constant(actual_sym.mem_offset)
                    self.emit(f"STORE {param_info['base']}")

        self.emit(f"CALL {proc_name}")

    # --- CONTROL FLOW ---

    def gen_assign(self, cmd):
        self.gen_expression(cmd[2])
        self.store_to_variable(cmd[1])

    def gen_read(self, cmd):
        self.emit("READ")
        self.store_to_variable(cmd[1])

    def gen_write(self, cmd):
        val = cmd[1]
        self.gen_expression(val)
        self.emit("WRITE")

    def gen_if(self, cmd):
        cond = cmd[1]
        false_label = f"else_{id(cmd)}"
        end_label = f"endif_{id(cmd)}"
        
        self.gen_condition(cond, false_label) # Jump if FALSE
        self.visit_commands(cmd[2])
        
        has_else = len(cmd) > 3 and isinstance(cmd[3], list) and len(cmd[3]) > 0
        if has_else:
            self.emit(f"JUMP {end_label}")
            
        self.emit(f"{false_label}:", label=True)
        if has_else:
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
        # If cond is TRUE, we stop. So if cond is FALSE, we JUMP back.
        # gen_condition jumps if FALSE. So checking condition -> jump back 
        # is exactly what we need.
        self.gen_condition(cmd[2], start_label) 

    def gen_for(self, cmd, down=False):
        iterator_name = cmd[1]
        start_val = cmd[2]
        end_val = cmd[3]

        # Allocate internal registers for loop bounds
        iter_storage_name = f"_iter_{id(cmd)}"
        iter_sym = self.analyzer.declare_variable(iter_storage_name)
        iter_sym.is_initialized = True
        
        limit_name = f"_limit_{id(cmd)}"
        limit_sym = self.analyzer.declare_variable(limit_name)
        limit_sym.is_initialized = True

        # Scope Management for Iterator
        scope = self.analyzer.scopes[self.analyzer.current_scope_name]
        prev_iter_binding = scope.get(iterator_name)
        scope[iterator_name] = iter_sym
        
        # 1. Init Iterator
        self.gen_expression(start_val)
        self.emit(f"STORE {iter_sym.mem_offset}")

        # 2. Calc Limit ONCE
        self.gen_expression(end_val)
        self.emit(f"STORE {limit_sym.mem_offset}")
        
        start_label = f"for_start_{id(cmd)}"
        end_label = f"for_end_{id(cmd)}"
        
        self.emit(f"{start_label}:", label=True)
        
        # Load values
        self.emit(f"LOAD {iter_sym.mem_offset}") # a = iter
        self.emit("SWP b") 
        self.emit(f"LOAD {limit_sym.mem_offset}") # a = limit, b = iter
        
        if down:
             # DOWNTO: Run if iter >= limit.
             # Stop if iter < limit. (limit > iter)
             # limit - iter > 0
             self.emit("SUB b") 
             self.emit(f"JPOS {end_label}")
        else:
             # TO: Run if iter <= limit.
             # Stop if iter > limit.
             # iter - limit > 0
             self.emit("SWP b") # a=iter, b=limit
             self.emit("SUB b") 
             self.emit(f"JPOS {end_label}")
             
        self.visit_commands(cmd[4])
        
        # Update Iterator
        self.emit(f"LOAD {iter_sym.mem_offset}")
        if down:
            # If iter == limit, stop to avoid DEC saturation loops (limit may be 0).
            self.emit("SWP b")
            self.emit(f"LOAD {limit_sym.mem_offset}")
            self.emit("SWP b")
            self.emit("SUB b")
            self.emit(f"JZERO {end_label}")
            self.emit(f"LOAD {iter_sym.mem_offset}")
            self.emit("DEC a")
        else:
            self.emit("INC a")
        self.emit(f"STORE {iter_sym.mem_offset}")
        
        self.emit(f"JUMP {start_label}")
        self.emit(f"{end_label}:", label=True)

        # Cleanup
        if prev_iter_binding is None:
            del scope[iterator_name]
        else:
            scope[iterator_name] = prev_iter_binding
        del scope[iter_storage_name]
        del scope[limit_name]

    def gen_condition(self, node, jump_target_if_false):
        op = node[0]
        # Map AST ops to standard set
        op_map = {'EQUAL': 'EQ', 'NE': 'NEQ', 'NEQ': 'NEQ', 'LEQ': 'LE', 'GEQ': 'GE'}
        op = op_map.get(op, op)

        self.gen_expression(node[1])
        self.emit("SWP c")
        self.gen_expression(node[2])
        self.emit("SWP d")

        # c = LHS, d = RHS
        def check_diff(reg_x, reg_y):
            # Returns a = max(reg_x - reg_y, 0)
            self.emit("RST a")
            self.emit(f"ADD {reg_x}")
            self.emit(f"SUB {reg_y}")

        if op == 'EQ':
            # False if c != d. (c > d OR d > c)
            check_diff('c', 'd') # c - d
            self.emit(f"JPOS {jump_target_if_false}")
            check_diff('d', 'c') # d - c
            self.emit(f"JPOS {jump_target_if_false}")

        elif op == 'NEQ':
            # False if c == d.
            # If c != d, we must NOT jump.
            true_label = f"cond_true_{id(node)}"
            check_diff('c', 'd')
            self.emit(f"JPOS {true_label}") # c > d, true, skip jump
            check_diff('d', 'c')
            self.emit(f"JPOS {true_label}") # d > c, true, skip jump
            self.emit(f"JUMP {jump_target_if_false}") # Equal
            self.emit(f"{true_label}:", label=True)

        elif op == 'LT':
            # True if d - c > 0, False otherwise
            check_diff('d', 'c')
            self.emit(f"JZERO {jump_target_if_false}")

        elif op == 'GT':
            # c > d. False if c <= d.
            # True only if c - d > 0.
            check_diff('c', 'd')
            self.emit(f"JZERO {jump_target_if_false}")

        elif op == 'LE':
            # c <= d. False if c > d.
            check_diff('c', 'd')
            self.emit(f"JPOS {jump_target_if_false}")

        elif op == 'GE':
            # c >= d. False if d > c.
            check_diff('d', 'c')
            self.emit(f"JPOS {jump_target_if_false}")

    # --- MATH (Logarithmic Time) ---

    def gen_mul(self, node1, node2):
        # Result in r_a
        if isinstance(node2, tuple) and node2[0] == 'NUMBER' and self._is_power_of_two(node2[1]):
            self.gen_expression(node1)
            shift = self._power_of_two_shift(node2[1])
            for _ in range(shift):
                self.emit("SHL a")
            return
        self.gen_expression(node1)
        self.emit("SWP c")  # multiplier
        self.gen_expression(node2)
        self.emit("SWP d")  # multiplicand
        self.emit("RST e")  # accumulator

        start = f"mul_start_{id(node1)}"
        end = f"mul_end_{id(node1)}"

        self.emit(f"{start}:", label=True)
        # if c == 0 => end
        self.emit("RST a")
        self.emit("ADD c")
        self.emit(f"JZERO {end}")

        # Check if c is odd: c - (c/2)*2
        self.emit("RST a")
        self.emit("ADD c")
        self.emit("SHR a")
        self.emit("SHL a")
        self.emit("SWP b")
        self.emit("RST a")
        self.emit("ADD c")
        self.emit("SUB b")

        skip = f"mul_skip_{id(node1)}_{id(node2)}"
        self.emit(f"JZERO {skip}")

        # e += d
        self.emit("RST a")
        self.emit("ADD e")
        self.emit("ADD d")
        self.emit("SWP e")

        self.emit(f"{skip}:", label=True)

        # d *= 2
        self.emit("RST a")
        self.emit("ADD d")
        self.emit("SHL a")
        self.emit("SWP d")

        # c /= 2
        self.emit("RST a")
        self.emit("ADD c")
        self.emit("SHR a")
        self.emit("SWP c")
        self.emit(f"JUMP {start}")

        self.emit(f"{end}:", label=True)
        self.emit("RST a")
        self.emit("ADD e")

    def _gen_divmod(self, node1, node2, quotient=True):
        self.gen_expression(node1)
        self.emit("SWP c") # Dividend
        self.gen_expression(node2)
        self.emit("SWP d") # Divisor

        final_lbl = f"dm_end_{id(node1)}_{id(node2)}"

        # Check div 0: if divisor is zero, jump to handler that zeroes results
        self.emit("RST a")
        self.emit("ADD d")
        div_zero_label = f"div_zero_{id(node1)}_{id(node2)}"
        self.emit(f"JZERO {div_zero_label}")

        # Initialize quotient accumulator
        self.emit("RST e")

        loop = f"dm_loop_{id(node1)}"
        self.emit(f"{loop}:", label=True)
        
        # While c >= d
        self.emit("RST a")
        self.emit("ADD c")
        self.emit("SUB d") 
        # If c < d, c-d=0 (saturated). We need strictly less.
        # If c < d, we are done.
        # But VM SUB returns 0 for equal AND less.
        # Check d - c. If > 0 => d > c => done.
        self.emit("SWP f") # Save c-d check
        self.emit("RST a")
        self.emit("ADD d")
        self.emit("SUB c")
        self.emit(f"JPOS {final_lbl}") 
        # If d > c, jump. If d == c, result 0, no jump.
        
        # Find largest shift
        self.emit("RST a")
        self.emit("ADD d")
        self.emit("SWP f") # f = current divisor (d * 2^k)
        self.emit("RST g")
        self.emit("INC g") # g = multiple (2^k)
        
        grow = f"dm_grow_{id(node1)}"
        self.emit(f"{grow}:", label=True)
        
        self.emit("RST a")
        self.emit("ADD f")
        self.emit("SHL a")
        self.emit("SWP b") # b = f * 2
        
        # If b > c, stop growing
        self.emit("RST a")
        self.emit("ADD b")
        self.emit("SUB c") 
        self.emit(f"JPOS {loop}_sub")
        
        # Update f, g
        self.emit("RST a")
        self.emit("ADD b")
        self.emit("SWP f")
        
        self.emit("RST a")
        self.emit("ADD g")
        self.emit("SHL a")
        self.emit("SWP g")
        self.emit(f"JUMP {grow}")
        
        self.emit(f"{loop}_sub:", label=True)
        # c -= f
        self.emit("RST a")
        self.emit("ADD c")
        self.emit("SUB f")
        self.emit("SWP c")
        
        # e += g
        self.emit("RST a")
        self.emit("ADD e")
        self.emit("ADD g")
        self.emit("SWP e")
        
        self.emit(f"JUMP {loop}")

        # Divisor-zero handler: place both quotient and remainder as 0
        self.emit(f"{div_zero_label}:", label=True)
        self.emit("RST e")
        self.emit("RST c")
        self.emit(f"JUMP {final_lbl}")

        # Final label: select which register (quotient or remainder) to put into a
        self.emit(f"{final_lbl}:", label=True)
        self.emit("RST a")
        if quotient:
            self.emit("ADD e")
        else:
            self.emit("ADD c")

    def gen_div(self, n1, n2):
        if isinstance(n2, tuple) and n2[0] == 'NUMBER' and self._is_power_of_two(n2[1]):
            self.gen_expression(n1)
            shift = self._power_of_two_shift(n2[1])
            for _ in range(shift):
                self.emit("SHR a")
            return
        self._gen_divmod(n1, n2, True)

    def gen_mod(self, n1, n2):
        if isinstance(n2, tuple) and n2[0] == 'NUMBER' and self._is_power_of_two(n2[1]):
            shift = self._power_of_two_shift(n2[1])
            self.gen_expression(n1)
            self.emit("SWP b")
            self.emit("RST a")
            self.emit("ADD b")
            for _ in range(shift):
                self.emit("SHR a")
            for _ in range(shift):
                self.emit("SHL a")
            self.emit("SWP c")
            self.emit("RST a")
            self.emit("ADD b")
            self.emit("SUB c")
            return
        self._gen_divmod(n1, n2, False)