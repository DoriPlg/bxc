
import ply.yacc as yacc
from bxlexer import Lexer
from bxast import *
from bxmunch import TopDownMunch #,BottomUpMuch

from bxerrors import DefaultReporter, Range, Reporter
#import bxast # We will write this module later

class Parser:
    UNIOP = {
        '-' : 'opposite'        ,
        '~' : 'bitwise-negation',
        '!' : 'boolean-not'     ,
    }

    BINOP = {
        '+'  : 'addition'                 ,
        '-'  : 'subtraction'              ,
        '*'  : 'multiplication'           ,
        '/'  : 'division'                 ,
        '%'  : 'modulus'                  ,
        '>>' : 'logical-right-shift'      ,
        '<<' : 'logical-left-shift'       ,
        '&'  : 'bitwise-and'              ,
        '|'  : 'bitwise-or'               ,
        '^'  : 'bitwise-xor'              ,
    }

    start = 'program'

    names = {}

    tokens = Lexer.tokens

    precedence = (
        ('left', 'OR'),
        ('left', 'XOR'),
        ('left','AND'),
        ('left', 'RSHIFT','LSHIFT'),
        ('left', 'PLUS', 'MINUS'), # left-assoc., low precedence
        ('left', 'TIMES', 'DIV', 'MODULUS'), # left-assoc., medium precedence
        ('right', 'UMINUS'), # right-assoc., high precedence
        ('right','TILDE')
    )

    def __init__(self, reporter: Reporter):
        self.lexer    = Lexer(reporter = reporter)
        self.parser   = yacc.yacc(module = self)
        self.reporter = reporter

    def parse(self, program: str):
        with self.reporter.checkpoint() as checkpoint:
            ast = self.parser.parse(
                program,
                lexer    = self.lexer.lexer,
                tracking = True,
            )

            return ast if checkpoint else None
        
    def _position(self, p) -> Range:
        n = len(p) - 1
        return Range(
            start = (p.linespan(1)[0], self.lexer.column_of_pos(p.lexspan(1)[0])    ),
            end   = (p.linespan(n)[1], self.lexer.column_of_pos(p.lexspan(n)[1]) + 1),
        )

    ## Every parser function is written with a ‘p_' prefix.
    ## The docstring of the function is the portion of the grammar it handles
    def p_name(self, p):
        """name : IDENT"""
        p[0] = Name(position=self._position(p), name=p[1])

    def p_expr_ident(self, p):
        """expr : name"""
        p[0] = EVar(position=self._position(p), name=p[1])
        
        
    def p_expr_number(self, p):
        """expr : NUMBER"""
        p[0] = ENum(position=self._position(p),value=int(p[1]))

    def p_expression_uniop(self, p):
        """expr : MINUS expr %prec UMINUS
                | TILDE expr %prec TILDE"""
        p[0] = EUnOp(
            self._position(p),
            unop=self.UNIOP[p[1]],
            rvalue=p[2]
        )

    def p_expression_binop(self, p):
        """expr : expr PLUS     expr
                | expr MINUS     expr
                | expr TIMES    expr
                | expr DIV    expr
                | expr MODULUS    expr
                | expr AND      expr
                | expr OR     expr
                | expr XOR      expr
                | expr LSHIFT     expr
                | expr RSHIFT     expr"""
        p[0] = EBinOp(
            self._position(p),
            binop=self.BINOP[p[2]],
            lvalue=p[1],
            rvalue=p[3]
        )

    def p_expr_parens(self, p):
        """expr : LPAREN expr LPAREN"""
        p[0] = EPar(self._position(p), value=p[2])

    def p_stmt_assign(self, p):
        """stmt : name EQUALS expr SEMICOLON"""
        var_name = p[1].name
        if (var_name not in self.names.keys()):
            self.reporter(
                f"Undeclared usage of var `{var_name}' -- skipping",
                position = self._position(p)
            )
        p[0] = SAssignment(
            self._position(p),
            lvalue=p[1],
            rvalue=p[3]
        )

    def p_stmt_print(self, p):
        """stmt : PRINT LPAREN expr RPAREN SEMICOLON"""
        p[0] = SPrint(self._position(p), value=p[3])

    def p_stmt_vardecl(self, p):
        """stmt : VAR name EQUALS expr COLON INT SEMICOLON"""
        var_name = p[2].name
        if var_name in self.names.keys():
            self.reporter(
                f"Double declare of var `{var_name}' -- skipping",
                position = self._position(p)
            )
        self.names[var_name] = p[6]
        p[0] = SVarDecl(
            self._position(p),
            name=p[2],
            type=p[6],
            init=p[4]
        )

    def p_program(self, p):
        """program : DEF MAIN LPAREN RPAREN LCB stmts RCB"""
        p[0] = p[6]

    def p_stmt_s(self, p):
        """stmts   :
                    | stmts stmt"""
        if len(p) == 1: # empty case
            p[0] = []
        else: # nonempty case
            p[0] = p[1]
            p[0].append(p[2])

    def p_error(self, p):
        if p:
            position = Range.of_position(
                p.lineno,
                self.lexer.column_of_pos(p.lexpos),
            )

            self.reporter(
                f'syntax error',
                position = position,
            )
            #self.parser.errok()
        else:
            self.reporter('syntax error at end of file')





# =========================================================
import sys

def _test_parser():
    if len(sys.argv)-1 != 1:
        print(f"Usage: {sys.argv[0]} [filename.bx...]", file = sys.stderr)
        exit(1)

    with open(sys.argv[1], "r") as stream:
        contents = stream.read()
    reporter = DefaultReporter(source = contents)
    tree = Parser(reporter).parse(contents)
    if reporter.nerrors:
        sys.exit(1)
    return TopDownMunch(tree)

if __name__=="__main__":
    _test_parser()