import abc
import dataclasses as dc
from typing import Optional
from bxerrors import Range


# ===============   Building Block   =========
@dc.dataclass
class AST(abc.ABC):
    position: Optional[Range]

    @abc.abstractmethod
    def generate_TAC(self):
        return

@dc.dataclass
class Statement(AST):
    @abc.abstractmethod
    def generate_TAC(self):
        return

@dc.dataclass
class Expression(AST):
    @abc.abstractmethod
    def generate_TAC(self):
        return

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
    lvalue: Name
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

    def generate_TAC(self):
        return self.value
    

@dc.dataclass
class EUnOp(Expression):
    unop: str
    rvalue: Expression

    def generate_TAC(self):
        return 
    

@dc.dataclass
class EBinOp(Expression):
    binop: str
    lvalue: Expression
    rvalue: Expression
    

@dc.dataclass
class EPar(Expression):
    value: Expression
    
    
        

