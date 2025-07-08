import os, re, ast, traceback
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from ..classes.argParse import ArgParse
from ..defs.logIt import printIt, lable
from ..defs.piRCFile import getKeyItem

# Intelligent pattern detection functions
def isDefaultStrCode(methodCode: List[str], className: str, initArgs: Dict) -> bool:
    """Check if __str__ method is just the default generated pattern"""
    if not methodCode or not initArgs:
        return True
    
    # Instead of exact matching, check for standard patterns
    codeStr = '\n'.join(methodCode)
    
    # Must start with def __str__(self):
    if not codeStr.startswith('def __str__(self):'):
        return False
    
    # Must contain standard elements for all init args
    argNames = list(initArgs.keys())
    for argName in argNames:
        if f'self.{argName}' not in codeStr:
            return False  # Missing expected field
    
    # Check for custom logic indicators (excluding the method definition itself)
    # Remove the first line to avoid false positives from the method definition
    codeLines = methodCode[1:]  # Skip 'def __str__(self):'
    bodyStr = '\n'.join(codeLines)
    
    customIndicators = [
        'if ', 'for ', 'while ', 'try:', 'except:', 'with ',
        'import ', 'def ', 'class ', 'lambda', '@',
        'print(', 'input(', 'open(', 'file(', 'read(', 'write('
    ]
    
    for indicator in customIndicators:
        if indicator in bodyStr:
            return False  # Contains custom logic
    
    # Check if it's just a simple string formatting pattern
    hasRtnStr = 'rtnStr' in codeStr
    hasReturn = 'return' in codeStr
    hasFormatting = ('{' in codeStr and '}' in codeStr) or ('f"' in codeStr or "f'" in codeStr)
    
    # If it has the basic structure and no custom logic, consider it default
    return hasRtnStr and hasReturn and hasFormatting

def isDefaultJsonCode(methodCode: List[str], className: str, initArgs: Dict) -> bool:
    """Check if json() method is just the default generated pattern"""
    if not methodCode or not initArgs:
        return True
    
    codeStr = '\n'.join(methodCode)
    
    # Must start with def json(self) -> dict:
    if not codeStr.startswith('def json(self) -> dict:'):
        return False
    
    # Must contain standard elements for all init args
    argNames = list(initArgs.keys())
    for argName in argNames:
        if f'self.{argName}' not in codeStr:
            return False  # Missing expected field
    
    # Check for custom logic indicators (excluding the method definition itself)
    codeLines = methodCode[1:]  # Skip 'def json(self) -> dict:'
    bodyStr = '\n'.join(codeLines)
    
    customIndicators = [
        'if ', 'for ', 'while ', 'try:', 'except:', 'with ',
        'import ', 'def ', 'class ', 'lambda', '@',
        'print(', 'input(', 'open(', 'file(', 'read(', 'write(',
        'datetime', 'json.', 'str(', 'int(', 'float(', 'bool('
    ]
    
    for indicator in customIndicators:
        if indicator in bodyStr:
            return False  # Contains custom logic
    
    # Check if it's just a simple dict return pattern
    hasRtnDict = 'rtnDict' in codeStr or 'return {' in codeStr
    hasReturn = 'return' in codeStr
    
    # If it has the basic structure and no custom logic, consider it default
    return hasRtnDict and hasReturn

def isDefaultInitAppendCode(codeLines: List[str], initArgs: Dict) -> bool:
    """Check if initAppendCode is just standard parameter assignments"""
    if not codeLines:
        return True
    
    # Check if all lines are just standard self.param = param assignments
    standardAssignments = 0
    totalLines = 0
    
    for line in codeLines:
        stripped = line.strip()
        if stripped:
            totalLines += 1
            # Skip constructor signature lines
            if ':' in stripped and '=' in stripped and ('str' in stripped or 'int' in stripped or 'bool' in stripped):
                continue
            # Check for standard assignment pattern
            if stripped.startswith('self.') and '=' in stripped and len(stripped.split('=')) == 2:
                standardAssignments += 1
    
    # If most lines are standard assignments, consider it default
    return totalLines > 0 and standardAssignments >= (totalLines * 0.8)

def hasElegantValueReferences(seedContent: str, className: str) -> bool:
    """Check if the seed file uses elegant pi.piBase:field references"""
    lines = seedContent.split('\n')
    argValuePattern = rf'^piValue\s+{re.escape(className)}\.piBody:piClassGC:initArguments:\w+:value\s+pi\.'
    
    for line in lines:
        if re.match(argValuePattern, line):
            return True  # Found elegant reference
    
    return False

def extractInitArgsFromSeed(seedContent: str, className: str) -> Dict[str, str]:
    """Extract initArguments from seed content for pattern matching"""
    lines = seedContent.split('\n')
    initArgs = {}
    
    argPattern = rf'^piStructC01\s+argument\s+(\w+)\.\s*$'
    
    for line in lines:
        match = re.match(argPattern, line)
        if match:
            argName = match.group(1)
            initArgs[argName] = 'str'  # Default type
    
    return initArgs

def shouldPreserveElegantPattern(seedContent: str, className: str, codeType: str, codeLines: List[str]) -> bool:
    """Determine if we should preserve elegant piSeed patterns instead of syncing"""
    
    # For initAppendCode, don't sync if it's just default assignments
    if codeType == 'initAppendCode':
        initArgs = extractInitArgsFromSeed(seedContent, className)
        return isDefaultInitAppendCode(codeLines, initArgs)
    
    # For strCode/jsonCode, don't sync if they're default patterns
    if codeType == 'strCode':
        initArgs = extractInitArgsFromSeed(seedContent, className)
        return isDefaultStrCode(codeLines, className, initArgs)
    
    if codeType == 'jsonCode':
        initArgs = extractInitArgsFromSeed(seedContent, className)
        return isDefaultJsonCode(codeLines, className, initArgs)
    
    return False

