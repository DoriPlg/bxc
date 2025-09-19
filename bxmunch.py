# To clear vision from no docstrings, extra spaces
# pylint: disable=[C0115, C0303]     
from bxast import AST
from bxerrors import DefaultReporter, Range, Reporter
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
    def __init__(self, tree: AST, reporter : Reporter):
        self.tree = tree
        self.reporter = reporter
        self.temp_counter = 0
        self.label_counter = 0
        self.instructions = []
        self.vars_temps = [{}]  # Map variable names to their current temp names
        self.loop_stack = []  # Stack to manage loop labels for break/continue 

    def new_temp(self) -> str:
        """Generate a new temporary variable name"""
        temp_name = f"%{self.temp_counter}"
        self.temp_counter += 1
        return temp_name
    
    def fresh_label(self, base: str = "L") -> str:
        """Generate a new unique label name"""
        label_name = f"%.{base}{self.label_counter}"
        self.label_counter += 1
        return label_name
    
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
        self.reporter(f"No visitor method for {type(node).__name__}", position=node.position)
        exit(1)

    def munch(self):
        """Generate TAC JSON from the AST"""
        instructions = self.generate_code()
        return {
            "proc": "main",
            "body": instructions if len(instructions) > 0 else [{"opcode": "nop", "args": [], "result": None}]
        }



    #    =============  Statement Visitors ===================== 
    def visit_SVarDecl(self, node):
        """Visit a variable declaration statement"""
        self.handle_decl_or_assign(node, declare=True)

    def visit_SAssignment(self, node):
        """Visit an assignment statement"""
        self.handle_decl_or_assign(node, declare=False)

    def handle_decl_or_assign(self, node, declare: bool):
        """Handle both variable declarations and assignments.
        If `assign` is True, it's an assignment; otherwise, it's a declaration."""
        if declare:
            if node.name.name in self.vars_temps[-1]:
                self.reporter(
                    f"Double declare of var `{node.name.name}' -- skipping",
                    position = node.position
                )
                return
            self.vars_temps[-1][node.name.name] = self.new_temp()
        try:
            self.assign_or_declare(node, self.find_variable_temp(node.name.name))
        except ValueError:
            self.reporter(
                f"Undeclared usage of var `{node.name.name}' -- skipping",
                position = node.position
            )

    def visit_SBlock(self, node):
        """Visit a block statement"""
        self.vars_temps.append({})
        for stmt in node.statements:
            self.visit(stmt)
        self.vars_temps.pop()

    def visit_SIfElse(self, node):
        """Visit an if-else statement"""
        cond_temp = self.visit(node.condition)
        else_label = self.fresh_label("else")
        end_label = self.fresh_label("end_if")

        self.emit("jeq", [cond_temp], else_label)
        self.visit(node.if_block)
        self.emit("jmp", [], end_label)

        self.emit("label", [], else_label)
        if node.else_block:
            self.visit(node.else_block)
        self.emit("label", [], end_label)

    def visit_SWhile(self, node):
        """Visit a while statement"""
        start_label = self.fresh_label("start_while")
        end_label = self.fresh_label("end_while")
        self.loop_stack.append((start_label, end_label))
        self.emit("label", [], start_label)
        cond_temp = self.visit(node.condition)
        self.emit("jeq", [cond_temp], end_label)
        self.visit(node.body)
        self.emit("jmp", [], start_label)
        self.emit("label", [], end_label)

    def visit_SBreak(self, node):
        """Visit a break statement"""
        if not self.loop_stack:
            self.reporter(
                "Break statement not within a loop -- skipping",
                position = node.position
            )
            return
        _, end_label = self.loop_stack[-1]
        self.emit("jmp", [], end_label)
    
    def visit_SContinue(self, node):
        """Visit a continue statement"""
        if not self.loop_stack:
            self.reporter(
                "Continue statement not within a loop -- skipping",
                position = node.position
            )
            return
        start_label, _ = self.loop_stack[-1]
        self.emit("jmp", [], start_label)
    # ================  Methods that must be overridden by subclasses ==========
    
    @abstractmethod
    def emit(self, opcode: str, args: list, result: str = None):
        """Emit a TAC instruction"""
        pass
    @abstractmethod
    def assign_or_declare(self, node, temp: str):
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


    def find_variable_temp(self, var_name: str) -> str:
        """Find the temp associated with a variable name in the current scope."""
        for scope in reversed(self.vars_temps):
            if var_name in scope:
                return scope[var_name]
        raise ValueError(f"Variable '{var_name}' not declared")
    

            
