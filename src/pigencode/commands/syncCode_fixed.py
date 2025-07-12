import os, re, ast, traceback, json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from ..classes.argParse import ArgParse
from ..defs.logIt import printIt, lable
from ..defs.fileIO import getKeyItem

def syncCode(argParse: ArgParse):
    """
    Synchronize changes from modified Python files back to their corresponding piSeed files.
    This command analyzes changes in piClasses and piDefs directories and updates the appropriate piSeed files.
    Only syncs actual user modifications, preserving the elegance of original piSeed patterns.
    """
    args = argParse.parser.parse_args()
    theArgs = args.arguments

    if len(theArgs) > 0:
        # Sync specific file
        fileName = theArgs[0]
        syncSingleFile(fileName)
    else:
        # Sync all changed files in piClasses and piDefs directories
        syncAllChangedFiles()

def syncSingleFile(fileName: str):
    """Sync a single modified Python file back to its piSeed file"""
    try:
        filePath = Path(fileName)
        if not filePath.exists():
            # Try looking in piClasses directory first
            piClassesDir = Path("piClasses")
            if piClassesDir.exists():
                filePath = piClassesDir / fileName
                if not filePath.exists():
                    filePath = piClassesDir / f"{fileName}.py"

            # If not found in piClasses, try piDefs directory
            if not filePath.exists():
                piDefsDir = Path("piDefs")
                if piDefsDir.exists():
                    filePath = piDefsDir / fileName
                    if not filePath.exists():
                        filePath = piDefsDir / f"{fileName}.py"

        if not filePath.exists():
            printIt(f"File not found: {fileName}", lable.FileNotFound)
            return

        if not filePath.suffix == '.py':
            printIt(f"File must be a Python file: {fileName}", lable.ERROR)
            return

        # Determine if this is a class file or def file based on directory
        isDefFile = filePath.parent.name == "piDefs"

        if isDefFile:
            # Handle piDefGC file
            defName = filePath.stem
            piSeedFile = findPiDefGCSeedFile(defName)
            if not piSeedFile:
                printIt(f"Could not find piDefGC piSeed file for: {defName}", lable.WARN)
                return

            changes = syncPythonDefToSeed(filePath, piSeedFile)
        else:
            # Handle piClassGC file
            className = filePath.stem
            piSeedFile = findPiClassGCSeedFile(className)
            if not piSeedFile:
                printIt(f"Could not find piClassGC piSeed file for class: {className}", lable.WARN)
                return

            changes = syncPythonClassToSeed(filePath, piSeedFile)

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
    """Sync all changed files in the piClasses and piDefs directories"""
    try:
        totalChanges = 0
        processedFiles = 0

        # Process piClasses directory
        piClassesDir = Path("piClasses")
        if piClassesDir.exists():
            pythonFiles = list(piClassesDir.glob("*.py"))

            for pyFile in pythonFiles:
                className = pyFile.stem
                piSeedFile = findPiClassGCSeedFile(className)

                if piSeedFile:
                    changes = syncPythonClassToSeed(pyFile, piSeedFile)
                    if changes:
                        totalChanges += len(changes)
                        printIt(f"Synced {len(changes)} changes from {pyFile.name}", lable.INFO)
                    processedFiles += 1
                else:
                    printIt(f"No piClassGC piSeed file found for {className}", lable.DEBUG)

        # Process piDefs directory
        piDefsDir = Path("piDefs")
        if piDefsDir.exists():
            pythonFiles = list(piDefsDir.glob("*.py"))

            for pyFile in pythonFiles:
                defName = pyFile.stem
                piSeedFile = findPiDefGCSeedFile(defName)

                if piSeedFile:
                    changes = syncPythonDefToSeed(pyFile, piSeedFile)
                    if changes:
                        totalChanges += len(changes)
                        printIt(f"Synced {len(changes)} changes from {pyFile.name}", lable.INFO)
                    processedFiles += 1
                else:
                    printIt(f"No piDefGC piSeed file found for {defName}", lable.DEBUG)

        if processedFiles == 0:
            printIt("No Python files found in piClasses or piDefs directories", lable.WARN)
        else:
            printIt(f"Processed {processedFiles} files, made {totalChanges} total changes", lable.INFO)

    except Exception as e:
        tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
        printIt(f'syncAllChangedFiles error:\n{tb_str}', lable.ERROR)

def findPiClassGCSeedFile(className: str) -> Optional[Path]:
    """Find the piSeed file that corresponds to a given class name (piClassGC)"""
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
        printIt(f"Error finding piClassGC piSeed file for {className}: {e}", lable.ERROR)
        return None

