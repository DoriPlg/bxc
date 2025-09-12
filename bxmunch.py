# To clear vision from no docstrings, extra spaces
# pylint: disable=[C0115, C0303]     
from bxast import AST
from abc import abstractmethod


op_map = {
    'opposite': 'neg',
    'bitwise-negation': 'not'
    # ,'boolean-not': '!'
}

op_map = {
    'addition': 'add',
    'subtraction': 'sub',
    'multiplication': 'mul',
    'division': 'div',
    'modulus': 'mod',
    'bitwise-and': 'and',
    'bitwise-or': 'or',
    'bitwise-xor': 'xor',
    'logical-left-shift': 'shl',
    'logical-right-shift': 'shr'
}
        

class Munch:
    def __init__(self, tree: AST):
        self.tree = tree
        self.temp_counter = 0
        self.instructions = []
        self.vars_temps = {}  # Map variable names to their current temp names

    def new_temp(self) -> str:
        """Generate a new temporary variable name"""
        temp_name = f"%{self.temp_counter}"
        self.temp_counter += 1
        return temp_name
    
    def generate_code(self):
        """Main entry point for code generation"""
        if isinstance(self.tree, list):  # list of statements
            for stmt in self.tree:
                self.visit(stmt)
        else:
            self.visit(self.tree)
        return self.instructions
        
    def visit(self, node):
        """Dispatch method for visiting AST nodes"""
        method_name = f'visit_{type(node).__name__}'
        method = getattr(self, method_name, self.generic_visit)
        return method(node)
    
    def generic_visit(self, node):
        """Default visitor for unhandled node types"""
        raise NotImplementedError(f"No visitor method for {type(node).__name__}")

    def visit_SVarDecl(self, node):
        """Visit a variable declaration statement"""
        self.assign_or_declare(node, declare=True)

    def visit_SAssignment(self, node):
        """Visit an assignment statement"""
        self.assign_or_declare(node, declare=False)

    def munch(self):
        """Generate TAC JSON from the AST"""
        instructions = self.generate_code()
        return {
            "proc": "main",
            "body": instructions if len(instructions) > 0 else [{"opcode": "nop", "args": [], "result": None}]
        }

    # ================  Methods that must be overridden by subclasses ==========
    
    @abstractmethod
    def emit(self, opcode: str, args: list, result: str = None):
        """Emit a TAC instruction"""
        pass
    @abstractmethod
    def assign_or_declare(self, node, declare: bool):
        """Handle both variable declarations and assignments.
        If `assign` is True, it's an assignment; otherwise, it's a declaration."""
        pass
    @abstractmethod
    def visit_SPrint(self, node):
        """Visit a print statement"""
        pass
    @abstractmethod
    def visit_EVar(self, node):
        """Visit a variable expression"""
        pass
    @abstractmethod
    def visit_ENum(self, node):
        """Visit a numeric literal expression"""
        pass
    @abstractmethod
    def visit_EUnOp(self, node):
        """Visit a unary operation expression"""
        pass
    @abstractmethod
    def visit_EBinOp(self, node):
        """Visit a binary operation expression"""
        pass
    @abstractmethod
    def visit_EPar(self, node):
        """Visit a parenthesized expression"""
        pass

            
class TopDownMunch(Munch):
    """A simple top-down AST muncher that generates three-address code (TAC)"""

    def emit(self, instruction: str, args: list = [], result: str = None):
        self.instructions.append({
            "opcode": instruction,
            "args": args,
            "result": result
        })

    # ===============  Statement Visitors ============

    def assign_or_declare(self, node, declare: bool):
        """
        Handle both variable declarations and assignments.
        If `assign` is True, it's an assignment; otherwise, it's a declaration."""
        rvalue_temp = self.visit(node.rvalue)
        if declare:
            if node.name.name in self.vars_temps:
                raise ValueError(f"Variable '{node.name.name}' already declared")
            self.vars_temps[node.name.name] = self.new_temp()
        else:
            if node.name.name not in self.vars_temps:
                raise ValueError(f"Variable '{node.name.name}' not declared")
        self.emit("copy", [rvalue_temp], self.vars_temps[node.name.name])

    def visit_SPrint(self, node):
        value_temp = self.visit(node.value)
        self.emit("print", [value_temp])



    # ================  Expression Visitors ==========

    def visit_EVar(self, node):
        if node.name.name not in self.vars_temps:
            raise ValueError(f"Variable '{node.name.name}' not declared")
        return self.vars_temps[node.name.name]
    
    def visit_ENum(self, node):
        temp = self.new_temp()
        self.emit("const", [node.value], temp)
        return temp
    
    def visit_EUnOp(self, node):
        rvalue_temp = self.visit(node.rvalue)
        result_temp = self.new_temp()

        op = op_map.get(node.unop, node.unop)
        self.emit(op, [rvalue_temp], result_temp)
        return result_temp
    
    def visit_EBinOp(self, node):
        left_temp = self.visit(node.lvalue)
        right_temp = self.visit(node.rvalue)
        result_temp = self.new_temp()
        
        op = op_map.get(node.binop, node.binop)
        self.emit(op, [left_temp, right_temp], result_temp)
        return result_temp
    
    def visit_EPar(self, node):
        return self.visit(node.value)


class BottomUpMunch(Munch):
    """A bottom-up AST muncher that generates three-address code (TAC)"""
    def emit(self, instructions):
        self.instructions.extend(instructions)

    # ===============  Statement Visitors ============

    def assign_or_declare(self, node, declare: bool):
        """
        Handle both variable declarations and assignments.
        If `assign` is True, it's an assignment; otherwise, it's a declaration."""
        rvalue_temp, rvalue_instr = self.visit(node.rvalue)
        if declare:
            if node.name.name in self.vars_temps:
                raise ValueError(f"Variable '{node.name.name}' already declared")
            self.vars_temps[node.name.name] = self.new_temp()
        else:   
            if node.name.name not in self.vars_temps:
                raise ValueError(f"Variable '{node.name.name}' not declared")
        instr = rvalue_instr + [{
            "opcode": "copy",
            "args": [rvalue_temp],
            "result": self.vars_temps[node.name.name]
        }]
        self.emit(instr)

    def visit_SPrint(self, node):
        value_temp, value_instr = self.visit(node.value)
        instr = value_instr + [{
            "opcode": "print",
            "args": [value_temp],
            "result": None
        }]
        self.emit(instr)


    # ===============  Expression Visitors ============
    def visit_EVar(self, node):
        if node.name.name not in self.vars_temps:
            raise ValueError(f"Variable '{node.name.name}' not declared")
        return self.vars_temps[node.name.name],[]
    
    def visit_ENum(self, node):
        temp = self.new_temp()
        instr = [{
            "opcode": "const",
            "args": [node.value],
            "result": temp
        }]
        return temp,instr
    
    def visit_EUnOp(self, node):
        rvalue_temp, rvalue_instr = self.visit(node.rvalue)
        result_temp = self.new_temp()

        op = op_map.get(node.unop, node.unop)
        instr = rvalue_instr + [{
            "opcode": op,
            "args": [rvalue_temp],
            "result": result_temp
        }]
        return result_temp,instr

    def visit_EBinOp(self, node):
        left_temp, left_instr = self.visit(node.lvalue)
        right_temp, right_instr = self.visit(node.rvalue)
        result_temp = self.new_temp()
        
        op = op_map.get(node.binop, node.binop)
        instr = left_instr + right_instr + [{
            "opcode": op,
            "args": [left_temp, right_temp],
            "result": result_temp
        }]
        return result_temp,instr
    
    def visit_EPar(self, node):
        return self.visit(node.value)
        