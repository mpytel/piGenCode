import os, re, ast, traceback
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from ..classes.argParse import ArgParse
from ..defs.logIt import printIt, lable
from ..defs.piRCFile import getKeyItem

def syncCode(argParse: ArgParse):
    """
    Synchronize changes from modified Python files back to their corresponding piSeed files.
    This command analyzes changes in piClasses directory and updates the appropriate piSeed files.
    """
    args = argParse.parser.parse_args()
    theArgs = args.arguments

    if len(theArgs) > 0:
        # Sync specific file
        fileName = theArgs[0]
        syncSingleFile(fileName)
    else:
        # Sync all changed files in piClasses directory
        syncAllChangedFiles()

def syncSingleFile(fileName: str):
    """Sync a single modified Python file back to its piSeed file"""
    try:
        filePath = Path(fileName)
        if not filePath.exists():
            # Try looking in piClasses directory
            piClassesDir = Path("piClasses")
            if piClassesDir.exists():
                filePath = piClassesDir / fileName
                if not filePath.exists():
                    filePath = piClassesDir / f"{fileName}.py"

        if not filePath.exists():
            printIt(f"File not found: {fileName}", lable.FileNotFound)
            return

        if not filePath.suffix == '.py':
            printIt(f"File must be a Python file: {fileName}", lable.ERROR)
            return

        # Extract class name from filename
        className = filePath.stem

        # Find corresponding piSeed file
        piSeedFile = findPiSeedFile(className)
        if not piSeedFile:
            printIt(f"Could not find piSeed file for class: {className}", lable.WARN)
            return

        # Perform the sync
        changes = syncPythonToSeed(filePath, piSeedFile)
        if changes:
            printIt(f"Synced {len(changes)} changes from {filePath.name} to {piSeedFile.name}", lable.INFO)
            for change in changes:
                printIt(f"  Updated: {change}", lable.DEBUG)
        else:
            printIt(f"No changes needed for {filePath.name}", lable.INFO)

    except Exception as e:
        tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
        printIt(f'syncSingleFile error:\n{tb_str}', lable.ERROR)

def syncAllChangedFiles():
    """Sync all changed files in the piClasses directory"""
    try:
        piClassesDir = Path("piClasses")
        if not piClassesDir.exists():
            printIt("piClasses directory not found", lable.FileNotFound)
            return

        pythonFiles = list(piClassesDir.glob("*.py"))
        if not pythonFiles:
            printIt("No Python files found in piClasses directory", lable.WARN)
            return

        totalChanges = 0
        processedFiles = 0

        for pyFile in pythonFiles:
            className = pyFile.stem
            piSeedFile = findPiSeedFile(className)

            if piSeedFile:
                changes = syncPythonToSeed(pyFile, piSeedFile)
                if changes:
                    totalChanges += len(changes)
                    printIt(f"Synced {len(changes)} changes from {pyFile.name}", lable.INFO)
                processedFiles += 1
            else:
                printIt(f"No piSeed file found for {className}", lable.DEBUG)

        printIt(f"Processed {processedFiles} files, made {totalChanges} total changes", lable.INFO)

    except Exception as e:
        tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
        printIt(f'syncAllChangedFiles error:\n{tb_str}', lable.ERROR)

