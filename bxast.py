import abc
import dataclasses as dc
from typing import Optional, Union
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
    type: Optional[str]

@dc.dataclass
class Name(AST):
    name: str


# ===============  Statements    ============
@dc.dataclass
class SVarDecl(Statement):
    name: Name
    type: str
    rvalue: Expression

@dc.dataclass
class SAssignment(Statement):
    name: Name
    rvalue: Expression

@dc.dataclass
class SPrint(Statement):
    value: Expression

@dc.dataclass
class SBlock(Statement):
    statements: list[Statement]

@dc.dataclass
class SWhile(Statement):
    condition: Expression
    body: SBlock

@dc.dataclass
class SIfElse(Statement):
    condition: Expression
    if_block: SBlock
    else_block: Optional[Union['SIfElse', SBlock]]


@dc.dataclass
class SBreak(Statement):
    pass
@dc.dataclass
class SContinue(Statement):
    pass

# ===============   Expressions      ==========
@dc.dataclass
class EVar(Expression):
    name: Name

@dc.dataclass
class ENum(Expression):
    value: int

@dc.dataclass
class EBool(Expression):
    value: bool

@dc.dataclass
class EUnOp(Expression):
    unop: str
    rvalue: Expression

@dc.dataclass
class EBinOp(Expression):
    binop: str
    lvalue: Expression
    rvalue: Expression

# @dc.dataclass
# class EPar(Expression):
#     value: Expression
