import sys
import pprint
from my_lexer import MyLexer
from my_parser import MyParser
from semantic_analyzer import SemanticAnalyzer
from code_generator import CodeGenerator

if __name__ == '__main__':
    lexer = MyLexer()
    parser = MyParser()

    parser.debugfile = 'parser_debug.out'
    
    args = sys.argv[1:]
    verbose = False
    if "-v" in args:
        verbose = True
        parser.verbose = True
        args.remove("-v")
    
    if len(args) != 2:
        print("Usage: python compiler.py <inputfile> <outputfile> [-v]")
        sys.exit(1)
    
    input_file = args[0]
    output_file = args[1]
    
    with open(input_file, 'r') as f:
        text = f.read()
    
    if verbose:
        print("Tokens:")
        for token in lexer.tokenize(text):
            print(token)

    ast = parser.parse(lexer.tokenize(text))

    if verbose:
        print("\n\nAST:")
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(ast)
    
    
    ast = parser.parse(lexer.tokenize(text))
    if ast:
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        generator = CodeGenerator(analyzer)
        if verbose: generator.verbose = True
        generated_code = generator.generate(ast)
        with open(output_file, 'w') as f:
            f.write("\n".join(generated_code))
    else:
        print("Parsing failed; no code generated.")