class TopDownMunch(Munch):
    """A simple top-down AST muncher that generates three-address code (TAC)"""

    def emit(self, instruction: str, args: list = [], result: str = None):
        self.instructions.append({
            "opcode": instruction,
            "args": args,
            "result": result
        })

    # ===============  Statement Visitors ============

    def assign_or_declare(self, node, temp):
        """
        Handle both variable declarations and assignments.
        If `assign` is True, it's an assignment; otherwise, it's a declaration."""
        rvalue_temp = self.visit(node.rvalue)
        self.emit("copy", [rvalue_temp], temp)

    def visit_SPrint(self, node):
        value_temp = self.visit(node.value)
        self.emit("print", [value_temp])



    # ================  Expression Visitors ==========

    def visit_EVar(self, node):
        try :
            return self.find_variable_temp(node.name.name)
        except ValueError:
            self.reporter(
                f"Undeclared usage of var `{node.name.name}' -- skipping",
                position = node.position
            )
            return self.new_temp()  # Return a dummy temp to continue processing
    
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
        match node.binop:
            case 'boolean-and':
                t1, t2 = self.new_temp(), self.new_temp()
                end_label = self.fresh_label("end_and")
                self.emit("const", [1], t1)  # Assume true
                self.emit("const", [1], t2)  # Assume true
                self.emit("copy", self.visit(node.lvalue), t1)
                self.emit("jeq", [t1], end_label)
                self.emit("copy", self.visit(node.rvalue), t2)
                self.emit("label", [], end_label)
                self.emit("and", [t1, t2], t1)
                return t1
            case 'boolean-or':
                t1, t2 = self.new_temp(), self.new_temp()
                end_label = self.fresh_label("end_or")
                self.emit("const", [0], t1)  # Assume false
                self.emit("const", [0], t2)  # Assume false
                self.emit("copy", self.visit(node.lvalue), t1)
                self.emit("jne", [t1], end_label)
                self.emit("copy", self.visit(node.rvalue), t2)
                self.emit("label", [], end_label)
                self.emit("or", [t1, t2], t1)
                return t1
            case _:
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

    def visit(self, node):
        result = super().visit(node)
        temp, instr = result if isinstance(result, tuple) else (result, [])
        if not instr:
            self.reporter(
                f"No instructions generated for {type(node).__name__},"+
                "check visitor method", position=node.position
            )
        return temp, instr

    # ===============  Statement Visitors ============

    def assign_or_declare(self, node, temp):
        """
        Handle both variable declarations and assignments.
        If `assign` is True, it's an assignment; otherwise, it's a declaration."""
        rvalue_temp, rvalue_instr = self.visit(node.rvalue)
        instr = rvalue_instr + [{
            "opcode": "copy",
            "args": [rvalue_temp],
            "result": temp
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
        try :
            return self.find_variable_temp(node.name.name),[]
        except ValueError:
            self.reporter(
                f"Undeclared usage of var `{node.name.name}' -- skipping",
                position = node.position
            )
            return self.new_temp(),[]  # Return a dummy temp to continue processing
    
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
        match node.binop:
            case 'boolean-and':
                t1, t2 = self.new_temp(), self.new_temp()
                end_label = self.fresh_label("end_and")
                instr = [
                    {"opcode": "const", "args": [1], "result": t1},  # Assume true
                    {"opcode": "const", "args": [1], "result": t2}   # Assume true
                ]
                left_temp, left_instr = self.visit(node.lvalue)
                instr += left_instr + [{"opcode": "copy", "args": [left_temp], "result": t1}]
                instr += [{"opcode": "jeq", "args": [t1], "result": end_label}]
                right_temp, right_instr = self.visit(node.rvalue)
                instr += right_instr + [{"opcode": "copy", "args": [right_temp], "result": t2}]
                instr += [{"opcode": "label", "args": [], "result": end_label}]
                instr += [{"opcode": "and", "args": [t1, t2], "result": t1}]
                return t1,instr
            case 'boolean-or':
                t1, t2 = self.new_temp(), self.new_temp()
                end_label = self.fresh_label("end_or")
                instr = [
                    {"opcode": "const", "args": [0], "result": t1},  # Assume false
                    {"opcode": "const", "args": [0], "result": t2}   # Assume false
                ]
                left_temp, left_instr = self.visit(node.lvalue)
                instr += left_instr + [{"opcode": "copy", "args": [left_temp], "result": t1}]
                instr += [{"opcode": "jne", "args": [t1], "result": end_label}]
                right_temp, right_instr = self.visit(node.rvalue)
                instr += right_instr + [{"opcode": "copy", "args": [right_temp], "result": t2}]
                instr += [{"opcode": "label", "args": [], "result": end_label}]
                instr += [{"opcode": "or", "args": [t1, t2], "result": t1}]
                return t1,instr
            case _:
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
        