# To clear vision from no docstrings, extra spaces
# pylint: disable=[C0115, C0303]     
from bxast import AST


op_map = {
'opposite': '-',
'bitwise-negation': '~',
'boolean-not': '!'
}

op_map = {
'addition': '+',
'subtraction': '-',
'multiplication': '*',
'division': '/',
'modulus': '%',
'bitwise-and': '&',
'bitwise-or': '|',
'bitwise-xor': '^',
'logical-left-shift': '<<',
'logical-right-shift': '>>'
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
    
    def emit(self, instruction: str):
        """Emit a TAC instruction"""
        self.instructions.append(instruction)

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
            
class TopDownMunch(Munch):
    """A simple top-down AST muncher that generates three-address code (TAC)"""

    # ===============  Statement Visitors ============
    def visit_SVarDecl(self, node):
        """Handle variable declarations"""
        init_temp = self.visit(node.init)
        self.vars_temps[node.name.name] = self.new_temp()
        self.emit(f"{self.vars_temps[node.name.name]} = {init_temp}")

    def visit_SAssignment(self, node):
        """Handle assignments"""
        rvalue_temp = self.visit(node.rvalue)
        if node.lvalue.name not in self.vars_temps:
            raise ValueError(f"Variable '{node.lvalue.name}' not declared")
        self.emit(f"{self.vars_temps[node.lvalue.name]} = {rvalue_temp}")

    def visit_SPrint(self, node):
        """Handle print statements"""
        value_temp = self.visit(node.value)
        self.emit(f"print {value_temp}")



    # ================  Expression Visitors ==========

    def visit_EVar(self, node):
        """Handle variable expressions"""
        if node.name.name not in self.vars_temps:
            raise ValueError(f"Variable '{node.name.name}' not declared")
        return self.vars_temps[node.name.name]
    
    def visit_ENum(self, node):
        """Handle number expressions"""
        temp = self.new_temp()
        self.emit(f"{temp} = {node.value}")
        return temp
    
    def visit_EUnOp(self, node):
        """Handle unary operations"""
        rvalue_temp = self.visit(node.rvalue)
        result_temp = self.new_temp()

        op = op_map.get(node.unop, node.unop)
        self.emit(f"{result_temp} = {op}{rvalue_temp}")
        return result_temp
    
    def visit_EBinOp(self, node):
        """Handle binary operations"""
        left_temp = self.visit(node.lvalue)
        right_temp = self.visit(node.rvalue)
        result_temp = self.new_temp()
        
        op = op_map.get(node.binop, node.binop)
        self.emit(f"{result_temp} = {left_temp} {op} {right_temp}")
        return result_temp
    
    def visit_EPar(self, node):
        """Handle parenthesized expressions"""
        return self.visit(node.value)