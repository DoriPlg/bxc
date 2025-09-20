from bxast import *
from bxerrors import Reporter

class SymbolTable:
    def __init__(self):
        self.scopes = [{}]  # Stack of symbol tables for nested scopes
    
    def declare(self, name: str, var_type: str, position: Range):
        if name in self.scopes[-1]:
            return False  # Already declared in current scope
        self.scopes[-1][name] = {'type': var_type, 'position': position}
        return True
    
    def lookup(self, name: str):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None
    
    def push_scope(self):
        self.scopes.append({})
    
    def pop_scope(self):
        self.scopes.pop()

class TypeChecker:
    def __init__(self, reporter: Reporter):
        self.reporter = reporter
        self.symbol_table = SymbolTable()
    
    def check(self, ast):
        self.visit(ast)
        return self.reporter.nerrors == 0
    
    def visit(self, node):
        method_name = f'visit_{type(node).__name__}'
        method = getattr(self, method_name, self.generic_visit)
        return method(node)
    
    def visit_SVarDecl(self, node):
        # Check if variable already declared
        if not self.symbol_table.declare(node.name.name, node.type, node.position):
            self.reporter(
                f"Variable '{node.name.name}' already declared",
                position=node.position
            )
        
        # Check initializer type
        init_type = self.visit(node.rvalue)
        if init_type != node.type:
            self.reporter(
                f"Type mismatch: cannot initialize {node.type} with {init_type}",
                position=node.position
            )
    
    def visit_EVar(self, node):
        var_info = self.symbol_table.lookup(node.name.name)
        if var_info is None:
            self.reporter(
                f"Undeclared variable '{node.name.name}'",
                position=node.position
            )
            return 'error'
        return var_info['type']