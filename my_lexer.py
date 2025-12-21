from sly import Lexer

class MyLexer(Lexer):
    tokens = {  PID, NUM, ASSIGN, NEQ, GEQ, LEQ, 
                IF, THEN, ELSE, ENDIF, WHILE, DO, ENDWHILE,
                REPEAT, UNTIL, FOR, FROM, TO, DOWNTO, ENDFOR,
                PROCEDURE, PROGRAM, IS, IN, END, READ, WRITE, 
                INPUT, OUTPUT, ARRAY }
    
    ignore = ' \t'
    
    literals = { '+', '-', '*', '/', '%', ';', ',', '(', ')', '[', ']', ':', '=', '<', '>'}
    ASSIGN = ':='
    NEQ = '!='
    GEQ = '>='
    LEQ = '<='


    IF, THEN, ELSE, ENDIF, WHILE, DO, ENDWHILE, REPEAT, UNTIL, FOR, FROM, TO, DOWNTO, ENDFOR, PROCEDURE, PROGRAM, IS, IN, END, READ, WRITE = map(r'{}'.format, [
        'IF', 'THEN', 'ELSE', 'ENDIF', 'WHILE', 'DO', 'ENDWHILE', 'REPEAT', 'UNTIL', 'FOR', 'FROM', 'TO', 'DOWNTO', 'ENDFOR', 
        'PROCEDURE', 'PROGRAM', 'IS', 'IN', 'END', 'READ', 'WRITE'
    ])

    PID = '[_a-z]+'

    # This must stay at the end to avoid conflicts
    INPUT = r'I'
    OUTPUT = r'O'
    ARRAY = r'T'
    

    @_(r'\d+')
    def NUM(self, t):
        t.value = int(t.value)
        return t

    @_(r'\#.*')
    def ignore_comment(self, t):
        pass

    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += len(t.value)