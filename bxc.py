"""
A simple driver program to test the bx parser and AST construction."""

import sys
from bxast import *
from bxparser import Parser
from bxmunch import *
from bxerrors import DefaultReporter

def _test_parser():
    if len(sys.argv)-1 < 1:
        print(f"Usage: {sys.argv[0]} [filename.bx...]", file = sys.stderr)
        exit(1)
    filename = sys.argv[2] if len(sys.argv) > 2 else sys.argv[1]
    with open(filename, "r", encoding="UTF-8") as stream:
        contents = stream.read()
    reporter = DefaultReporter(source = contents)
    tree = Parser(reporter).parse(contents)
    if reporter.nerrors:
        sys.exit(1)
    munch_type = sys.argv[1] if len(sys.argv) > 1 else "--tmm"
    if munch_type == "--tmm":
        mm = TopDownMunch(tree)
    elif munch_type == "--bmm":
        mm = BottomUpMunch(tree)
    else:
        print(f"Unknown muncher type '{munch_type}'", file = sys.stderr)
        sys.exit(1)
    outfile = f"out/{filename.split('.')[0].split('/')[-1]}.tac.json"
    with open(outfile, "w", encoding="UTF-8") as outfile:
        import json
        json.dump(mm.munch(), outfile, indent=4)
    print(f"Wrote TAC to {outfile.name}")
    sys.exit(0)

    
if __name__=="__main__":
    _test_parser()