def findPiDefGCSeedFile(defName: str) -> Optional[Path]:
    """Find the piSeed file that corresponds to a given function definition name (piDefGC)"""
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

        # Look for piSeed files that contain piDefGC for this def name
        seedFiles = list(seedPath.glob("*.pi"))

        for seedFile in seedFiles:
            try:
                with open(seedFile, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Look for piDefGC line with this def name
                    if re.search(rf'^piDefGC\s+{re.escape(defName)}\s+', content, re.MULTILINE):
                        return seedFile
            except Exception:
                continue

        return None

    except Exception as e:
        printIt(f"Error finding piDefGC piSeed file for {defName}: {e}", lable.ERROR)
        return None

def syncPythonClassToSeed(pythonFile: Path, piSeedFile: Path) -> List[str]:
    """
    Sync changes from Python class file back to piClassGC piSeed file.
    Only syncs actual user modifications, preserving elegant piSeed patterns.
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

        # Parse Python file to extract methods and code elements
        try:
            tree = ast.parse(pythonContent)
            className = pythonFile.stem

            # Generate expected default code patterns to compare against
            defaultPatterns = generateDefaultPatterns(className, seedContent)

            # Find class definition and global code
            classNode = None
            globalFunctions = []
            importStatements = []

            for node in tree.body:
                if isinstance(node, ast.ClassDef) and node.name.lower() == className.lower():
                    classNode = node
                elif isinstance(node, ast.FunctionDef):
                    # Global function
                    globalFunctions.append(node)
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    # Import statements
                    importStatements.append(node)

            if classNode:
                # Process each method in the class
                for item in classNode.body:
                    if isinstance(item, ast.FunctionDef):
                        methodName = item.name

                        if methodName == '__init__':
                            # Special handling for __init__ method - only sync if truly custom
                            initCodeElements = extractInitCode(pythonContent, item, className)

                            for codeType, codeLines in initCodeElements.items():
                                if codeLines and not isDefaultInitCode(codeType, codeLines, defaultPatterns):
                                    newSeedContent, changed = updateSeedCodeElement(
                                        seedContent, className, codeType, codeLines
                                    )
                                    if changed:
                                        seedContent = newSeedContent
                                        changes.append(f"{codeType}")

                            # Extract and sync initArguments only if they differ from elegant patterns
                            initArgs = extractInitArguments(item)
                            if initArgs and not isDefaultInitArguments(initArgs, seedContent, className):
                                newSeedContent, changed = updateSeedInitArguments(
                                    seedContent, className, initArgs
                                )
                                if changed:
                                    seedContent = newSeedContent
                                    changes.append("initArguments")
                        else:
                            # Map Python method names to piSeed code element names
                            codeElementName = mapMethodToCodeElement(methodName)
                            if codeElementName:
                                methodCode = extractMethodCode(pythonContent, item)

                                # Only sync if this is not a default generated method
                                if methodCode and not isDefaultMethodCode(methodName, methodCode, defaultPatterns):
                                    # Update piSeed file with new method code
                                    newSeedContent, changed = updateSeedCodeElement(
                                        seedContent, className, codeElementName, methodCode
                                    )
                                    if changed:
                                        seedContent = newSeedContent
                                        changes.append(f"{codeElementName} ({methodName})")

            # Handle import statements - only if they differ from existing
            if importStatements:
                fromImports, regularImports = extractImportStatements(importStatements)

                if fromImports and not isDefaultImports(fromImports, seedContent, className, 'fromImports'):
                    newSeedContent, changed = updateSeedFromImports(
                        seedContent, className, fromImports
                    )
                    if changed:
                        seedContent = newSeedContent
                        changes.append("fromImports")

                if regularImports and not isDefaultImports(regularImports, seedContent, className, 'imports'):
                    newSeedContent, changed = updateSeedImports(
                        seedContent, className, regularImports
                    )
                    if changed:
                        seedContent = newSeedContent
                        changes.append("imports")

            # Handle global functions and code - only if truly custom
            if globalFunctions:
                globalCode = []
                for func in globalFunctions:
                    funcCode = extractMethodCode(pythonContent, func)
                    globalCode.extend(funcCode)
                    globalCode.append("")  # Add blank line between functions

                if globalCode and not isDefaultGlobalCode(globalCode, defaultPatterns):
                    # Remove trailing empty line
                    if globalCode and globalCode[-1] == "":
                        globalCode.pop()

                    newSeedContent, changed = updateSeedCodeElement(
                        seedContent, className, 'globalCode', globalCode
                    )
                    if changed:
                        seedContent = newSeedContent
                        changes.append("globalCode")

            # Write updated piSeed file if changes were made
            if changes:
                with open(piSeedFile, 'w', encoding='utf-8') as f:
                    f.write(seedContent)

        except SyntaxError as e:
            printIt(f"Syntax error in Python file {pythonFile}: {e}", lable.ERROR)

    except Exception as e:
        printIt(f"Error syncing {pythonFile} to {piSeedFile}: {e}", lable.ERROR)

    return changes

def generateDefaultPatterns(className: str, seedContent: str) -> Dict[str, any]:
    """
    Generate expected default code patterns based on the piSeed configuration.
    This helps identify what is default vs custom code.
    """
    patterns = {
        'defaultStrCode': [],
        'defaultJsonCode': [],
        'defaultInitAppendCode': [],
        'initArguments': {},
        'imports': [],
        'fromImports': {}
    }

    try:
        # Extract initArguments from seed to predict default patterns
        lines = seedContent.split('\n')
        argPattern = rf'^piStructC01\s+argument\s+(\w+)\.\s*$'

        for line in lines:
            match = re.match(argPattern, line)
            if match:
                argName = match.group(1)
                patterns['initArguments'][argName] = {
                    'type': 'str',
                    'value': f'pi.piBase:{argName}'  # Default elegant pattern
                }

        # Generate expected default __str__ method pattern
        if patterns['initArguments']:
            patterns['defaultStrCode'] = [
                "def __str__(self):",
                f"    rtnStr = \"{className.title()} = {{\\n\\\"\"",
            ]

            argNames = list(patterns['initArguments'].keys())
            for i, argName in enumerate(argNames):
                if i < len(argNames) - 1:
                    patterns['defaultStrCode'].append(f"    rtnStr += f'    \\\"{argName}\\\":\\\"{{self.{argName}}}\\\",\\n'")
                else:
                    patterns['defaultStrCode'].append(f"    rtnStr += f'    \\\"{argName}\\\":\\\"{{self.{argName}}}\\\"\\n'")

            patterns['defaultStrCode'].extend([
                "    rtnStr += \"}\"",
                "    return rtnStr",
                ""
            ])

        # Generate expected default json() method pattern
        if patterns['initArguments']:
            patterns['defaultJsonCode'] = [
                "def json(self) -> dict:",
                "    rtnDict = {"
            ]

            argNames = list(patterns['initArguments'].keys())
            for i, argName in enumerate(argNames):
                if i < len(argNames) - 1:
                    patterns['defaultJsonCode'].append(f"        \"{argName}\": self.{argName},")
                else:
                    patterns['defaultJsonCode'].append(f"        \"{argName}\": self.{argName}")

            patterns['defaultJsonCode'].extend([
                "    }",
                "    return rtnDict",
                "",
                ""
            ])

    except Exception as e:
        printIt(f"Error generating default patterns: {e}", lable.DEBUG)

    return patterns

def isDefaultInitCode(codeType: str, codeLines: List[str], defaultPatterns: Dict) -> bool:
    """Check if init code is just the default pattern"""
    if codeType == 'initAppendCode':
        # Check if this is just standard parameter assignments
        for line in codeLines:
            stripped = line.strip()
            if stripped and not (stripped.startswith('self.') and '=' in stripped):
                return False  # Contains non-standard code
        return True  # Only standard assignments

    return False

def isDefaultInitArguments(initArgs: Dict, seedContent: str, className: str) -> bool:
    """Check if initArguments match the elegant piSeed patterns"""
    try:
        # Extract existing elegant patterns from seed
        lines = seedContent.split('\n')
        existingArgs = {}

        argValuePattern = rf'^piValue\s+{re.escape(className)}\.piBody:piClassGC:initArguments:(\w+):value\s+(.+)$'

        for line in lines:
            match = re.match(argValuePattern, line)
            if match:
                argName = match.group(1)
                argValue = match.group(2).strip()
                existingArgs[argName] = argValue

        # Check if current args match elegant patterns
        for argName, argInfo in initArgs.items():
            if argName in existingArgs:
                existingValue = existingArgs[argName]
                currentValue = argInfo.get('value', '""')

                # If existing uses elegant pattern (pi.piBase:argName), preserve it
                if existingValue.startswith('pi.') and ':' in existingValue:
                    return True  # Keep elegant pattern

                # If values are different, it's a real change
                if existingValue != currentValue:
                    return False

        return True  # No significant changes

    except Exception:
        return False

def isDefaultMethodCode(methodName: str, methodCode: List[str], defaultPatterns: Dict) -> bool:
    """Check if method code is just the default generated pattern"""
    if methodName == '__str__':
        defaultCode = defaultPatterns.get('defaultStrCode', [])
        return methodCode == defaultCode

    elif methodName == 'json':
        defaultCode = defaultPatterns.get('defaultJsonCode', [])
        return methodCode == defaultCode

    return False

def isDefaultImports(imports, seedContent: str, className: str, importType: str) -> bool:
    """Check if imports match what's already in the seed file"""
    try:
        lines = seedContent.split('\n')
        existingImports = []

        if importType == 'imports':
            pattern = rf'^piValueA\s+{re.escape(className)}\.piBody:piClassGC:imports\s+(.+)$'
            for line in lines:
                match = re.match(pattern, line)
                if match:
                    existingImports.append(match.group(1).strip())

            return set(imports) == set(existingImports)

        elif importType == 'fromImports':
            # More complex comparison for fromImports
            return False  # For now, always sync fromImports if they exist

    except Exception:
        return False

    return True

def isDefaultGlobalCode(globalCode: List[str], defaultPatterns: Dict) -> bool:
    """Check if global code is just default patterns"""
    # For now, assume any global code is custom
    return False

# Include all the existing helper functions from the original syncCode.py
# (extractMethodCode, updateSeedCodeElement, extractInitCode, etc.)
# These remain largely unchanged but with improved logic

def mapMethodToCodeElement(methodName: str) -> Optional[str]:
    """Map Python method names to piSeed code element names"""
    method_mapping = {
        '__str__': 'strCode',
        'json': 'jsonCode',
        '__init__': None,  # Special handling needed for init code
    }

    # Check for exact matches first
    if methodName in method_mapping:
        return method_mapping[methodName]

    # For other methods, they go into classDefCode
    if not methodName.startswith('_'):  # Skip private methods
        return 'classDefCode'

    return None

def extractMethodCode(pythonContent: str, methodNode: ast.FunctionDef) -> List[str]:
    """Extract the code lines for a method from the Python content"""
    try:
        lines = pythonContent.split('\n')
        startLine = methodNode.lineno - 1  # ast uses 1-based line numbers

        # Find the end of the method
        endLine = len(lines)

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

        # Extract method lines, preserving relative indentation
        methodLines = []
        for i in range(startLine, endLine):
            line = lines[i]
            if i == startLine:
                # First line (method definition) - remove class indentation
                methodLines.append(line[methodIndent:] if len(line) > methodIndent else line.strip())
            else:
                # Subsequent lines - preserve relative indentation
                if line.strip():  # Non-empty line
                    if len(line) > methodIndent:
                        # Remove the base method indentation, keep relative indentation
                        methodLines.append(line[methodIndent:])
                    else:
                        methodLines.append(line.strip())
                else:
                    # Empty line
                    methodLines.append("")

        return methodLines

    except Exception as e:
        printIt(f"Error extracting method code: {e}", lable.ERROR)
        return []

# Placeholder implementations for the remaining functions
# These would need to be implemented based on the original syncCode.py

def syncPythonDefToSeed(pythonFile: Path, piSeedFile: Path) -> List[str]:
    """Sync piDefGC files - placeholder implementation"""
    return []

def extractInitCode(pythonContent: str, initNode: ast.FunctionDef, className: str) -> Dict[str, List[str]]:
    """Extract init code - placeholder implementation"""
    return {'initAppendCode': []}

def extractInitArguments(initNode: ast.FunctionDef) -> Dict[str, Dict[str, str]]:
    """Extract init arguments - placeholder implementation"""
    return {}

def extractImportStatements(importNodes: List) -> Tuple[Dict[str, Dict[str, str]], List[str]]:
    """Extract import statements - placeholder implementation"""
    return {}, []

def updateSeedCodeElement(seedContent: str, className: str, codeElementName: str, methodCode: List[str]) -> Tuple[str, bool]:
    """Update seed code element - placeholder implementation"""
    return seedContent, False

def updateSeedInitArguments(seedContent: str, className: str, initArgs: Dict[str, Dict[str, str]]) -> Tuple[str, bool]:
    """Update seed init arguments - placeholder implementation"""
    return seedContent, False

def updateSeedFromImports(seedContent: str, className: str, fromImports: Dict[str, Dict[str, str]]) -> Tuple[str, bool]:
    """Update seed from imports - placeholder implementation"""
    return seedContent, False

def updateSeedImports(seedContent: str, className: str, regularImports: List[str]) -> Tuple[str, bool]:
    """Update seed imports - placeholder implementation"""
    return seedContent, False
