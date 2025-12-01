from sly import Parser

class Parser(Parser):
    tokens = Lexer.tokens

    @_('procedures main')
    def program_all(self, p):
        return ('PROGRAM', p.procedures, p.main)

    @_('procedures PROCEDURE proc_head IS declarations IN commands END')
    def procedures(self, p):
        return [('PROCEDURE', p.proc_head, p.declarations, p.commands)] + p.procedures

    @_('')
    def procedures(self, p):
        return []

    @_('PROGRAM IS declarations IN commands END')
    def main(self, p):
        return ('MAIN', p.declarations, p.commands)