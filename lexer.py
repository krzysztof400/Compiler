from sly import Lexer

class Lexer(Lexer):
    tokens = { PID, NUM, ASSIGN, NEQ, GEQ, LEQ, 
               IF, THEN, ELSE, ENDIF, WHILE, DO, ENDWHILE,
               REPEAT, UNTIL, FOR, FROM, TO, DOWNTO, ENDFOR,
               proc_head, PROGRAM, IS, IN, END, READ, WRITE }
    
    ignore = ' \t'
    
    literals = { '+', '-', '*', '/', '%', ';', ',', '(', ')', '[', ']', ':' }
    ASSIGN = ':='
    NEQ = '!='
    GEQ = '>='
    LEQ = '<='
    
    PID = '[_a-z]+'
    
    PID['PROCEDURE'] = proc_head
    PID['IF'] = IF
    PID['PROGRAM'] = PROGRAM

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