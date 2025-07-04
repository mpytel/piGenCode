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
                            # Special handling for __init__ method
                            initCodeElements = extractInitCode(pythonContent, item, className)
                            
                            for codeType, codeLines in initCodeElements.items():
                                if codeLines:
                                    newSeedContent, changed = updateSeedCodeElement(
                                        seedContent, className, codeType, codeLines
                                    )
                                    if changed:
                                        seedContent = newSeedContent
                                        changes.append(f"{codeType}")
                            
                            # Extract and sync initArguments from __init__ method
                            initArgs = extractInitArguments(item)
                            if initArgs:
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
                                
                                if methodCode:
                                    # Update piSeed file with new method code
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
        
        # Find and replace existing code element entries
        i = 0
        foundElement = False
        while i < len(lines):
            line = lines[i]
            
            # Check if this line matches our code element pattern
            if re.match(elementPattern, line):
                if not foundElement:
                    # First occurrence - replace with new code
                    foundElement = True
                    for codeLine in methodCode:
                        # Escape quotes in code lines
                        escapedCode = codeLine.replace('"', '\\"')
                        newLines.append(f'piValueA {className}.piBody:piClassGC:{codeElementName} "{escapedCode}"')
                    changed = True
                # Skip all subsequent lines that match this pattern (old code)
                while i < len(lines) and re.match(elementPattern, lines[i]):
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
        
        i = 0
        foundInitArgs = False
        
        while i < len(lines):
            line = lines[i]
            
            # Check if we found the initArguments structure declaration
            if re.match(structPattern, line):
                foundInitArgs = True
                newLines.append(line)
                i += 1
                
                # Skip existing argument definitions
                while i < len(lines):
                    line = lines[i]
                    if (re.match(argStructPattern, line) or 
                        re.match(argTypePattern, line) or 
                        re.match(argValuePattern, line)):
                        i += 1
                        continue
                    else:
                        break
                
                # Add new argument definitions
                for argName, argInfo in initArgs.items():
                    newLines.append(f'piStructC01 argument {argName}.')
                
                for argName, argInfo in initArgs.items():
                    newLines.append(f'piValue {className}.piBody:piClassGC:initArguments:{argName}:type {argInfo["type"]}')
                    newLines.append(f'piValue {className}.piBody:piClassGC:initArguments:{argName}:value {argInfo["value"]}')
                
                changed = True
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
        
        i = 0
        foundImports = False
        
        while i < len(lines):
            line = lines[i]
            
            # Check if this is an imports line
            if re.match(importsPattern, line):
                if not foundImports:
                    foundImports = True
                    # Replace all existing imports with new ones
                    for import_item in regularImports:
                        newLines.append(f'piValueA {className}.piBody:piClassGC:imports {import_item}')
                    changed = True
                
                # Skip all existing import lines
                while i < len(lines) and re.match(importsPattern, lines[i]):
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
