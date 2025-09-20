"""
A simple driver program to test the bx parser and AST construction."""

import sys
import json
from bxast import *
from bxparser import Parser
from bxmunch import *
from bxerrors import DefaultReporter

def _run_parser():
    if len(sys.argv)-1 < 1:
        print(f"Usage: {sys.argv[0]} [filename.bx...]", file = sys.stderr)
        exit(1)
    filename = sys.argv[2] if len(sys.argv) > 2 else sys.argv[1]
    outfile = f"out/{filename.split('.')[0].split('/')[-1]}.tac.json"
    with open(filename, "r", encoding="UTF-8") as stream:
        contents = stream.read()

    reporter = DefaultReporter(source = contents)
    tree = parse(contents, reporter)

    munch_for_type(tree, reporter)

    munch_type = sys.argv[1] if len(sys.argv) > 2 else "--tmm"
    mm = make_muncher(tree, reporter, munch_type)

    munch_gen_json(mm, outfile)
    sys.exit(0 if reporter.nerrors == 0 else 1)

def parse(contents: str, reporter: Reporter):
    """Parse the given program contents and return the AST.
    If there are any errors, report them using the given reporter and return exit.
    """
    tree = Parser(reporter).parse(contents)
    if reporter.nerrors:
        sys.exit(1)
    return tree

def make_muncher(tree: AST, reporter: Reporter, munch_type: str) -> Munch:
    """
    Create and return a muncher of the given type.
    If the type is unknown, report an error using the given reporter and return exit.
    """
    mm = TopDownMunch(tree, reporter) if munch_type == "--tmm" else \
        BottomUpMunch(tree, reporter) if munch_type == "--bmm" else  None
    if mm is None:
        print(f"Unknown muncher type '{munch_type}'", file = sys.stderr)
        sys.exit(1)
    return mm

def munch_for_type(tree: AST, reporter: Reporter):
    """
    Perform type checking and inference on the AST.
    If there are any errors, report them using the given reporter and return exit.
    """
    TypeMunch(tree, reporter).generate_code()
    if reporter.nerrors:
        sys.exit(1)


def munch_gen_json(mm: Munch, outfile: str):
    with open(outfile, "w", encoding="UTF-8") as outfile:
        json.dump(mm.munch(), outfile, indent=4)
    print(f"Wrote TAC to {outfile.name}")

if __name__=="__main__":
    _run_parser()
