from sly import Lexer

class MyLexer(Lexer):
    tokens = {
        PID, NUM, ASSIGN, NEQ, GEQ, LEQ,
        IF, THEN, ELSE, ENDIF, WHILE, DO, ENDWHILE,
        REPEAT, UNTIL, FOR, FROM, TO, DOWNTO, ENDFOR,
        PROCEDURE, PROGRAM, IS, IN, END, READ, WRITE,
        INPUT, OUTPUT, ARRAY
    }

    literals = { '+', '-', '*', '/', '%', ';', ',', '(', ')', '[', ']', ':', '=', '<', '>' }

    ASSIGN = r':='
    NEQ    = r'!='
    GEQ    = r'>='
    LEQ    = r'<='

    IF        = r'IF'
    THEN      = r'THEN'
    ELSE      = r'ELSE'
    ENDIF     = r'ENDIF'
    WHILE     = r'WHILE'
    DOWNTO    = r'DOWNTO'
    DO        = r'DO'
    ENDWHILE  = r'ENDWHILE'
    REPEAT    = r'REPEAT'
    UNTIL     = r'UNTIL'
    FOR       = r'FOR'
    FROM      = r'FROM'
    TO        = r'TO'
    ENDFOR    = r'ENDFOR'
    PROCEDURE = r'PROCEDURE'
    PROGRAM   = r'PROGRAM'
    IS        = r'IS'
    IN        = r'IN'
    END       = r'END'
    READ      = r'READ'
    WRITE     = r'WRITE'

    INPUT     = r'I'
    OUTPUT    = r'O'
    ARRAY     = r'T'

    PID = r'[_a-z]+'

    ignore = ' \t'

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

    def error(self, t):
        print(f"Illegal character '{t.value[0]}' at line {self.lineno}")
        self.index += 1