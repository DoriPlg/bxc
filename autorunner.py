import sys
import os

EXAMPLE_PATH = "../starter/examples/"
REGRESSION_PATH = "../starter/regression/"

def get_file_names(prefix: str = EXAMPLE_PATH) -> list[str]:
    """
    Get a list of .bx files in the EXAMPLE_PATH directory.
    """
    try:
        return [f for f in os.listdir(prefix) if os.path.isfile(os.path.join(prefix, f))]
    except FileNotFoundError:
        print(f"Error: Directory '{prefix}' does not exist.", file=sys.stderr)
        return []

def compile_and_run(filename: str, prefix: str = EXAMPLE_PATH):
    """
    Compile and run a .bx file.
    """
    if not filename.endswith('.bx'):
        print(f"Error: File '{filename}' is not a .bx file.", file=sys.stderr)
        return
    filepath = os.path.join(prefix, filename)
    if not os.path.isfile(filepath):
        print(f"Error: File '{filepath}' does not exist.", file=sys.stderr)
        return
    try:
        os.system(f"python3 bxc.py {filepath}")
        s_file = f"out/{filename.split('.')[-2]}.s"
        if os.path.isfile(s_file):
            os.system(f"gcc -c {s_file} -o out/{filename.split('.')[-2]}.o")
            os.system(f"gcc out/{filename.split('.')[-2]}.o -o out/{filename.split('.')[-2]}")
            os.system(f"./out/{filename.split('.')[-2]}")
        else:
            print(f"Error: Assembly file '{s_file}' was not generated.", file=sys.stderr)
    except Exception as e:
        print(f"Error during compilation or execution: {e}", file=sys.stderr)



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} (p/n) \\epsilon|[filename.bx...]", file=sys.stderr)
        print("  p: process all good examples", file=sys.stderr)
        print("  n: process all bad examples", file=sys.stderr)
        print("  If filenames are provided, process those instead of all examples.", file=sys.stderr)
        sys.exit(1)
    prefix = EXAMPLE_PATH if sys.argv[1] == 'p' else REGRESSION_PATH if sys.argv[1] == 'n' else None
    if prefix is None:
        print("Error: First argument must be 'p' or 'n'.", file=sys.stderr)
        sys.exit(1)
    if sys.argv[2:]:
        files = sys.argv[1:]
    else:
        files = get_file_names(prefix)
    if not files:
        print("No .bx files found to process.", file=sys.stderr)
        sys.exit(1)
    for file in files:
        print(f"Processing file: {file}")
        compile_and_run(file, prefix)
        print("-" * 40)
