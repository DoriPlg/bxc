from bxast import AST

class Munch:
    def __init__(self, tree: AST):
        self.tree = tree

class TopDownMunch(Munch):
    def __init__(self, tree):
        super().__init__(tree)
        