def syncCode(argParse: ArgParse):
    """
    Synchronize changes from modified Python files back to their corresponding piSeed files.
    This command analyzes changes in piClasses and piDefs directories and updates the appropriate piSeed files.
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
            # Try looking in configurable piClassGCDir first
            piClassesDir = Path(getKeyItem("piClassGCDir", "piClasses"))
            if piClassesDir.exists():
                filePath = piClassesDir / fileName
                if not filePath.exists():
                    filePath = piClassesDir / f"{fileName}.py"
                
                # Also search in piClasses subdirectories
                if not filePath.exists():
                    for subdir in piClassesDir.iterdir():
                        if subdir.is_dir():
                            candidate = subdir / fileName
                            if candidate.exists():
                                filePath = candidate
                                break
                            candidate = subdir / f"{fileName}.py"
                            if candidate.exists():
                                filePath = candidate
                                break
            
            # If not found in piClasses, try configurable piDefGCDir
            if not filePath.exists():
                piDefsDir = Path(getKeyItem("piDefGCDir", "piDefs"))
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
            # Handle piClassGC file (existing logic)
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
    """Sync all changed files in the configurable piClassGCDir and piDefGCDir directories"""
    try:
        totalChanges = 0
        processedFiles = 0
        
        # Process configurable piClassGCDir directory
        piClassesDir = Path(getKeyItem("piClassGCDir", "piClasses"))
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
        
        # Process configurable piDefGCDir directory
        piDefsDir = Path(getKeyItem("piDefGCDir", "piDefs"))
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
            printIt(f"No Python files found in {piClassesDir} or {piDefsDir} directories", lable.WARN)
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
                                # Only sync if not a default pattern
                                if codeLines and not shouldPreserveElegantPattern(seedContent, className, codeType, codeLines):
                                    newSeedContent, changed = updateSeedCodeElement(
                                        seedContent, className, codeType, codeLines
                                    )
                                    if changed:
                                        seedContent = newSeedContent
                                        changes.append(f"{codeType}")
                            
                            # Extract and sync initArguments only if no elegant references exist
                            initArgs = extractInitArguments(item)
                            if initArgs and not hasElegantValueReferences(seedContent, className):
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
                                
                                # Only sync if not a default pattern
                                if methodCode and not shouldPreserveElegantPattern(seedContent, className, codeElementName, methodCode):
                                    if codeElementName == 'classDefCode':
                                        # Special handling for classDefCode - it's a dictionary of methods
                                        newSeedContent, changed = updateSeedClassDefCode(
                                            seedContent, className, methodName, methodCode
                                        )
                                    else:
                                        # Regular code elements (strCode, jsonCode, etc.)
                                        newSeedContent, changed = updateSeedCodeElement(
                                            seedContent, className, codeElementName, methodCode
                                        )
                                    
                                    if changed:
                                        seedContent = newSeedContent
                                        changes.append(f"{codeElementName} ({methodName})")
            
            # Handle import statements
            if importStatements:
                fromImports, regularImports = extractImportStatements(importStatements)
                
                if fromImports:
                    newSeedContent, changed = updateSeedFromImports(
                        seedContent, className, fromImports
                    )
                    if changed:
                        seedContent = newSeedContent
                        changes.append("fromImports")
                
                if regularImports:
                    newSeedContent, changed = updateSeedImports(
                        seedContent, className, regularImports
                    )
                    if changed:
                        seedContent = newSeedContent
                        changes.append("imports")
            
            # Handle global functions and code
            if globalFunctions:
                globalCode = []
                for func in globalFunctions:
                    funcCode = extractMethodCode(pythonContent, func)
                    globalCode.extend(funcCode)
                    globalCode.append("")  # Add blank line between functions
                
                if globalCode:
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

def syncPythonDefToSeed(pythonFile: Path, piSeedFile: Path) -> List[str]:
    """
    Sync changes from Python function definition file back to piDefGC piSeed file.
    Returns list of changes made.
    """
    changes = []
    
    try:
        # Read the Python file
        with open(pythonFile, 'r', encoding='utf-8') as f:
            pythonContent = f.read()
        
        # Read the piSeed file
        with open(piSeedFile, 'r', encoding='utf-8') as f:
            seedContent = f.read()
        
        # Parse Python file to extract elements
        try:
            tree = ast.parse(pythonContent)
            defName = pythonFile.stem
            
            # Extract different elements from the Python file
            importStatements = []
            functionDefs = {}
            constants = []
            globalCode = []
            fileComments = []
            headers = []
            
            # Process top-level nodes
            for node in tree.body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    importStatements.append(node)
                elif isinstance(node, ast.FunctionDef):
                    # Extract function definition
                    funcCode = extractMethodCode(pythonContent, node)
                    functionDefs[node.name] = funcCode
                elif isinstance(node, ast.Assign):
                    # Constants (module-level assignments)
                    constantCode = extractAssignmentCode(pythonContent, node)
                    if constantCode:
                        constants.append(constantCode)
                elif isinstance(node, ast.If) and hasattr(node.test, 'left') and hasattr(node.test.left, 'id'):
                    # Handle if __name__ == '__main__': blocks
                    if (node.test.left.id == '__name__' and 
                        hasattr(node.test.comparators[0], 's') and 
                        node.test.comparators[0].s == '__main__'):
                        globalCode.extend(extractIfMainCode(pythonContent, node))
            
            # Extract file comments and headers from the beginning of the file
            lines = pythonContent.split('\n')
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('#') and not stripped.startswith('# Module'):
                    if 'Generated from' in stripped:
                        headers.append(stripped)
                    else:
                        headers.append(stripped)
                elif stripped.startswith('"""') or stripped.startswith("'''"):
                    # Extract docstring as file comment
                    docstring = extractModuleDocstring(pythonContent)
                    if docstring:
                        fileComments.extend(docstring)
                    break
                elif stripped and not stripped.startswith('#'):
                    break
            
            # Update piSeed file with extracted elements
            
            # Update headers
            if headers:
                newSeedContent, changed = updateDefSeedHeaders(seedContent, defName, headers)
                if changed:
                    seedContent = newSeedContent
                    changes.append("headers")
            
            # Update file comments
            if fileComments:
                newSeedContent, changed = updateDefSeedFileComments(seedContent, defName, fileComments)
                if changed:
                    seedContent = newSeedContent
                    changes.append("fileComment")
            
            # Update imports
            if importStatements:
                fromImports, regularImports = extractImportStatements(importStatements)
                
                if regularImports:
                    newSeedContent, changed = updateDefSeedImports(seedContent, defName, regularImports)
                    if changed:
                        seedContent = newSeedContent
                        changes.append("imports")
                
                if fromImports:
                    newSeedContent, changed = updateDefSeedFromImports(seedContent, defName, fromImports)
                    if changed:
                        seedContent = newSeedContent
                        changes.append("fromImports")
            
            # Update constants
            if constants:
                newSeedContent, changed = updateDefSeedConstants(seedContent, defName, constants)
                if changed:
                    seedContent = newSeedContent
                    changes.append("constants")
            
            # Update function definitions
            if functionDefs:
                newSeedContent, changed = updateDefSeedFunctionDefs(seedContent, defName, functionDefs)
                if changed:
                    seedContent = newSeedContent
                    changes.append("functionDefs")
            
            # Update global code
            if globalCode:
                newSeedContent, changed = updateDefSeedGlobalCode(seedContent, defName, globalCode)
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

