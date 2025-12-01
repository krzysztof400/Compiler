import sys
from lexer import Lexer
from parser import Parser

if __name__ == '__main__':
    lexer = Lexer()
    parser = Parser()
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    with open(input_file, 'r') as f:
        text = f.read()
    
    ast = parser.parse(lexer.tokenize(text))
    
    # Run Semantic Analysis on ast
    # Run Code Generator on ast -> returns list of strings (ASM commands)
    
    with open(output_file, 'w') as f:
        f.write("\n".join(generated_code))