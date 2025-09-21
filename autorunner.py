import sys
import os

EXAMPLE_PATH = "../starter/examples/"

def get_file_names():
    """
    Get a list of .bx files in the EXAMPLE_PATH directory.
    """
    try:
        return [f for f in os.listdir(EXAMPLE_PATH) if os.path.isfile(os.path.join(EXAMPLE_PATH, f))]
    except FileNotFoundError:
        print(f"Error: Directory '{EXAMPLE_PATH}' does not exist.", file=sys.stderr)
        return []

def compile_and_run(filename: str):
    """
    Compile and run a .bx file.
    """
    if not filename.endswith('.bx'):
        print(f"Error: File '{filename}' is not a .bx file.", file=sys.stderr)
        return
    filepath = os.path.join(EXAMPLE_PATH, filename)
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
    files = get_file_names()
    if not files:
        print("No .bx files found to process.", file=sys.stderr)
        sys.exit(1)
    for file in files:
        print(f"Processing file: {file}")
        compile_and_run(file)
        print("-" * 40)