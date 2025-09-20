
import ply.yacc as yacc
from bxlexer import Lexer
from bxast import *

from bxerrors import DefaultReporter, Range, Reporter
#import bxast # We will write this module later

class Parser:
    UNIOP = {
        '-' : 'opposite'        ,
        '~' : 'bitwise-negation',
        '!' : 'boolean-not'     ,
    }

    BINOP = {
        '+'     : 'addition'               ,
        '-'     : 'subtraction'            ,
        '*'     : 'multiplication'         ,
        '/'     : 'division'               ,
        '%'     : 'modulus'                ,
        '>>'    : 'logical-right-shift'    ,
        '<<'    : 'logical-left-shift'     ,
        '&'     : 'bitwise-and'            ,
        '|'     : 'bitwise-or'             ,
        '^'     : 'bitwise-xor'            ,
        '=='    : 'boolean-eq'             ,
        '!='    : 'boolean-noneq'          ,    
        '<'     : 'boolean-less'           ,    
        '<='    : 'boolean-lesseq'         ,    
        '>'     : 'boolean-great'          ,    
        '>='    : 'boolean-greateq'        ,    
        '&&'    : 'boolean-and'            ,
        '||'    : 'boolean-or'
    }

    start = 'program'

    tokens = Lexer.tokens

    precedence = (
        ('left',    'BOOLOR'),
        ('left',    'BOOLAND'),
        ('left',    'OR'),
        ('left',    'XOR'),
        ('left',    'AND'),
        ('nonassoc',    'BOOLEQ', 'NEQ'),
        ('nonassoc',    'LT', 'LEQ', 'GT','GEQ'),
        ('left',    'RSHIFT','LSHIFT'),
        ('left',    'PLUS', 'MINUS'), # left-assoc., low precedence
        ('left',    'TIMES', 'DIV', 'MODULUS'), # left-assoc., medium precedence
        ('right',   'UMINUS', 'BOOLNOT'), # right-assoc., high precedence
        ('right',   'TILDE')
    )

    def __init__(self, reporter: Reporter):
        self.lexer    = Lexer(reporter = reporter)
        self.parser   = yacc.yacc(module = self)
        self.reporter = reporter
        self.names    = {} 

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
        p[0] = EVar(position=self._position(p), type=None, name=p[1])

    def p_expr_true(self, p):
        """expr : TRUE"""
        p[0] = ENum(position=self._position(p), type=None, value=1)

    def p_expr_false(self, p):
        """expr : FALSE"""
        p[0] = ENum(position=self._position(p), type=None, value=0)

    def p_expr_number(self, p):
        """expr : NUMBER"""
        if not (- (2**63)<=p[1] < 2**63):
            self.reporter(
                f"Number _{p[1]}_ too big! -- skipping",
                position = self._position(p)
            )
        p[0] = ENum(position=self._position(p), type=None, value=int(p[1]))

    def p_expression_uniop(self, p):
        """expr : MINUS expr %prec UMINUS
                | TILDE expr %prec TILDE
                | BOOLNOT expr %prec BOOLNOT"""
        etype = None
        match p[1]:
            case '-':
                if p[2].type == 'int':
                    etype = 'int'
            case '~':
                if p[2].type == 'int':
                    etype = 'int'
            case '!':
                if p[2].type == 'bool':
                    etype = 'bool'
        if etype is None:
            self.reporter(
                f"Type error: unary operator `{p[1]}' cannot be applied to type `{p[2].type}'"+
                    " -- skipping",
                position = self._position(p)
            )
            etype = 'error'
        p[0] = EUnOp(
            self._position(p), type=None,
            unop=self.UNIOP[p[1]],
            rvalue=p[2]
        )

    def p_expression_binop(self, p):
        """expr : expr PLUS     expr
                | expr MINUS    expr
                | expr TIMES    expr
                | expr DIV      expr
                | expr MODULUS  expr
                | expr AND      expr
                | expr OR       expr
                | expr XOR      expr
                | expr LSHIFT   expr
                | expr RSHIFT   expr
                | expr BOOLEQ   expr
                | expr NEQ      expr
                | expr LT       expr
                | expr LEQ      expr
                | expr GT       expr
                | expr GEQ      expr
                | expr BOOLAND  expr
                | expr BOOLOR   expr
                """
        match p[2]:
            case 'PLUS' | 'MINUS' | 'TIMES' | 'DIV' | 'MODULUS' | 'AND'\
                  | 'OR' | 'XOR' | 'LSHIFT' | 'RSHIFT':
                if p[1].type != 'int' or p[3].type != 'int':
                    self.reporter(
                        f"Type error: binary operator `{p[2]}' cannot be applied to types "+
                        f"`{p[1].type}' and `{p[3].type}' -- skipping",
                        position = self._position(p)
                    )
                    etype = 'error'
                else:
                    etype = 'int'
            case 'BOOLEQ' | 'NEQ' | 'LT' | 'LEQ' | 'GT' | 'GEQ' | 'BOOLAND' | 'BOOLOR':
                if p[1].type != 'bool' or p[3].type != 'bool':
                    self.reporter(
                        f"Type error: binary operator `{p[2]}' cannot be applied to types "+
                        f"`{p[1].type}' and `{p[3].type}' -- skipping",
                        position = self._position(p)
                    )
                    etype = 'error'
                else:
                    etype = 'bool'
        p[0] = EBinOp(
            position=self._position(p), type=None,
            binop=self.BINOP[p[2]],
            lvalue=p[1], rvalue=p[3]
        )

    def p_expr_parens(self, p):
        """expr : LPAREN expr LPAREN"""
        p[0] = p[2]

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
            name=p[1],
            rvalue=p[3]
        )

    def p_stmt_print(self, p):
        """stmt : PRINT LPAREN expr RPAREN SEMICOLON"""
        p[0] = SPrint(self._position(p), value=p[3])

    def p_stmt_vardecl(self, p):
        """stmt :   VAR name EQUALS expr COLON INT SEMICOLON
                |   VAR name EQUALS expr COLON BOOL SEMICOLON"""
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
            rvalue=p[4]
        )

    def p_stmt_block(self,p):
        """stmt :   block"""
        p[0]=p[1]

    def p_stmt_ifelse(self, p):
        """stmt : ifelse"""
        p[0]=p[1]

    def p_stmt_while(self,p):
        """stmt : WHILE LPAREN expr RPAREN block"""
        p[0] = SWhile(
            self._position(p),
            condition=p[3],
            body=SBlock(
                position=self._position(p),
                statements=p[5]
            )
        )

    def p_stmt_jump(self, p):
        """stmt :   BREAK       SEMICOLON
                |   CONTINUE    SEMICOLON"""
        if p[1] == 'break':
            p[0] = SBreak(self._position(p))
        else:
            p[0] = SContinue(self._position(p))

    def p_ifelse(self,p):
        """ifelse :   IF LPAREN expr RPAREN block ifrest"""
        p[0] = SIfElse(
            self._position(p),
            condition=p[3],
            if_block=SBlock(
                position=self._position(p),
                statements=p[5]
            ),
            else_block=p[6] if len(p) > 6 else None
        )
        

    def p_ifrest(self, p):
        """ifrest   :   
                        | ELSE ifelse
                        | ELSE block"""
        if len(p) == 1: # empty case
            p[0] = None
        else: # nonempty case
            p[0] = p[2]


    def p_program(self, p):
        """program : DEF MAIN LPAREN RPAREN block"""
        p[0] = p[5]

    def p_stmt_s(self, p):
        """stmts   :
                    | stmts stmt"""
        if len(p) == 1: # empty case
            p[0] = []
        else: # nonempty case
            p[0] = p[1]
            p[0].append(p[2])

    def p_block(self, p):
        """block : LCB stmts RCB"""
        p[0] = p[2]

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