def updateSeedClassDefCode(seedContent: str, className: str, methodName: str, methodCode: List[str]) -> Tuple[str, bool]:
    """
    Update classDefCode in the piSeed file content.
    classDefCode should be structured as:
    piStructA00 className.piBody:piClassGC:classDefCode
    piStructL01 methodName 'Method description'
    piValueA className.piBody:piClassGC:classDefCode:methodName "code line 1"
    piValueA className.piBody:piClassGC:classDefCode:methodName "code line 2"
    Returns (updated_content, was_changed)
    """
    try:
        lines = seedContent.split('\n')
        newLines = []
        changed = False
        
        # Check if classDefCode structure exists
        structPattern = rf'^piStructA00\s+{re.escape(className)}\.piBody:piClassGC:classDefCode\s*$'
        methodStructPattern = rf'^piStructL01\s+{re.escape(methodName)}\s+'
        methodValuePattern = rf'^piValueA\s+{re.escape(className)}\.piBody:piClassGC:classDefCode:{re.escape(methodName)}\s+'
        
        hasStructure = False
        hasMethod = False
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check for classDefCode structure
            if re.match(structPattern, line):
                hasStructure = True
                newLines.append(line)
                i += 1
                continue
            
            # Check for method structure
            elif re.match(methodStructPattern, line):
                hasMethod = True
                newLines.append(line)
                i += 1
                
                # Skip existing method code lines
                while i < len(lines) and re.match(methodValuePattern, lines[i]):
                    i += 1
                
                # Add new method code
                for codeLine in methodCode:
                    escapedCode = codeLine.replace('"', '\\"')
                    newLines.append(f'piValueA {className}.piBody:piClassGC:classDefCode:{methodName} "{escapedCode}"')
                changed = True
                continue
            
            # Skip old-style classDefCode entries (without method name)
            elif re.match(rf'^piValueA\s+{re.escape(className)}\.piBody:piClassGC:classDefCode\s+".*def {re.escape(methodName)}\(', line):
                # Skip all lines for this method in old format
                while i < len(lines) and re.match(rf'^piValueA\s+{re.escape(className)}\.piBody:piClassGC:classDefCode\s+', lines[i]):
                    nextLine = lines[i]
                    # Check if this is the start of a different method
                    if 'def ' in nextLine and f'def {methodName}(' not in nextLine:
                        break
                    i += 1
                changed = True
                continue
            
            else:
                newLines.append(line)
                i += 1
        
        # If structure doesn't exist, add it
        if not hasStructure:
            # Find a good place to insert (after piClassName)
            insertIndex = len(newLines)
            classNamePattern = rf'^piValue\s+{re.escape(className)}\.piBody:piClassGC:piClassName\s+'
            
            for idx in range(len(newLines)):
                if re.match(classNamePattern, newLines[idx]):
                    insertIndex = idx + 1
                    break
            
            # Add structure
            newLines.insert(insertIndex, f'piStructA00 {className}.piBody:piClassGC:classDefCode')
            insertIndex += 1
            newLines.insert(insertIndex, f'piStructL01 {methodName} \'Custom method {methodName}\'')
            insertIndex += 1
            
            # Add method code
            for codeLine in methodCode:
                escapedCode = codeLine.replace('"', '\\"')
                newLines.insert(insertIndex, f'piValueA {className}.piBody:piClassGC:classDefCode:{methodName} "{escapedCode}"')
                insertIndex += 1
            
            changed = True
        
        # If structure exists but method doesn't, add method
        elif hasStructure and not hasMethod:
            # Find where to insert the method (after piStructA00 line)
            insertIndex = len(newLines)
            for idx in range(len(newLines)):
                if re.match(structPattern, newLines[idx]):
                    insertIndex = idx + 1
                    break
            
            # Add method structure and code
            newLines.insert(insertIndex, f'piStructL01 {methodName} \'Custom method {methodName}\'')
            insertIndex += 1
            
            for codeLine in methodCode:
                escapedCode = codeLine.replace('"', '\\"')
                newLines.insert(insertIndex, f'piValueA {className}.piBody:piClassGC:classDefCode:{methodName} "{escapedCode}"')
                insertIndex += 1
            
            changed = True
        
        return '\n'.join(newLines), changed
        
    except Exception as e:
        printIt(f"Error updating seed classDefCode: {e}", lable.ERROR)
        return seedContent, False

def updateSeedCodeElement(seedContent: str, className: str, codeElementName: str, methodCode: List[str]) -> Tuple[str, bool]:
    """
    Update a code element in the piSeed file content.
    Returns (updated_content, was_changed)
    """
    try:
        lines = seedContent.split('\n')
        newLines = []
        changed = False
        
        # Pattern to match the specific code element
        elementPattern = rf'^piValueA\s+{re.escape(className)}\.piBody:piClassGC:{re.escape(codeElementName)}\s+'
        
        # Extract existing code element content for comparison
        existingCode = []
        i = 0
        foundElement = False
        
        while i < len(lines):
            line = lines[i]
            
            # Check if this line matches our code element pattern
            if re.match(elementPattern, line):
                if not foundElement:
                    foundElement = True
                    # Extract existing code lines
                    while i < len(lines) and re.match(elementPattern, lines[i]):
                        # Extract the quoted content
                        match = re.match(rf'^piValueA\s+{re.escape(className)}\.piBody:piClassGC:{re.escape(codeElementName)}\s+"(.*)"$', lines[i])
                        if match:
                            # Unescape quotes
                            existingLine = match.group(1).replace('\\"', '"')
                            existingCode.append(existingLine)
                        i += 1
                    
                    # Compare existing code with new code
                    if existingCode != methodCode:
                        # Content is different, replace with new code
                        for codeLine in methodCode:
                            # Escape quotes in code lines
                            escapedCode = codeLine.replace('"', '\\"')
                            newLines.append(f'piValueA {className}.piBody:piClassGC:{codeElementName} "{escapedCode}"')
                        changed = True
                    else:
                        # Content is the same, keep existing code
                        for existingLine in existingCode:
                            escapedCode = existingLine.replace('"', '\\"')
                            newLines.append(f'piValueA {className}.piBody:piClassGC:{codeElementName} "{escapedCode}"')
                    continue
                else:
                    # Skip remaining lines (already processed above)
                    i += 1
                    continue
            else:
                newLines.append(line)
                i += 1
        
        # If we didn't find the element, add it at the end of the piClassGC section
        if not foundElement:
            # Find a good place to insert (after other piValueA entries for this class)
            insertIndex = len(newLines)
            classPattern = rf'^piValueA\s+{re.escape(className)}\.piBody:piClassGC:'
            
            for idx in range(len(newLines) - 1, -1, -1):
                if re.match(classPattern, newLines[idx]):
                    insertIndex = idx + 1
                    break
            
            # Insert new code element
            for codeLine in methodCode:
                escapedCode = codeLine.replace('"', '\\"')
                newLines.insert(insertIndex, f'piValueA {className}.piBody:piClassGC:{codeElementName} "{escapedCode}"')
                insertIndex += 1
            changed = True
        
        return '\n'.join(newLines), changed
        
    except Exception as e:
        printIt(f"Error updating seed code element: {e}", lable.ERROR)
        return seedContent, False

