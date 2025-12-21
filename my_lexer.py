from sly import Lexer

class MyLexer(Lexer):
    tokens = { PID, NUM, ASSIGN, NEQ, GEQ, LEQ, 
               IF, THEN, ELSE, ENDIF, WHILE, DO, ENDWHILE,
               REPEAT, UNTIL, FOR, FROM, TO, DOWNTO, ENDFOR,
               PROCEDURE, PROGRAM, IS, IN, END, READ, WRITE }
    
    ignore = ' \t'
    
    literals = { '+', '-', '*', '/', '%', ';', ',', '(', ')', '[', ']', ':', '=', '<', '>' }
    ASSIGN = ':='
    NEQ = '!='
    GEQ = '>='
    LEQ = '<='
    
    PID = '[_A-Za-z]+'
    
    PID['PROCEDURE'] = PROCEDURE
    PID['IF'] = IF
    PID['PROGRAM'] = PROGRAM
    PID['IS'] = IS
    PID['IN'] = IN
    PID['END'] = END
    PID['READ'] = READ
    PID['WRITE'] = WRITE
    PID['THEN'] = THEN
    PID['ELSE'] = ELSE
    PID['ENDIF'] = ENDIF
    PID['WHILE'] = WHILE
    PID['DO'] = DO
    PID['ENDWHILE'] = ENDWHILE
    PID['REPEAT'] = REPEAT
    PID['UNTIL'] = UNTIL
    PID['FOR'] = FOR
    PID['FROM'] = FROM
    PID['TO'] = TO
    PID['DOWNTO'] = DOWNTO
    PID['ENDFOR'] = ENDFOR
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