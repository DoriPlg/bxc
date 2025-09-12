import abc
import dataclasses as dc
from typing import Optional
from bxerrors import Range


# ===============   Building Block   =========
@dc.dataclass
class AST(abc.ABC):
    position: Optional[Range]


@dc.dataclass
class Statement(AST):
    pass

@dc.dataclass
class Expression(AST):
    pass

@dc.dataclass
class Name(AST):
    name: str


# ===============  Statements    ============
@dc.dataclass
class SVarDecl(Statement):
    name: Name
    type: str
    init: Expression


@dc.dataclass
class SAssignment(Statement):
    name: Name
    rvalue: Expression


@dc.dataclass
class SPrint(Statement):
    value: Expression


# ===============   Expressions      ==========
@dc.dataclass
class EVar(Expression):
    name: Name
    

@dc.dataclass
class ENum(Expression):
    value: int
    

@dc.dataclass
class EUnOp(Expression):
    unop: str
    rvalue: Expression

    

@dc.dataclass
class EBinOp(Expression):
    binop: str
    lvalue: Expression
    rvalue: Expression
    

@dc.dataclass
class EPar(Expression):
    value: Expression
    
    
        