def extractInitCode(pythonContent: str, initNode: ast.FunctionDef, className: str) -> Dict[str, List[str]]:
    """
    Extract different types of init code from __init__ method.
    Returns dict with keys: preSuperInitCode, postSuperInitCode, initAppendCode
    """
    try:
        lines = pythonContent.split('\n')
        startLine = initNode.lineno - 1
        
        # Find method end
        endLine = len(lines)
        methodIndent = len(lines[startLine]) - len(lines[startLine].lstrip())
        
        for i in range(startLine + 1, len(lines)):
            line = lines[i]
            if line.strip():
                lineIndent = len(line) - len(line.lstrip())
                if lineIndent <= methodIndent:
                    endLine = i
                    break
        
        # Extract method body
        methodLines = []
        for i in range(startLine + 1, endLine):  # Skip method definition line
            line = lines[i]
            if line.strip():
                if len(line) > methodIndent + 4:  # Account for method body indentation
                    methodLines.append(line[methodIndent + 4:])
                else:
                    methodLines.append(line.strip())
            else:
                methodLines.append("")
        
        # Find super() call
        superCallIndex = -1
        for i, line in enumerate(methodLines):
            if 'super(' in line and '__init__' in line:
                superCallIndex = i
                break
        
        result = {
            'preSuperInitCode': [],
            'postSuperInitCode': [],
            'initAppendCode': []
        }
        
        if superCallIndex >= 0:
            # Class has inheritance
            result['preSuperInitCode'] = [line for line in methodLines[:superCallIndex] if line.strip()]
            
            # Find where standard assignments start (after super call)
            assignmentStart = superCallIndex + 1
            while assignmentStart < len(methodLines) and not methodLines[assignmentStart].strip().startswith('self.'):
                assignmentStart += 1
            
            # Find where standard assignments end
            assignmentEnd = assignmentStart
            while assignmentEnd < len(methodLines) and methodLines[assignmentEnd].strip().startswith('self.') and '=' in methodLines[assignmentEnd]:
                assignmentEnd += 1
            
            result['postSuperInitCode'] = [line for line in methodLines[assignmentEnd:] if line.strip()]
        else:
            # Class has no inheritance - all custom code goes to initAppendCode
            # Find where standard assignments end
            assignmentEnd = 0
            while assignmentEnd < len(methodLines) and methodLines[assignmentEnd].strip().startswith('self.') and '=' in methodLines[assignmentEnd]:
                assignmentEnd += 1
            
            result['initAppendCode'] = [line for line in methodLines[assignmentEnd:] if line.strip()]
        
        return result
        
    except Exception as e:
        printIt(f"Error extracting init code: {e}", lable.ERROR)
        return {'preSuperInitCode': [], 'postSuperInitCode': [], 'initAppendCode': []}

def extractInitArguments(initNode: ast.FunctionDef) -> Dict[str, Dict[str, str]]:
    """
    Extract constructor arguments from __init__ method.
    Returns dict with argument names as keys and type/default info as values.
    """
    try:
        arguments = {}
        
        # Process function arguments
        for arg in initNode.args.args:
            if arg.arg != 'self':  # Skip 'self' parameter
                arg_info = {
                    'type': 'str',  # Default type
                    'value': '""'   # Default value
                }
                
                # Try to infer type from type annotation
                if arg.annotation:
                    if isinstance(arg.annotation, ast.Name):
                        arg_info['type'] = arg.annotation.id
                    elif isinstance(arg.annotation, ast.Constant):
                        arg_info['type'] = str(arg.annotation.value)
                
                arguments[arg.arg] = arg_info
        
        # Process default values
        if initNode.args.defaults:
            # Map defaults to arguments (defaults apply to last N arguments)
            num_defaults = len(initNode.args.defaults)
            num_args = len(initNode.args.args) - 1  # Exclude 'self'
            
            for i, default in enumerate(initNode.args.defaults):
                arg_index = num_args - num_defaults + i
                if arg_index >= 0:
                    arg_name = initNode.args.args[arg_index + 1].arg  # +1 to skip 'self'
                    
                    if arg_name in arguments:
                        # Extract default value
                        if isinstance(default, ast.Constant):
                            if isinstance(default.value, str):
                                arguments[arg_name]['value'] = f'"{default.value}"'
                            else:
                                arguments[arg_name]['value'] = str(default.value)
                        elif isinstance(default, ast.Name):
                            arguments[arg_name]['value'] = default.id
                        elif isinstance(default, ast.List):
                            # Handle list defaults
                            list_items = []
                            for item in default.elts:
                                if isinstance(item, ast.Constant):
                                    if isinstance(item.value, str):
                                        list_items.append(f'"{item.value}"')
                                    else:
                                        list_items.append(str(item.value))
                            arguments[arg_name]['value'] = f'[{", ".join(list_items)}]'
                            arguments[arg_name]['type'] = 'list'
                        else:
                            # For complex expressions, convert to string
                            arguments[arg_name]['value'] = ast.unparse(default)
        
        return arguments
        
    except Exception as e:
        printIt(f"Error extracting init arguments: {e}", lable.ERROR)
        return {}

def updateSeedInitArguments(seedContent: str, className: str, initArgs: Dict[str, Dict[str, str]]) -> Tuple[str, bool]:
    """
    Update initArguments in the piSeed file content.
    Returns (updated_content, was_changed)
    """
    try:
        lines = seedContent.split('\n')
        newLines = []
        changed = False
        
        # Patterns to match initArguments entries
        structPattern = rf'^piStructA00\s+{re.escape(className)}\.piBody:piClassGC:initArguments\s*$'
        argStructPattern = rf'^piStructC01\s+argument\s+(\w+)\.\s*$'
        argTypePattern = rf'^piValue\s+{re.escape(className)}\.piBody:piClassGC:initArguments:(\w+):type\s+'
        argValuePattern = rf'^piValue\s+{re.escape(className)}\.piBody:piClassGC:initArguments:(\w+):value\s+'
        
        # Extract existing arguments for comparison
        existingArgs = {}
        i = 0
        foundInitArgs = False
        
        while i < len(lines):
            line = lines[i]
            
            # Check if we found the initArguments structure declaration
            if re.match(structPattern, line):
                foundInitArgs = True
                newLines.append(line)
                i += 1
                
                # Extract existing argument definitions
                while i < len(lines):
                    line = lines[i]
                    
                    # Extract argument structure declarations
                    argStructMatch = re.match(argStructPattern, line)
                    if argStructMatch:
                        argName = argStructMatch.group(1)
                        if argName not in existingArgs:
                            existingArgs[argName] = {'type': 'str', 'value': '""'}
                        i += 1
                        continue
                    
                    # Extract argument type definitions
                    argTypeMatch = re.match(argTypePattern, line)
                    if argTypeMatch:
                        argName = argTypeMatch.group(1)
                        # Extract the type part after the pattern
                        typePart = line[re.match(argTypePattern, line).end():].strip()
                        if argName not in existingArgs:
                            existingArgs[argName] = {'type': 'str', 'value': '""'}
                        existingArgs[argName]['type'] = typePart
                        i += 1
                        continue
                    
                    # Extract argument value definitions
                    argValueMatch = re.match(argValuePattern, line)
                    if argValueMatch:
                        argName = argValueMatch.group(1)
                        # Extract the value part after the pattern
                        valuePart = line[re.match(argValuePattern, line).end():].strip()
                        if argName not in existingArgs:
                            existingArgs[argName] = {'type': 'str', 'value': '""'}
                        existingArgs[argName]['value'] = valuePart
                        i += 1
                        continue
                    
                    # If we reach here, we're done with initArguments section
                    break
                
                # Compare existing arguments with new arguments
                if existingArgs != initArgs:
                    # Arguments are different, add new argument definitions
                    for argName, argInfo in initArgs.items():
                        newLines.append(f'piStructC01 argument {argName}.')
                    
                    for argName, argInfo in initArgs.items():
                        newLines.append(f'piValue {className}.piBody:piClassGC:initArguments:{argName}:type {argInfo["type"]}')
                        newLines.append(f'piValue {className}.piBody:piClassGC:initArguments:{argName}:value {argInfo["value"]}')
                    
                    changed = True
                else:
                    # Arguments are the same, keep existing definitions
                    for argName, argInfo in existingArgs.items():
                        newLines.append(f'piStructC01 argument {argName}.')
                    
                    for argName, argInfo in existingArgs.items():
                        newLines.append(f'piValue {className}.piBody:piClassGC:initArguments:{argName}:type {argInfo["type"]}')
                        newLines.append(f'piValue {className}.piBody:piClassGC:initArguments:{argName}:value {argInfo["value"]}')
                
                continue
            else:
                newLines.append(line)
                i += 1
        
        # If initArguments structure wasn't found, add it
        if not foundInitArgs and initArgs:
            # Find a good place to insert (after piClassName)
            insertIndex = len(newLines)
            classNamePattern = rf'^piValue\s+{re.escape(className)}\.piBody:piClassGC:piClassName\s+'
            
            for idx in range(len(newLines)):
                if re.match(classNamePattern, newLines[idx]):
                    insertIndex = idx + 1
                    break
            
            # Insert initArguments structure
            newLines.insert(insertIndex, f'piStructA00 {className}.piBody:piClassGC:initArguments')
            insertIndex += 1
            
            # Add argument definitions
            for argName, argInfo in initArgs.items():
                newLines.insert(insertIndex, f'piStructC01 argument {argName}.')
                insertIndex += 1
            
            for argName, argInfo in initArgs.items():
                newLines.insert(insertIndex, f'piValue {className}.piBody:piClassGC:initArguments:{argName}:type {argInfo["type"]}')
                insertIndex += 1
                newLines.insert(insertIndex, f'piValue {className}.piBody:piClassGC:initArguments:{argName}:value {argInfo["value"]}')
                insertIndex += 1
            
            changed = True
        
        return '\n'.join(newLines), changed
        
    except Exception as e:
        printIt(f"Error updating seed init arguments: {e}", lable.ERROR)
        return seedContent, False

