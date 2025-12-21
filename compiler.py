import sys
import pprint
from my_lexer import MyLexer
from my_parser import MyParser

if __name__ == '__main__':
    lexer = MyLexer()
    parser = MyParser()

    parser.debugfile = 'parser_debug.out'
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    with open(input_file, 'r') as f:
        text = f.read()
    
    tokens = list(lexer.tokenize(text)) #TODO: remove list and then prints below, and iter in tokens for production

    print("Tokens:")

    for token in tokens:
        print(token)

    print("\n\nAST:")

    ast = parser.parse(iter(tokens))

    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(ast)
    
    # TODO: Run Semantic Analysis on ast
    # TODO: Run Code Generator on ast -> returns list of strings (ASM commands)
    
    ast = parser.parse(lexer.tokenize(text))
    if ast:
        # TODO: code generation
        # generated_code = generate_code(ast)
        with open(output_file, 'w') as f:
            f.write("\n".join(generated_code))
    else:
        print("Parsing failed; no code generated.")