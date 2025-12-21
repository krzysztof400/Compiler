from sly import Parser
from my_lexer import Lexer
from my_lexer import MyLexer

class MyParser(Parser):
    tokens = MyLexer.tokens

    @_('procedures main')
    def program_all(self, p):
        return ('PROGRAM', p.procedures, p.main)

    # --- PROCEDURES ---
    @_('procedures PROCEDURE proc_head IS declarations IN commands END')
    def procedures(self, p):
        p.procedures.append(('PROCEDURE', p.proc_head, p.declarations, p.commands))
        return p.procedures

    @_('procedures PROCEDURE proc_head IS IN commands END')
    def procedures(self, p):
        p.procedures.append(('PROCEDURE', p.proc_head, [], p.commands))
        return p.procedures

    @_('')
    def procedures(self, p):
        return []

    @_('')
    def proc_head(self, p):
        return []

    # --- DECLARATIONS ---
    @_('declarations "," PID')
    def declarations(self, p):
        p.declarations.append(('VAR', p.PID))
        return p.declarations
    
    @_('PID')
    def declarations(self, p):
        return [('VAR', p.PID)]
    
    @_('commands command')
    def commands(self, p):
        return p.commands + p.command
    
    @_('command')
    def commands(self, p):
        return p.command
    
    @_('READ identifier ";"')
    def command(self, p):
        return ('READ', p.identifier)
    
    @_('WRITE value ";"')
    def command(self, p):
        return ('WRITE', p.value)

    @_('NUM')
    def value(self, p):
        return ('NUMBER', p.NUM)
    
    @_('PID')
    def value(self, p):
        return ('IDENTIFIER', p.PID)
    
    @_('PID')
    def identifier(self, p):
        return ('IDENTIFIER', p.PID)

    # @_('value + value;')
    # def expression(self, p):
    #     return ('ADD', p.value0, p.value1)
    
    # @_('NUMBER')
    # def value(self, p):
    #     return ('NUMBER', p.NUMBER)
    
    # @_('IDENTIFIER')
    # def value(self, p):
    #     return ('IDENTIFIER', p.IDENTIFIER)
    
    @_('PROGRAM IS declarations IN commands END')
    def main(self, p):
        return ('MAIN', p.declarations, p.commands)
    
    def error(self, p):
        if p:
            print(f"Syntax error at token {p.type}, line {p.lineno}, value {p.value}")
            exit(1)
        else:
            print("ERRORROROROR: EOF")
            exit(1)