def extractImportStatements(importNodes: List) -> Tuple[Dict[str, Dict[str, str]], List[str]]:
    """
    Extract import statements from AST nodes.
    Returns (fromImports_dict, regular_imports_list)
    """
    try:
        fromImports = {}
        regularImports = []
        
        for node in importNodes:
            if isinstance(node, ast.ImportFrom):
                # Handle "from module import item" statements
                if node.module:
                    module_name = node.module
                    
                    for alias in node.names:
                        import_name = alias.name
                        if alias.asname:
                            import_name = f"{alias.name} as {alias.asname}"
                        
                        if module_name not in fromImports:
                            fromImports[module_name] = {
                                'from': module_name,
                                'import': import_name
                            }
                        else:
                            # Multiple imports from same module
                            existing_import = fromImports[module_name]['import']
                            if import_name not in existing_import:
                                fromImports[module_name]['import'] = f"{existing_import}, {import_name}"
            
            elif isinstance(node, ast.Import):
                # Handle "import module" statements
                for alias in node.names:
                    import_name = alias.name
                    if alias.asname:
                        import_name = f"{alias.name} as {alias.asname}"
                    regularImports.append(import_name)
        
        return fromImports, regularImports
        
    except Exception as e:
        printIt(f"Error extracting import statements: {e}", lable.ERROR)
        return {}, []

def updateSeedFromImports(seedContent: str, className: str, fromImports: Dict[str, Dict[str, str]]) -> Tuple[str, bool]:
    """
    Update fromImports in the piSeed file content.
    Returns (updated_content, was_changed)
    """
    try:
        lines = seedContent.split('\n')
        newLines = []
        changed = False
        
        # Patterns to match fromImports entries
        structPattern = rf'^piStructA00\s+{re.escape(className)}\.piBody:piClassGC:fromImports\s*$'
        importStructPattern = rf'^piStructC01\s+fromImports\s+(\w+)\.\s*$'
        importFromPattern = rf'^piValue\s+{re.escape(className)}\.piBody:piClassGC:fromImports:(\w+):from\s+'
        importImportPattern = rf'^piValue\s+{re.escape(className)}\.piBody:piClassGC:fromImports:(\w+):import\s+'
        
        i = 0
        foundFromImports = False
        
        while i < len(lines):
            line = lines[i]
            
            # Check if we found the fromImports structure declaration
            if re.match(structPattern, line):
                foundFromImports = True
                newLines.append(line)
                i += 1
                
                # Skip existing import definitions
                while i < len(lines):
                    line = lines[i]
                    if (re.match(importStructPattern, line) or 
                        re.match(importFromPattern, line) or 
                        re.match(importImportPattern, line)):
                        i += 1
                        continue
                    else:
                        break
                
                # Add new import definitions
                for module_name, import_info in fromImports.items():
                    # Clean module name for piSeed (replace dots, hyphens with underscores)
                    clean_module = module_name.replace('.', '_').replace('-', '_')
                    newLines.append(f'piStructC01 fromImports {clean_module}.')
                
                for module_name, import_info in fromImports.items():
                    clean_module = module_name.replace('.', '_').replace('-', '_')
                    newLines.append(f'piValue {className}.piBody:piClassGC:fromImports:{clean_module}:from "{import_info["from"]}"')
                    newLines.append(f'piValue {className}.piBody:piClassGC:fromImports:{clean_module}:import "{import_info["import"]}"')
                
                changed = True
                continue
            else:
                newLines.append(line)
                i += 1
        
        # If fromImports structure wasn't found, add it
        if not foundFromImports and fromImports:
            # Find a good place to insert (after imports)
            insertIndex = len(newLines)
            importsPattern = rf'^piValueA\s+{re.escape(className)}\.piBody:piClassGC:imports\s+'
            
            # Look for existing imports section
            for idx in range(len(newLines)):
                if re.match(importsPattern, newLines[idx]):
                    # Find end of imports section
                    insertIndex = idx
                    while insertIndex < len(newLines) and re.match(importsPattern, newLines[insertIndex]):
                        insertIndex += 1
                    break
            
            # Insert fromImports structure
            newLines.insert(insertIndex, f'piStructA00 {className}.piBody:piClassGC:fromImports')
            insertIndex += 1
            
            # Add import definitions
            for module_name, import_info in fromImports.items():
                clean_module = module_name.replace('.', '_').replace('-', '_')
                newLines.insert(insertIndex, f'piStructC01 fromImports {clean_module}.')
                insertIndex += 1
            
            for module_name, import_info in fromImports.items():
                clean_module = module_name.replace('.', '_').replace('-', '_')
                newLines.insert(insertIndex, f'piValue {className}.piBody:piClassGC:fromImports:{clean_module}:from "{import_info["from"]}"')
                insertIndex += 1
                newLines.insert(insertIndex, f'piValue {className}.piBody:piClassGC:fromImports:{clean_module}:import "{import_info["import"]}"')
                insertIndex += 1
            
            changed = True
        
        return '\n'.join(newLines), changed
        
    except Exception as e:
        printIt(f"Error updating seed fromImports: {e}", lable.ERROR)
        return seedContent, False

