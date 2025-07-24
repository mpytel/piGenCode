import sys
import os
import difflib
from pathlib import Path
from pigencode.defs.logIt import printIt, lable, cStr, color

def fileDiff(argParse):
    global commands
    args = argParse.args
    theArgs = args.arguments
    if len(theArgs) == 2:
        origFilePath = theArgs[0]
        newFilePath = theArgs[1]
        compare_python_files(origFilePath, newFilePath)

def compare_python_files(file1_path, file2_path):
    """
    Compares two Python files and prints their differences.

    Args:
        file1_path (str): The path to the first Python file (e.g., the original).
        file2_path (str): The path to the second Python file (e.g., the modified).
    """
    # 1. Validate file paths
    if not os.path.exists(file1_path):
        print(f"Error: File not found at '{file1_path}'", file=sys.stderr)
        return
    if not os.path.exists(file2_path):
        print(f"Error: File not found at '{file2_path}'", file=sys.stderr)
        return
    if not os.path.isfile(file1_path):
        print(f"Error: '{file1_path}' is not a file.", file=sys.stderr)
        return
    if not os.path.isfile(file2_path):
        print(f"Error: '{file2_path}' is not a file.", file=sys.stderr)
        return

    # 2. Read file contents as lists of lines
    try:
        with open(file1_path, 'r', encoding='utf-8') as f1:
            lines1 = f1.readlines()
        with open(file2_path, 'r', encoding='utf-8') as f2:
            lines2 = f2.readlines()
    except IOError as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        return
    except UnicodeDecodeError:
        print(f"Error: Could not decode file with UTF-8. Try a different encoding if known.", file=sys.stderr)
        return

    # 3. Generate differences using difflib.unified_diff
    # unified_diff produces a diff in the unified format, like 'diff -u'
    # 'lineterm=' is important if readlines() keeps newlines, to avoid double spacing in output.
    diff = difflib.unified_diff(
        lines1,
        lines2,
        fromfile=file1_path,
        tofile=file2_path,
        lineterm=''  # Ensures difflib doesn't add an extra newline if lines already have them
    )

    # 4. Print the differences with optional color coding
    print(f"\n--- Comparing '{file1_path}' and '{file2_path}' ---")
    has_diff = False
    for line in diff:
        has_diff = True
        # ANSI escape codes for coloring output in terminals
        if line.startswith('+'):
            print(f"\033[92m{line}\033[0m", end='')  # Green for added lines
        elif line.startswith('-'):
            print(f"\033[91m{line}\033[0m", end='')  # Red for removed lines
        elif line.startswith('@'):
            print(f"\033[94m{line}\033[0m", end='')  # Blue for hunk headers
        else:
            print(line, end='')  # Default color for context lines

    if not has_diff:
        print("No differences found.")
    print("\n" + "=" * 60 + "\n")
