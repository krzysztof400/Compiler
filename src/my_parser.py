from sly import Parser
from my_lexer import MyLexer
from schemas import SyntaxError as CompilationSyntaxError, SourceLocation

class MyParser(Parser):
    tokens = MyLexer.tokens

    # --- PROGRAM ---

    @_('procedures main')
    def program_all(self, p):
        return ('PROGRAM', p.procedures, p.main)

    # --- PROCEDURES ---

    @_('procedures PROCEDURE proc_head IS declarations IN commands END')
    def procedures(self, p):
        name, args = p.proc_head
        p.procedures.append(('PROCEDURE', name, args, p.declarations, p.commands))
        return p.procedures

    @_('procedures PROCEDURE proc_head IS IN commands END')
    def procedures(self, p):
        name, args = p.proc_head
        p.procedures.append(('PROCEDURE', name, args, [], p.commands))
        return p.procedures

    @_('')
    def procedures(self, p):
        return []

    # --- MAIN ---

    @_('PROGRAM IS declarations IN commands END')
    def main(self, p):
        return ('MAIN', p.declarations, p.commands)

    @_('PROGRAM IS IN commands END')
    def main(self, p):
        return ('MAIN', [], p.commands)

    # --- COMMANDS ---

    @_('commands command')
    def commands(self, p):
        p.commands.append(p.command)
        return p.commands

    @_('command')
    def commands(self, p):
        return [p.command]

    # --- INDIVIDUAL COMMANDS ---

    @_('identifier ASSIGN expression ";"')
    def command(self, p):
        return ('ASSIGN', p.identifier, p.expression, p.lineno)

    @_('IF condition THEN commands ELSE commands ENDIF')
    def command(self, p):
        return ('IF', p.condition, p.commands0, p.commands1, p.lineno)

    @_('IF condition THEN commands ENDIF')
    def command(self, p):
        return ('IF', p.condition, p.commands, [], p.lineno)

    @_('WHILE condition DO commands ENDWHILE')
    def command(self, p):
        return ('WHILE', p.condition, p.commands, p.lineno)

    @_('REPEAT commands UNTIL condition ";"')
    def command(self, p):
        return ('REPEAT', p.commands, p.condition, p.lineno)

    @_('FOR PID FROM value TO value DO commands ENDFOR')
    def command(self, p):
        return ('FOR_TO', p.PID, p.value0, p.value1, p.commands, p.lineno)

    @_('FOR PID FROM value DOWNTO value DO commands ENDFOR')
    def command(self, p):
        return ('FOR_DOWNTO', p.PID, p.value0, p.value1, p.commands, p.lineno)

    @_('proc_call ";"')
    def command(self, p):
        # proc_call already has lineno attached
        return p.proc_call

    @_('READ identifier ";"')
    def command(self, p):
        return ('READ', p.identifier, p.lineno)

    @_('WRITE value ";"')
    def command(self, p):
        return ('WRITE', p.value, p.lineno)

    # --- PROCEDURE HEAD & CALLS ---

    @_('PID "(" args_decl ")"')
    def proc_head(self, p):
        return (p.PID, p.args_decl)

    @_('PID "(" args ")"')
    def proc_call(self, p):
        return ('PROC_CALL', p.PID, p.args, p.lineno)

    # --- ARGUMENT DECLARATIONS ---
    # args_decl -> args_decl, PID
    #          | args_decl, ARRAY PID
    #          | args_decl, INPUT PID
    #          | args_decl, OUTPUT PID
    #          | PID
    #          | ARRAY PID
    #          | INPUT PID
    #          | OUTPUT PID

    @_('args_decl "," PID')
    def args_decl(self, p):
        p.args_decl.append(('ARG', p.PID))
        return p.args_decl

    @_('args_decl "," ARRAY PID')
    def args_decl(self, p):
        p.args_decl.append(('ARG_ARRAY', p.PID))
        return p.args_decl

    @_('args_decl "," INPUT PID')
    def args_decl(self, p):
        p.args_decl.append(('ARG_INPUT', p.PID))
        return p.args_decl

    @_('args_decl "," OUTPUT PID')
    def args_decl(self, p):
        p.args_decl.append(('ARG_OUTPUT', p.PID))
        return p.args_decl

    @_('PID')
    def args_decl(self, p):
        return [('ARG', p.PID)]

    @_('ARRAY PID')
    def args_decl(self, p):
        return [('ARG_ARRAY', p.PID)]

    @_('INPUT PID')
    def args_decl(self, p):
        return [('ARG_INPUT', p.PID)]

    @_('OUTPUT PID')
    def args_decl(self, p):
        return [('ARG_OUTPUT', p.PID)]

    # --- ARGS ---

    @_('args "," PID')
    def args(self, p):
        p.args.append(p.PID)
        return p.args

    @_('PID')
    def args(self, p):
        return [p.PID]

    # --- DECLARATIONS ---

    @_('declarations "," PID')
    def declarations(self, p):
        p.declarations.append(('VAR', p.PID, p.lineno))
        return p.declarations

    @_('declarations "," PID "[" NUM ":" NUM "]"')
    def declarations(self, p):
        p.declarations.append(('ARRAY', p.PID, p.NUM0, p.NUM1, p.lineno))
        return p.declarations

    @_('PID')
    def declarations(self, p):
        return [('VAR', p.PID, p.lineno)]

    @_('PID "[" NUM ":" NUM "]"')
    def declarations(self, p):
        return [('ARRAY', p.PID, p.NUM0, p.NUM1, p.lineno)]

    # --- EXPRESSIONS ---

    @_('value')
    def expression(self, p):
        return p.value

    @_('value "+" value')
    def expression(self, p):
        return ('ADD', p.value0, p.value1)

    @_('value "-" value')
    def expression(self, p):
        return ('SUB', p.value0, p.value1)

    @_('value "*" value')
    def expression(self, p):
        return ('MUL', p.value0, p.value1)

    @_('value "/" value')
    def expression(self, p):
        return ('DIV', p.value0, p.value1)

    @_('value "%" value')
    def expression(self, p):
        return ('MOD', p.value0, p.value1)

    # --- CONDITIONS ---

    @_('value "=" value')
    def condition(self, p):
        return ('EQ', p.value0, p.value1)

    @_('value NEQ value')
    def condition(self, p):
        return ('NEQ', p.value0, p.value1)

    @_('value ">" value')
    def condition(self, p):
        return ('GT', p.value0, p.value1)

    @_('value "<" value')
    def condition(self, p):
        return ('LT', p.value0, p.value1)

    @_('value GEQ value')
    def condition(self, p):
        return ('GEQ', p.value0, p.value1)

    @_('value LEQ value')
    def condition(self, p):
        return ('LEQ', p.value0, p.value1)

    # --- VALUES ---

    @_('NUM')
    def value(self, p):
        return ('NUMBER', p.NUM, p.lineno)

    @_('identifier')
    def value(self, p):
        return p.identifier

    # --- IDENTIFIER ---

    @_('PID')
    def identifier(self, p):
        return ('PIDENTIFIER', p.PID, p.lineno)

    @_('PID "[" PID "]"')
    def identifier(self, p):
        return ('PIDENTIFIER_WITH_PID', p.PID0, p.PID1, p.lineno)

    @_('PID "[" NUM "]"')
    def identifier(self, p):
        return ('PIDENTIFIER_WITH_NUM', p.PID, p.NUM, p.lineno)

    # --- ERROR HANDLING ---

    def error(self, p):
        if p:
            raise CompilationSyntaxError(
                f"Unexpected token {p.type} (value={p.value})",
                location=SourceLocation(p.lineno),
            )
        else:
            raise CompilationSyntaxError("Unexpected end of file")