def updateSeedImports(seedContent: str, className: str, regularImports: List[str]) -> Tuple[str, bool]:
    """
    Update regular imports in the piSeed file content.
    Returns (updated_content, was_changed)
    """
    try:
        lines = seedContent.split('\n')
        newLines = []
        changed = False
        
        # Pattern to match regular imports
        importsPattern = rf'^piValueA\s+{re.escape(className)}\.piBody:piClassGC:imports\s+'
        
        # Extract existing imports for comparison
        existingImports = []
        i = 0
        foundImports = False
        
        while i < len(lines):
            line = lines[i]
            
            # Check if this is an imports line
            if re.match(importsPattern, line):
                if not foundImports:
                    foundImports = True
                    # Extract existing import lines
                    while i < len(lines) and re.match(importsPattern, lines[i]):
                        # Extract the import name
                        match = re.match(rf'^piValueA\s+{re.escape(className)}\.piBody:piClassGC:imports\s+(.+)$', lines[i])
                        if match:
                            existingImports.append(match.group(1))
                        i += 1
                    
                    # Compare existing imports with new imports
                    if set(existingImports) != set(regularImports):
                        # Imports are different, replace with new imports
                        for import_item in regularImports:
                            newLines.append(f'piValueA {className}.piBody:piClassGC:imports {import_item}')
                        changed = True
                    else:
                        # Imports are the same, keep existing imports
                        for import_item in existingImports:
                            newLines.append(f'piValueA {className}.piBody:piClassGC:imports {import_item}')
                    continue
                else:
                    # Skip remaining import lines (already processed above)
                    i += 1
                    continue
            else:
                newLines.append(line)
                i += 1
        
        # If no imports section found, add it
        if not foundImports and regularImports:
            # Find a good place to insert (after headers)
            insertIndex = len(newLines)
            headersPattern = rf'^piValueA\s+{re.escape(className)}\.piBody:piClassGC:headers\s+'
            
            for idx in range(len(newLines)):
                if re.match(headersPattern, newLines[idx]):
                    # Find end of headers section
                    insertIndex = idx
                    while insertIndex < len(newLines) and re.match(headersPattern, newLines[insertIndex]):
                        insertIndex += 1
                    break
            
            # Insert imports
            for import_item in regularImports:
                newLines.insert(insertIndex, f'piValueA {className}.piBody:piClassGC:imports {import_item}')
                insertIndex += 1
            
            changed = True
        
        return '\n'.join(newLines), changed
        
    except Exception as e:
        printIt(f"Error updating seed imports: {e}", lable.ERROR)
        return seedContent, False

# Helper functions for piDefGC synchronization

def extractAssignmentCode(pythonContent: str, assignNode: ast.Assign) -> Optional[str]:
    """Extract assignment code (constants) from AST node"""
    try:
        lines = pythonContent.split('\n')
        line_num = assignNode.lineno - 1
        if line_num < len(lines):
            return lines[line_num].strip()
        return None
    except Exception as e:
        printIt(f"Error extracting assignment code: {e}", lable.ERROR)
        return None

def extractIfMainCode(pythonContent: str, ifNode: ast.If) -> List[str]:
    """Extract code from if __name__ == '__main__': block"""
    try:
        lines = pythonContent.split('\n')
        startLine = ifNode.lineno - 1
        
        # Find the end of the if block
        endLine = len(lines)
        ifIndent = len(lines[startLine]) - len(lines[startLine].lstrip())
        
        for i in range(startLine + 1, len(lines)):
            line = lines[i]
            if line.strip():  # Non-empty line
                lineIndent = len(line) - len(line.lstrip())
                if lineIndent <= ifIndent:
                    endLine = i
                    break
        
        # Extract if block content
        ifCode = []
        for i in range(startLine, endLine):
            line = lines[i]
            if i == startLine:
                # First line (if statement)
                ifCode.append(line.strip())
            else:
                # Subsequent lines - preserve relative indentation
                if line.strip():
                    if len(line) > ifIndent:
                        ifCode.append(line[ifIndent:])
                    else:
                        ifCode.append(line.strip())
                else:
                    ifCode.append("")
        
        return ifCode
        
    except Exception as e:
        printIt(f"Error extracting if main code: {e}", lable.ERROR)
        return []

def extractModuleDocstring(pythonContent: str) -> List[str]:
    """Extract module-level docstring"""
    try:
        tree = ast.parse(pythonContent)
        if (tree.body and isinstance(tree.body[0], ast.Expr) and 
            isinstance(tree.body[0].value, ast.Constant) and 
            isinstance(tree.body[0].value.value, str)):
            
            docstring = tree.body[0].value.value
            return docstring.split('\n')
        return []
        
    except Exception as e:
        printIt(f"Error extracting module docstring: {e}", lable.ERROR)
        return []

def updateDefSeedHeaders(seedContent: str, defName: str, headers: List[str]) -> Tuple[str, bool]:
    """Update headers in piDefGC seed file"""
    try:
        lines = seedContent.split('\n')
        newLines = []
        changed = False
        
        # Pattern to match headers
        headerPattern = rf'^piValueA\s+{re.escape(defName)}\.piBody:piDefGC:headers\s+'
        
        # First, extract existing headers for comparison
        existingHeaders = []
        for line in lines:
            if re.match(headerPattern, line):
                # Extract the quoted content - use greedy match to handle escaped quotes
                match = re.search(r'"(.*)"$', line)
                if match:
                    existingHeaders.append(match.group(1))
        
        # Compare existing with new headers
        if existingHeaders != headers:
            changed = True
        
        i = 0
        foundHeaders = False
        
        while i < len(lines):
            line = lines[i]
            
            if re.match(headerPattern, line):
                if not foundHeaders:
                    foundHeaders = True
                    # Replace with new headers only if changed
                    if changed:
                        for header in headers:
                            escapedHeader = header.replace('"', '\\"')
                            newLines.append(f'piValueA {defName}.piBody:piDefGC:headers "{escapedHeader}"')
                    else:
                        # Keep existing content
                        temp_i = i
                        while temp_i < len(lines) and re.match(headerPattern, lines[temp_i]):
                            newLines.append(lines[temp_i])
                            temp_i += 1
                
                # Skip all existing header lines
                while i < len(lines) and re.match(headerPattern, lines[i]):
                    i += 1
                continue
            else:
                newLines.append(line)
                i += 1
        
        return '\n'.join(newLines), changed
        
    except Exception as e:
        printIt(f"Error updating def seed headers: {e}", lable.ERROR)
        return seedContent, False

def updateDefSeedFileComments(seedContent: str, defName: str, fileComments: List[str]) -> Tuple[str, bool]:
    """Update file comments in piDefGC seed file"""
    try:
        lines = seedContent.split('\n')
        newLines = []
        changed = False
        
        # Pattern to match file comments
        commentPattern = rf'^piValueA\s+{re.escape(defName)}\.piBody:piDefGC:fileComment\s+'
        
        # First, extract existing file comments for comparison
        existingComments = []
        for line in lines:
            if re.match(commentPattern, line):
                # Extract the quoted content - use greedy match to handle escaped quotes
                match = re.search(r'"(.*)"$', line)
                if match:
                    existingComments.append(match.group(1))
        
        # Filter new comments to only include non-empty ones (like the original logic)
        filteredComments = [comment.strip() for comment in fileComments if comment.strip()]
        
        # Compare existing with new file comments
        if existingComments != filteredComments:
            changed = True
        
        i = 0
        foundComments = False
        
        while i < len(lines):
            line = lines[i]
            
            if re.match(commentPattern, line):
                if not foundComments:
                    foundComments = True
                    # Replace with new comments only if changed
                    if changed:
                        for comment in fileComments:
                            if comment.strip():
                                escapedComment = comment.strip().replace('"', '\\"')
                                newLines.append(f'piValueA {defName}.piBody:piDefGC:fileComment "{escapedComment}"')
                    else:
                        # Keep existing content
                        temp_i = i
                        while temp_i < len(lines) and re.match(commentPattern, lines[temp_i]):
                            newLines.append(lines[temp_i])
                            temp_i += 1
                
                # Skip all existing comment lines
                while i < len(lines) and re.match(commentPattern, lines[i]):
                    i += 1
                continue
            else:
                newLines.append(line)
                i += 1
        
        return '\n'.join(newLines), changed
        
    except Exception as e:
        printIt(f"Error updating def seed file comments: {e}", lable.ERROR)
        return seedContent, False

