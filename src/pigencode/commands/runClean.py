from pathlib import Path
from json import dumps
from .rmGC import rmGC
from .syncCode import syncDirectory
from .germSeed import germAllSeedFiles
from .genCode import genCodeFile

import black
from black import FileMode
from black.report import NothingChanged
from difflib import unified_diff


def runClean(argParse):
    rmGC(argParse)
    options = {}
    targetPath = Path("testCode/pi")
    options["dest_dir"] = "holdCode/pi"
    syncDirectory(targetPath, options)
    
    germAllSeedFiles()
    savedCodeFiles = genCodeFile()
    #print(dumps(savedCodeFiles,indent=2))

    for file_path in savedCodeFiles.values():
        theDiff = get_black_diff(file_path)
        print(theDiff)
        if format_python_file(file_path):
            exit()
        exit()


def get_black_diff(file_path):
    """
    Returns the diff of a Python file after black formatting, as a string.
    Returns None if no changes are needed.
    """
    file_path = Path(file_path)
    try:
        # Read the original content
        src_code = file_path.read_text(encoding="utf-8")

        # Format the code using Black
        formatted_code = black.format_file_contents(
            src_code, fast=True, mode=FileMode(line_length=88)
        )

        # Split the original and formatted code into lines
        original_lines = src_code.splitlines(keepends=True)
        formatted_lines = formatted_code.splitlines(keepends=True)

        # Generate the unified diff
        diff = unified_diff(
            original_lines,
            formatted_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}"
        )
        return "".join(diff)

    except NothingChanged:
        return None
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None
    
def format_python_file(file_path) -> bool:
    """Formats a single Python file using the black library."""
    file_path = Path(file_path)

    try:
        # Read the content of the file
        code_content = file_path.read_text(encoding="utf-8")

        # Format the code using Black's internal API
        formatted_code = black.format_file_contents(
            code_content,
            fast=True,  # Use the fastest mode
            mode=FileMode(line_length=88)  # Set the line length (default is 88)
        )

        # Write the formatted code back to the file
        file_path.write_text(formatted_code, encoding="utf-8")
        print(f"✅ Successfully formatted: {file_path}")
        return True
    except NothingChanged:
        print(f"✅ Nothing to format: {file_path}")
        return False
    except Exception as e:
        print(f"❌ Failed to format {file_path}: {e}")
        return False