def findPiSeedFile(className: str) -> Optional[Path]:
    """Find the piSeed file that corresponds to a given class name"""
    try:
        # Get piSeeds directory
        seedDirName = "piSeeds"
        seedPath = Path(getKeyItem("piSeedsDir", seedDirName))

        if not seedPath.exists():
            # Try current directory
            cwd = Path.cwd()
            if cwd.name == seedDirName:
                seedPath = cwd
            else:
                seedPath = cwd / seedDirName

        if not seedPath.exists():
            return None

        # Look for piSeed files that contain piClassGC for this class
        seedFiles = list(seedPath.glob("*.pi"))

        for seedFile in seedFiles:
            try:
                with open(seedFile, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Look for piClassGC line with this class name
                    if re.search(rf'^piClassGC\s+{re.escape(className)}\s+', content, re.MULTILINE):
                        return seedFile
            except Exception:
                continue

        return None

    except Exception as e:
        printIt(f"Error finding piSeed file for {className}: {e}", lable.ERROR)
        return None

def syncPythonToSeed(pythonFile: Path, piSeedFile: Path) -> List[str]:
    """
    Sync changes from Python file back to piSeed file.
    Returns list of changes made.
    """
    changes = []

    try:
        # Read the Python file and extract method/function bodies
        with open(pythonFile, 'r', encoding='utf-8') as f:
            pythonContent = f.read()

        # Read the piSeed file
        with open(piSeedFile, 'r', encoding='utf-8') as f:
            seedContent = f.read()

        # Parse Python file to extract methods
        try:
            tree = ast.parse(pythonContent)
            className = pythonFile.stem

            # Find class definition
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name.lower() == className.lower():
                    # Process each method in the class
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            methodName = item.name
                            methodCode = extractMethodCode(pythonContent, item)

                            if methodCode:
                                # Update piSeed file with new method code
                                newSeedContent, changed = updateSeedMethod(
                                    seedContent, className, methodName, methodCode
                                )
                                if changed:
                                    # print('methodName:', methodName)
                                    # print('seedContent:', seedContent)
                                    # print('newSeedContent:', newSeedContent)
                                    seedContent = newSeedContent
                                    changes.append(f"{methodName}()")

            # Write updated piSeed file if changes were made
            if changes:
                print('update', piSeedFile)
                with open(piSeedFile, 'w', encoding='utf-8') as f:
                    f.write(seedContent)

        except SyntaxError as e:
            printIt(f"Syntax error in Python file {pythonFile}: {e}", lable.ERROR)

    except Exception as e:
        printIt(f"Error syncing {pythonFile} to {piSeedFile}: {e}", lable.ERROR)

    return changes

def extractMethodCode(pythonContent: str, methodNode: ast.FunctionDef) -> List[str]:
    """Extract the code lines for a method from the Python content"""
    try:
        lines = pythonContent.split('\n')
        startLine = methodNode.lineno - 1  # ast uses 1-based line numbers

        # Find the end of the method by looking for the next method or class end
        endLine = len(lines)
        currentIndent = None

        # Get the indentation of the method definition
        defLine = lines[startLine]
        methodIndent = len(defLine) - len(defLine.lstrip())

        # Find where this method ends
        for i in range(startLine + 1, len(lines)):
            line = lines[i]
            if line.strip():  # Non-empty line
                lineIndent = len(line) - len(line.lstrip())
                # If we find a line with same or less indentation than method def, method is done
                if lineIndent <= methodIndent:
                    endLine = i
                    break

        # Extract method lines
        methodLines = []
        for i in range(startLine, endLine):
            line = lines[i]
            # Remove the class-level indentation to get the method body
            if line.strip():
                if len(line) > methodIndent:
                    methodLines.append(line[methodIndent:])
                else:
                    methodLines.append(line.strip())
            else:
                methodLines.append("")

        return methodLines

    except Exception as e:
        printIt(f"Error extracting method code: {e}", lable.ERROR)
        return []

def updateSeedMethod(seedContent: str, className: str, methodName: str, methodCode: List[str]) -> Tuple[str, bool]:
    """
    Update a method in the piSeed file content.
    Returns (updated_content, was_changed)
    """
    try:
        lines = seedContent.split('\n')
        newLines = []
        changed = False
        inMethod = False
        methodPattern = rf'^piValueA\s+{re.escape(className)}\.piBody:piClassGC:{re.escape(methodName)}Code\s+'

        i = 0
        while i < len(lines):
            line = lines[i]

            # Check if this is the start of our method
            if re.match(methodPattern, line):
                inMethod = True
                # Skip all existing method lines
                while i < len(lines) and (inMethod or re.match(methodPattern, lines[i])):
                    if i + 1 < len(lines):
                        nextLine = lines[i + 1]
                        # Check if next line is also part of this method
                        if re.match(methodPattern, nextLine):
                            i += 1
                            continue
                        else:
                            inMethod = False
                    i += 1

                # Add new method code
                for codeLine in methodCode:
                    newLines.append(f'piValueA {className}.piBody:piClassGC:{methodName}Code "{codeLine}"')
                changed = True
                continue
            else:
                newLines.append(line)
                i += 1

        return '\n'.join(newLines), changed

    except Exception as e:
        printIt(f"Error updating seed method: {e}", lable.ERROR)
        return seedContent, False