def updateDefSeedImports(seedContent: str, defName: str, imports: List[str]) -> Tuple[str, bool]:
    """Update regular imports in piDefGC seed file"""
    try:
        lines = seedContent.split('\n')
        newLines = []
        changed = False
        
        # Pattern to match imports
        importPattern = rf'^piValueA\s+{re.escape(defName)}\.piBody:piDefGC:imports\s+'
        
        # First, extract existing imports for comparison
        existingImports = []
        for line in lines:
            if re.match(importPattern, line):
                # Extract the import name (everything after the pattern)
                match = re.match(rf'^piValueA\s+{re.escape(defName)}\.piBody:piDefGC:imports\s+(.+)$', line)
                if match:
                    existingImports.append(match.group(1))
        
        # Compare existing with new imports (order doesn't matter for imports)
        if set(existingImports) != set(imports):
            changed = True
        
        i = 0
        foundImports = False
        
        while i < len(lines):
            line = lines[i]
            
            if re.match(importPattern, line):
                if not foundImports:
                    foundImports = True
                    # Replace with new imports only if changed
                    if changed:
                        for imp in imports:
                            newLines.append(f'piValueA {defName}.piBody:piDefGC:imports {imp}')
                    else:
                        # Keep existing content
                        temp_i = i
                        while temp_i < len(lines) and re.match(importPattern, lines[temp_i]):
                            newLines.append(lines[temp_i])
                            temp_i += 1
                
                # Skip all existing import lines
                while i < len(lines) and re.match(importPattern, lines[i]):
                    i += 1
                continue
            else:
                newLines.append(line)
                i += 1
        
        return '\n'.join(newLines), changed
        
    except Exception as e:
        printIt(f"Error updating def seed imports: {e}", lable.ERROR)
        return seedContent, False

def updateDefSeedFromImports(seedContent: str, defName: str, fromImports: Dict[str, Dict[str, str]]) -> Tuple[str, bool]:
    """Update from imports in piDefGC seed file"""
    try:
        lines = seedContent.split('\n')
        newLines = []
        changed = False
        
        # Patterns for from imports
        structPattern = rf'^piStructA00\s+{re.escape(defName)}\.piBody:piDefGC:fromImports\s*$'
        importStructPattern = rf'^piStructC01\s+fromImports\s+(\w+)\.\s*$'
        importFromPattern = rf'^piValue\s+{re.escape(defName)}\.piBody:piDefGC:fromImports:(\w+):from\s+'
        importImportPattern = rf'^piValue\s+{re.escape(defName)}\.piBody:piDefGC:fromImports:(\w+):import\s+'
        
        # First, extract existing from imports for comparison
        existingFromImports = {}
        for line in lines:
            fromMatch = re.match(importFromPattern, line)
            importMatch = re.match(importImportPattern, line)
            
            if fromMatch:
                module_key = fromMatch.group(1)
                # Extract the quoted content - use greedy match to handle escaped quotes
                contentMatch = re.search(r'"(.*)"$', line)
                if contentMatch:
                    if module_key not in existingFromImports:
                        existingFromImports[module_key] = {}
                    existingFromImports[module_key]['from'] = contentMatch.group(1)
            elif importMatch:
                module_key = importMatch.group(1)
                # Extract the quoted content - use greedy match to handle escaped quotes
                contentMatch = re.search(r'"(.*)"$', line)
                if contentMatch:
                    if module_key not in existingFromImports:
                        existingFromImports[module_key] = {}
                    existingFromImports[module_key]['import'] = contentMatch.group(1)
        
        # Convert new fromImports to the same format for comparison
        newFromImportsForComparison = {}
        for module_name, import_info in fromImports.items():
            clean_module = module_name.replace('.', '_').replace('-', '_')
            newFromImportsForComparison[clean_module] = import_info
        
        # Compare existing with new from imports
        if existingFromImports != newFromImportsForComparison:
            changed = True
        
        i = 0
        foundFromImports = False
        
        while i < len(lines):
            line = lines[i]
            
            if re.match(structPattern, line):
                foundFromImports = True
                newLines.append(line)
                i += 1
                
                # Skip existing from import definitions
                while i < len(lines):
                    line = lines[i]
                    if (re.match(importStructPattern, line) or 
                        re.match(importFromPattern, line) or 
                        re.match(importImportPattern, line)):
                        i += 1
                        continue
                    else:
                        break
                
                # Add new from import definitions only if changed
                if changed:
                    for module_name, import_info in fromImports.items():
                        clean_module = module_name.replace('.', '_').replace('-', '_')
                        newLines.append(f'piStructC01 fromImports {clean_module}.')
                    
                    for module_name, import_info in fromImports.items():
                        clean_module = module_name.replace('.', '_').replace('-', '_')
                        newLines.append(f'piValue {defName}.piBody:piDefGC:fromImports:{clean_module}:from "{import_info["from"]}"')
                        newLines.append(f'piValue {defName}.piBody:piDefGC:fromImports:{clean_module}:import "{import_info["import"]}"')
                else:
                    # Keep existing content - need to reconstruct the skipped lines
                    temp_i = i - 1  # Go back to where we started skipping
                    while temp_i < len(lines):
                        line = lines[temp_i]
                        if (re.match(importStructPattern, line) or 
                            re.match(importFromPattern, line) or 
                            re.match(importImportPattern, line)):
                            newLines.append(line)
                            temp_i += 1
                        else:
                            break
                
                continue
            else:
                newLines.append(line)
                i += 1
        
        return '\n'.join(newLines), changed
        
    except Exception as e:
        printIt(f"Error updating def seed from imports: {e}", lable.ERROR)
        return seedContent, False

def updateDefSeedConstants(seedContent: str, defName: str, constants: List[str]) -> Tuple[str, bool]:
    """Update constants in piDefGC seed file"""
    try:
        lines = seedContent.split('\n')
        newLines = []
        changed = False
        
        # Pattern to match constants
        constantPattern = rf'^piValueA\s+{re.escape(defName)}\.piBody:piDefGC:constants\s+'
        
        # First, extract existing constants for comparison
        existingConstants = []
        for line in lines:
            if re.match(constantPattern, line):
                # Extract the quoted content - use greedy match to handle escaped quotes
                match = re.search(r'"(.*)"$', line)
                if match:
                    existingConstants.append(match.group(1))
        
        # Compare existing with new constants
        if existingConstants != constants:
            changed = True
        
        i = 0
        foundConstants = False
        
        while i < len(lines):
            line = lines[i]
            
            if re.match(constantPattern, line):
                if not foundConstants:
                    foundConstants = True
                    # Replace with new constants only if changed
                    if changed:
                        for constant in constants:
                            escapedConstant = constant.replace('"', '\\"')
                            newLines.append(f'piValueA {defName}.piBody:piDefGC:constants "{escapedConstant}"')
                    else:
                        # Keep existing content
                        temp_i = i
                        while temp_i < len(lines) and re.match(constantPattern, lines[temp_i]):
                            newLines.append(lines[temp_i])
                            temp_i += 1
                
                # Skip all existing constant lines
                while i < len(lines) and re.match(constantPattern, lines[i]):
                    i += 1
                continue
            else:
                newLines.append(line)
                i += 1
        
        return '\n'.join(newLines), changed
        
    except Exception as e:
        printIt(f"Error updating def seed constants: {e}", lable.ERROR)
        return seedContent, False

