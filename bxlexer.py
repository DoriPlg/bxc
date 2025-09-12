import ply.lex as lex
import re
import bisect

from bxerrors import Range, Reporter

class Lexer:
    keywords = {
        x: x.upper() for x in (
            'def'  ,
            'int'  ,
            'main' ,
            'print',
            'var'  ,
        )
    }
    
    tokens = (
        'IDENT' ,               # : str
        'NUMBER',               # : int

        # Punctuation
        'LPAREN'   ,
        'RPAREN'   ,
        'LCB'   ,
        'RCB'   ,
        'COLON'    ,
        'SEMICOLON',

        'AND'      ,
        'MINUS'     ,
        'EQUALS'       ,
        'RSHIFT'     ,
        'XOR'      ,
        'LSHIFT'     ,
        'MODULUS'    ,
        'OR'     ,
        'PLUS'     ,
        'DIV'    ,
        'TIMES'     ,
        'TILDE'     ,
    ) + tuple(keywords.values())

    t_LPAREN    = re.escape('(')
    t_RPAREN    = re.escape(')')
    t_LCB    = re.escape('{')
    t_RCB    = re.escape('}')
    t_COLON     = re.escape(':')
    t_SEMICOLON = re.escape(';')

    t_AND       = re.escape('&')
    t_MINUS      = re.escape('-')
    t_EQUALS        = re.escape('=')
    t_RSHIFT      = re.escape('>>')
    t_XOR       = re.escape('^')
    t_LSHIFT      = re.escape('<<')
    t_MODULUS     = re.escape('%')
    t_OR      = re.escape('|')
    t_PLUS      = re.escape('+')
    t_DIV     = re.escape('/')
    t_TIMES      = re.escape('*')
    t_TILDE      = re.escape('~')

    t_ignore = ' \t'            # Ignore all whitespaces
    t_ignore_comment = r'//.*'
    # Functions beginning with ‘t_' define complex token processing code.
    # The docstrings of the functions contain the regexp that is matched for the token
    def __init__(self, reporter: Reporter):
        self.lexer    = lex.lex(module = self)
        self.reporter = reporter
        self.bol      = [0]

    def column_of_pos(self, pos: int) -> int:
        assert(0 <= pos)
        return pos - self.bol[bisect.bisect_right(self.bol, pos)-1]
    
    
    def t_IDENT(self, t):
        r'[A-Za-z_][A-Za-z0-9_]*' # docstring contains the regexp
        t.type = self.keywords.get(t.value, 'IDENT')
        return t
    
    def t_NUMBER(self, t):
        r'[1-9][0-9]*|0'
        t.value = int(t.value)
        return t

    # error handling with t_error()
    def t_error(self, t):
        position = Range.of_position(t.lineno, self.column_of_pos(t.lexpos))
        self.reporter(
            f"illegal character: `{t.value[0]}' -- skipping",
            position = position,
        )
        t.lexer.skip(1)
    
    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)
        self.bol.append(t.lexer.lexpos)
    # no return, signifying ignore
    # This will use Python introspection (reflection) to find out all the
    # ‘tokens' and ‘t_stuff' in this module and create a suitable lexer from i