def updateDefSeedFunctionDefs(seedContent: str, defName: str, functionDefs: Dict[str, List[str]]) -> Tuple[str, bool]:
    """Update function definitions in piDefGC seed file"""
    try:
        lines = seedContent.split('\n')
        newLines = []
        changed = False
        
        # Patterns for function definitions
        structPattern = rf'^piStructA00\s+{re.escape(defName)}\.piBody:piDefGC:functionDefs\s*$'
        funcStructPattern = rf'^piStructL01\s+(\w+)\s+'
        funcDefPattern = rf'^piValueA\s+{re.escape(defName)}\.piBody:piDefGC:functionDefs:(\w+)\s+'
        
        # First, extract existing function definitions for comparison
        existingFunctionDefs = {}
        for line in lines:
            match = re.match(funcDefPattern, line)
            if match:
                funcName = match.group(1)
                if funcName not in existingFunctionDefs:
                    existingFunctionDefs[funcName] = []
                
                # Extract the quoted content - use greedy match to handle escaped quotes
                contentMatch = re.search(r'"(.*)"$', line)
                if contentMatch:
                    existingFunctionDefs[funcName].append(contentMatch.group(1))
        
        # Normalize content by removing trailing empty strings and fix docstring quotes
        def normalize_content(content_list):
            if not content_list:
                return []
            # Make a copy and normalize docstring quotes and escaped quotes
            normalized = []
            for line in content_list:
                # Convert ''' to '''' for consistent comparison
                if line.strip() == "'''":
                    normalized_line = "''''"
                else:
                    normalized_line = line
                # Unescape quotes for consistent comparison
                normalized_line = normalized_line.replace('\\"', '"')
                normalized.append(normalized_line)
            # Remove trailing empty strings
            while normalized and not normalized[-1].strip():
                normalized.pop()
            return normalized
        
        # Compare existing with new function definitions
        for funcName, newFuncCode in functionDefs.items():
            existingFuncCode = existingFunctionDefs.get(funcName, [])
            
            existing_normalized = normalize_content(existingFuncCode[:])  # Make copy
            new_normalized = normalize_content(newFuncCode[:])  # Make copy
            
            if existing_normalized != new_normalized:
                changed = True
                break
        
        # Check if any functions were removed
        if not changed:
            for funcName in existingFunctionDefs:
                if funcName not in functionDefs:
                    changed = True
                    break
        
        # Only update if there are actual changes
        if not changed:
            return seedContent, False
        
        i = 0
        foundFunctionDefs = False
        
        while i < len(lines):
            line = lines[i]
            
            if re.match(structPattern, line):
                foundFunctionDefs = True
                newLines.append(line)
                i += 1
                
                # Skip existing function definitions
                while i < len(lines):
                    line = lines[i]
                    if (re.match(funcStructPattern, line) or 
                        re.match(funcDefPattern, line)):
                        i += 1
                        continue
                    else:
                        break
                
                # Add new function definitions
                for funcName, funcLines in functionDefs.items():
                    newLines.append(f'piStructL01 {funcName} \'Function definition for {funcName}\'')
                
                for funcName, funcLines in functionDefs.items():
                    for funcLine in funcLines:
                        # Fix docstring quotes: convert ''' to ''''
                        if funcLine.strip() == "'''":
                            escapedLine = "''''"
                        else:
                            escapedLine = funcLine.replace('"', '\\"')
                        newLines.append(f'piValueA {defName}.piBody:piDefGC:functionDefs:{funcName} "{escapedLine}"')
                
                continue
            else:
                newLines.append(line)
                i += 1
        
        return '\n'.join(newLines), changed
        
    except Exception as e:
        printIt(f"Error updating def seed function definitions: {e}", lable.ERROR)
        return seedContent, False

def updateDefSeedGlobalCode(seedContent: str, defName: str, globalCode: List[str]) -> Tuple[str, bool]:
    """Update global code in piDefGC seed file"""
    try:
        lines = seedContent.split('\n')
        newLines = []
        changed = False
        
        # Pattern to match global code
        globalPattern = rf'^piValueA\s+{re.escape(defName)}\.piBody:piDefGC:globalCode\s+'
        
        # First, extract existing global code for comparison
        existingGlobalCode = []
        for line in lines:
            if re.match(globalPattern, line):
                # Extract the quoted content - use greedy match to handle escaped quotes
                match = re.search(r'"(.*)"$', line)
                if match:
                    existingGlobalCode.append(match.group(1))
                else:
                    # Handle unquoted content (shouldn't happen but be safe)
                    parts = line.split(None, 2)
                    if len(parts) > 2:
                        existingGlobalCode.append(parts[2])
        
        # Normalize both lists by removing trailing empty strings and fix docstring quotes
        def normalize_content(content_list):
            if not content_list:
                return []
            # Make a copy and normalize docstring quotes and escaped quotes
            normalized = []
            for line in content_list:
                # Convert ''' to '''' for consistent comparison
                if line.strip() == "'''":
                    normalized_line = "''''"
                else:
                    normalized_line = line
                # Unescape quotes for consistent comparison
                normalized_line = normalized_line.replace('\\"', '"')
                normalized.append(normalized_line)
            # Remove trailing empty strings
            while normalized and not normalized[-1].strip():
                normalized.pop()
            return normalized
        
        existing_normalized = normalize_content(existingGlobalCode[:])  # Make copy
        new_normalized = normalize_content(globalCode[:])  # Make copy
        
        # Only proceed if content is actually different
        if existing_normalized != new_normalized:
            changed = True
        
        i = 0
        foundGlobalCode = False
        
        while i < len(lines):
            line = lines[i]
            
            if re.match(globalPattern, line):
                if not foundGlobalCode:
                    foundGlobalCode = True
                    # Replace with new global code only if changed
                    if changed:
                        for codeLine in globalCode:
                            escapedCode = codeLine.replace('"', '\\"')
                            newLines.append(f'piValueA {defName}.piBody:piDefGC:globalCode "{escapedCode}"')
                    else:
                        # Keep existing content - add back the lines we're skipping
                        temp_i = i
                        while temp_i < len(lines) and re.match(globalPattern, lines[temp_i]):
                            newLines.append(lines[temp_i])
                            temp_i += 1
                
                # Skip all existing global code lines
                while i < len(lines) and re.match(globalPattern, lines[i]):
                    i += 1
                continue
            else:
                newLines.append(line)
                i += 1
        
        return '\n'.join(newLines), changed
        
    except Exception as e:
        printIt(f"Error updating def seed global code: {e}", lable.ERROR)
        return seedContent, False
