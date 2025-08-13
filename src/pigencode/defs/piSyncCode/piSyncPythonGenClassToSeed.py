import os
import re
import ast
import traceback
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from ..logIt import printIt, lable
from ..getSeedPath import getSeedPath
from ...classes.piGenCode import PiGenCode
from .piSyncCodeUtil import \
    getNextPiSeedNumber, \
    extract_ImportFrom, \
    extractMethodCode, \
    extractImportStatements, \
    extractAssignmentCode, \
    removeTrailingBlankLines, \
    extractCompleteClassCode

piSeedValuePattern = r'["\'](.*)["\'].*$'
global devExept
devExept = True
global showDefNames
# showDefNames = lable.ABORTPRT
# showDefNames = lable.IMPORT
showDefNames = lable.ABORTPRT
showDefNames01 = lable.ABORTPRT
showDefNames02 = lable.ABORTPRT
showDefNames03 = lable.ABORTPRT
# Intelligent pattern detection functions

def analyzeMultiClassFile(pythonFile: Path) -> Dict:
    """
    Analyze a Python file to extract multiple class information for creating piGenClass files.
    Returns dict with imports, from_imports, classes, constants, etc. (piGenClass)
    """
    printIt(f'analyzeMultiClassFile: {str(pythonFile)}', showDefNames)
    try:
        with open(pythonFile, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)

        info = {
            'imports': [],
            'from_imports': {},
            'classes': {},
            'constants': [],
            'mlConstants': {},
            'functions': []
        }

        # Extract imports, classes, and other elements
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    import_name = alias.name
                    if alias.asname:
                        import_name = f"{alias.name} as {alias.asname}"
                    info['imports'].append(import_name)

            elif isinstance(node, ast.ImportFrom):
                module_name, imports = extract_ImportFrom(node)

                info['from_imports'][module_name] = {
                    'from': module_name,
                    'import': ', '.join(imports)
                }

            elif isinstance(node, ast.ClassDef):
                class_name = node.name
                # Create description based on inheritance
                if node.bases:
                    base_names = []
                    for base in node.bases:

                        if isinstance(base, ast.Name):
                            base_names.append(base.id)
                        elif isinstance(base, ast.Attribute):
                            if isinstance(base.value, ast.Name):
                                base_names.append(
                                    f"{base.value.id}.{base.attr}")
                    inheritance_desc = f"inherits from {', '.join(base_names)}"
                else:
                    inheritance_desc = "base class"

                info['classes'][class_name] = f"Class {class_name} - {inheritance_desc}"

            elif isinstance(node, ast.FunctionDef):
                isPropertry, funcCode = extractMethodCode('functions', content, node)
                info['functions'].extend(funcCode)

            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                # Extract constants (module-level assignments)
                constantCode = extractAssignmentCode(content, node)
                if constantCode:
                    # Check if this is a multi-line constant
                    # Multi-line if: contains newlines OR contains triple quotes (multi-line strings)
                    if '\n' in constantCode or '"""' in constantCode or "'''" in constantCode:
                        # Multi-line constant - extract variable name and store in mlConstants ONLY
                        lines = constantCode.split('\n')
                        first_line = lines[0].strip()
                        if '=' in first_line:
                            var_name = first_line.split('=')[0].strip()
                            # Remove type annotation if present (e.g., "baseTypes: list" -> "baseTypes")
                            if ':' in var_name:
                                var_name = var_name.split(':')[0].strip()
                            info['mlConstants'][var_name] = constantCode.split('\n')
                        # Do NOT add to constants array - multi-line constants should only be in mlConstants
                    else:
                        # Single-line constant
                        info['constants'].append(constantCode)
        # printPythonFileInfo(pythonFile, info)
        return info

    except Exception as e:
        if devExept:
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(f'{tb_str}\n\n --- def analyzeMultiClassFile', lable.ERROR)
        printIt(
            f"Error analyzing multi-class file {pythonFile}: {e}", lable.ERROR)
        return {}

def createNewPiGenClassSeedFile(className: str, pythonFile: Path, seed_file: Path | None = None, dest_dir: str | None = None) -> Optional[Path]:
    """
    Create a new piGenClass piSeed file for handling multiple classes in a single file.
    """
    printIt(f'createNewPiGenClassSeedFile: {className}', showDefNames)
    try:
        seedPath = getSeedPath()
        if seed_file:
            seedFilePath = seed_file
        else:
            # Get next available number
            nextNum = getNextPiSeedNumber()

            # Create new piSeed file name
            seedFileName = f"piSeed{nextNum}_piGenClass_{className}.pi"
            seedFilePath = seedPath.joinpath(seedFileName)

        # Determine file directory - use dest_dir if provided, otherwise use pythonFile's directory
        # Determine file directory
        if dest_dir is not None:
            fileDirectory = dest_dir
        else:
            try:
                # Get relative path from current directory
                relativeDir = pythonFile.parent.relative_to(Path.cwd())
                fileDirectory = str(relativeDir)
            except ValueError:
                # If not relative to cwd, use absolute path
                fileDirectory = str(pythonFile.parent)

        # Analyze the Python file to extract class information
        class_info = analyzeMultiClassFile(pythonFile)
        #print(list(class_info.keys()))
        #print('createNewPiGenClassSeedFile-fileDirectory',fileDirectory)

        # Create piGenClass piSeed content
        seedContent = f"""piGenClass {className} 'Generated piGenClass for {className} multi-class file'
piValue {className}.piProlog pi.piProlog
piValue {className}.piBase:piType piGenClass
piValue {className}.piBase:piTitle {className}
piValue {className}.piBase:piSD 'Python multi-class file {className} generated from existing code'
piValue {className}.piBody:piGenClass:fileDirectory '{fileDirectory}'
piValue {className}.piBody:piGenClass:fileName {className}
piValueA {className}.piBody:piGenClass:headers '# {className} classes - synced from existing code'
"""

        # Add imports if found
        if class_info.get('imports'):
            for imp in class_info['imports']:
                seedContent += f"piValueA {className}.piBody:piGenClass:imports {imp}\n"

        # Add from imports if found
        if class_info.get('from_imports'):
            seedContent += f"piStructA00 {className}.piBody:piGenClass:fromImports\n"
            for module_name, import_info in class_info['from_imports'].items():
                clean_module = module_name.replace('.', '_').replace('-', '_')
                seedContent += f"piStructC01 fromImports {clean_module}.\n"
            for module_name, import_info in class_info['from_imports'].items():
                clean_module = module_name.replace('.', '_').replace('-', '_')
                seedContent += f"piValue {className}.piBody:piGenClass:fromImports:{clean_module}:from \"{import_info['from']}\"\n"
                seedContent += f"piValue {className}.piBody:piGenClass:fromImports:{clean_module}:import \"{import_info['import']}\"\n"

        # Add constants if found
        if class_info.get('constants'):
            for constant in class_info['constants']:
                escaped_constant = constant.replace('"', '\\"')
                seedContent += f"piValueA {className}.piBody:piGenClass:constants \"{escaped_constant}\"\n"

        # Add class definitions if found
        if class_info.get('classes'):
            seedContent += f"piStructA00 {className}.piBody:piGenClass:classDefs\n"
            for class_name, class_desc in class_info['classes'].items():
                seedContent += f"piStructL01 {class_name} '{class_desc}'\n"
        # ['imports', 'from_imports', 'classes', 'constants', 'mlConstants', 'functions']
        # Add multi-line constants
        if class_info.get('mlConstants'):
            seedContent += f"piStructA00 {className}.piBody:piGenClass:mlConstants\n"
            # First add all the structure definitions
            for var_name in class_info['mlConstants'].keys():
                seedContent += f"piStructL01 {var_name} 'Multi-line constant {var_name}'\n"
            # Then add the actual constant lines
            for var_name, constant_lines in class_info['mlConstants'].items():
                for line in constant_lines:
                    escaped_line = line.replace('"', '\\"')
                    seedContent += f"piValueA {className}.piBody:piGenClass:mlConstants:{var_name} \"{escaped_line}\"\n"

        # funcrionDefs seem to be written elseware so this is removed to avoid duplication

        if class_info.get('functions'):
            for line in class_info['functions']:
                seedContent += f"piValueA {className}.piBody:piGenClass:globalCode \"{line}\"\n"
        # if class_info.get('functions'):
        #     print('functions',class_info['functions'])
        #     seedContent += f"piStructA00 {className}.piBody:piDefGC:functionDefs\n"
        #     # First add all the structure definitions
        #     for func_name in class_info['functions']:
        #         seedContent += f"piStructL01 {func_name} 'Function definition for {func_name}'\n"
        #     # Then add the actual function code
        #     for line in class_info['functions']:
        #             escaped_line = escapeQuotesForPiSeed(line)
        #             seedContent += f"piValueA {className}.piBody:piDefGC:functionDefs:{func_name} \"{escaped_line}\"\n"

        # Write the new piSeed file
        with open(seedFilePath, 'w', encoding='utf-8') as f:
            f.write(seedContent)

        printIt(
            f"Created new piGenClass piSeed file: {seedFileName}", lable.INFO)
        return seedFilePath

    except Exception as e:
        if devExept:
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(f'{tb_str}\n\n --- def createNewPiGenClassSeedFile', lable.ERROR)
        printIt(
            f"Error creating new piGenClass piSeed file for {className}: {e}", lable.ERROR)
        return None

def syncPythonGenClassToSeed(pythonFile: Path, piSeedFile: Path) -> List[str]:
    """
    Sync changes from Python multi-class file back to piGenClass piSeed file.
    Returns list of changes made.
    """

    try:
        printIt(f'syncPythonGenClassToSeed: {pythonFile.name}', showDefNames)
        changes = []

        # Read the Python file
        with open(pythonFile, 'r', encoding='utf-8') as f:
            pythonContent = f.read()

        # Read the piSeed file
        with open(piSeedFile, 'r', encoding='utf-8') as f:
            seedContent = f.read()

        # Parse Python file to extract elements
        try:
            tree = ast.parse(pythonContent)
            className = pythonFile.stem

            # Extract different elements from the Python file
            importStatements = []
            classDefs = {}
            constants = []
            mlConstants = {}
            globalCode = []
            headers = []

            # Process top-level nodes
            for node in tree.body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    importStatements.append(node)
                elif isinstance(node, ast.ClassDef):
                    # Extract complete class definition
                    classCode = extractCompleteClassCode(pythonContent, node)
                    classDefs[node.name] = classCode
                elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                    # Constants (module-level assignments)
                    constantCode = extractAssignmentCode(pythonContent, node)
                    if constantCode:
                        # Check if this is a multi-line constant
                        # Multi-line if: contains newlines OR contains triple quotes (multi-line strings)
                        if '\n' in constantCode or '"""' in constantCode or "'''" in constantCode:
                            # Multi-line constant - extract variable name and store in mlConstants ONLY
                            lines = constantCode.split('\n')
                            first_line = lines[0].strip()
                            if '=' in first_line:
                                var_name = first_line.split('=')[0].strip()
                                # Remove type annotation if present (e.g., "baseTypes: list" -> "baseTypes")
                                if ':' in var_name:
                                    var_name = var_name.split(':')[0].strip()
                                mlConstants[var_name] = constantCode.split('\n')
                            # Do NOT add to constants array - multi-line constants should only be in mlConstants
                        else:
                            # Single-line constant
                            constants.append(constantCode)
                elif isinstance(node, ast.FunctionDef):
                    # Global functions
                    isPropertry, funcCode = extractMethodCode(
                        'global', pythonContent, node)
                    globalCode.extend(funcCode)
                    globalCode.append("")  # Add blank line between functions

            # Extract file headers from the beginning of the file
            lines = pythonContent.split('\n')
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('#'):
                    headers.append(stripped)
                elif stripped and not stripped.startswith('#'):
                    break

            # Update piSeed file with extracted elements

            # Update headers
            if headers:
                newSeedContent, changed = updateGenClassSeedHeaders(
                    seedContent, className, headers)
                if changed:
                    seedContent = newSeedContent
                    changes.append("headers")

            # Update imports
            if importStatements:
                fromImports, regularImports = extractImportStatements(
                    importStatements)

                if regularImports:
                    newSeedContent, changed = updateGenClassSeedImports(
                        seedContent, className, regularImports)
                    if changed:
                        seedContent = newSeedContent
                        changes.append("imports")

                if fromImports:
                    newSeedContent, changed = updateGenClassSeedFromImports(
                        seedContent, className, fromImports)
                    if changed:
                        seedContent = newSeedContent
                        changes.append("fromImports")

            # Update constants
            if constants:
                newSeedContent, changed = updateGenClassSeedConstants(
                    seedContent, className, constants)
                if changed:
                    seedContent = newSeedContent
                    changes.append("constants")

            # Update multi-line constants
            if mlConstants:
                newSeedContent, changed = updateGenClassSeedMlConstants(
                    seedContent, className, mlConstants)
                if changed:
                    seedContent = newSeedContent
                    changes.append("mlConstants")

            # Update class definitions
            if classDefs:
                newSeedContent, changed = updateGenClassSeedClassDefs(
                    seedContent, className, classDefs)
                if changed:
                    seedContent = newSeedContent
                    changes.append("classDefs")

            # Update global code
            if globalCode:
                # Remove trailing blank lines more robustly
                globalCode = removeTrailingBlankLines(globalCode)

                newSeedContent, changed = updateGenClassSeedGlobalCode(
                    seedContent, className, globalCode)
                if changed:
                    seedContent = newSeedContent
                    changes.append("globalCode")

            # Write updated piSeed file if changes were made
            if changes:
                with open(piSeedFile, 'w', encoding='utf-8') as f:
                    f.write(seedContent)

        except SyntaxError as e:
            printIt(
                f"Syntax error in Python file {pythonFile}: {e}", lable.ERROR)

    except Exception as e:
        if devExept:
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(f'{tb_str}\n\n --- def syncPythonGenClassToSeed', lable.ERROR)
        printIt(
            f"Error syncing {pythonFile} to {piSeedFile}: {e}", lable.ERROR)

    return changes

def updateGenClassSeedHeaders(seedContent: str, className: str, headers: List[str]) -> Tuple[str, bool]:
    """Update headers in piGenClass seed file"""
    printIt('updateGenClassSeedHeaders', showDefNames03)
    try:
        lines = seedContent.split('\n')
        newLines = []
        changed = False

        # Pattern to match headers
        headerPattern = rf'^piValueA\s+{re.escape(className)}\.piBody:piGenClass:headers\s+'

        # Extract existing headers for comparison
        existingHeaders = []
        for line in lines:
            if re.match(headerPattern, line):
                match = re.search(piSeedValuePattern, line)
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
                            escaped_header = header.replace("'", "\\'")
                            newLines.append(
                                f"piValueA {className}.piBody:piGenClass:headers '{escaped_header}'")
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
        printIt(f"Error updating piGenClass seed headers: {e}", lable.ERROR)
        return seedContent, False

def updateGenClassSeedImports(seedContent: str, className: str, imports: List[str]) -> Tuple[str, bool]:
    """Update regular imports in piGenClass seed file"""
    printIt('updateGenClassSeedImports', showDefNames03)
    try:
        lines = seedContent.split('\n')
        newLines = []
        changed = False

        # Pattern to match imports
        importPattern = rf'^piValueA\s+{re.escape(className)}\.piBody:piGenClass:imports\s+'

        # Extract existing imports for comparison
        existingImports = []
        for line in lines:
            if re.match(importPattern, line):
                match = re.match(
                    rf'^piValueA\s+{re.escape(className)}\.piBody:piGenClass:imports\s+(.+)$', line)
                if match:
                    existingImports.append(match.group(1))

        # Compare existing with new imports
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
                            newLines.append(
                                f"piValueA {className}.piBody:piGenClass:imports {imp}")
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
        printIt(f"Error updating piGenClass seed imports: {e}", lable.ERROR)
        return seedContent, False


def updateGenClassSeedMlConstants(seedContent: str, className: str, mlConstants: Dict[str, List[str]]) -> Tuple[str, bool]:
    """Update multi-line constants in piGenClass seed file"""
    printIt('updateGenClassSeedMlConstants', showDefNames03)
    try:
        lines = seedContent.split('\n')
        newLines = []
        changed = False

        # Patterns for multi-line constants
        structPattern = rf'^piStructA00\s+{re.escape(className)}\.piBody:piGenClass:mlConstants\s*$'
        mlConstStructPattern = rf'^piStructL01\s+(\w+)\s+'
        mlConstDefPattern = rf'^piValueA\s+{re.escape(className)}\.piBody:piGenClass:mlConstants:(\w+)\s+'

        # Extract existing multi-line constants for comparison
        existingMlConstants = {}
        for line in lines:
            match = re.match(mlConstDefPattern, line)
            if match:
                constName = match.group(1)
                if constName not in existingMlConstants:
                    existingMlConstants[constName] = []

                # Extract the quoted content
                contentMatch = re.search(piSeedValuePattern, line)
                if contentMatch:
                    existingMlConstants[constName].append(contentMatch.group(1))

        # Compare existing with new multi-line constants
        for constName, newConstLines in mlConstants.items():
            existingConstLines = existingMlConstants.get(constName, [])

            # Normalize content for comparison
            existing_normalized = [line.replace('\\"', '"') for line in existingConstLines]
            new_normalized = newConstLines[:]

            if existing_normalized != new_normalized:
                changed = True
                break

        # Check if any constants were removed
        if not changed:
            for constName in existingMlConstants:
                if constName not in mlConstants:
                    changed = True
                    break

        # Only update if there are actual changes
        if not changed:
            return seedContent, False

        i = 0
        foundMlConstants = False

        while i < len(lines):
            line = lines[i]

            if re.match(structPattern, line):
                foundMlConstants = True
                newLines.append(line)
                i += 1

                # Skip existing multi-line constant definitions
                while i < len(lines):
                    line = lines[i]
                    if (re.match(mlConstStructPattern, line) or
                            re.match(mlConstDefPattern, line)):
                        i += 1
                        continue
                    else:
                        break

                # Add new multi-line constant definitions
                for constName in mlConstants.keys():
                    newLines.append(f'piStructL01 {constName} \'Multi-line constant {constName}\'')

                for constName, constLines in mlConstants.items():
                    for constLine in constLines:
                        escapedLine = constLine.replace('"', '\\"')
                        newLines.append(f'piValueA {className}.piBody:piGenClass:mlConstants:{constName} "{escapedLine}"')

                continue
            else:
                newLines.append(line)
                i += 1

        # If no existing mlConstants section was found but we have new constants, add them
        if not foundMlConstants and mlConstants and changed:
            # Find insertion point (after constants, before classDefs)
            insertionPoint = -1
            for i, line in enumerate(newLines):
                if 'piStructA00' in line and 'classDefs' in line:
                    insertionPoint = i
                    break
            
            if insertionPoint >= 0:
                # Insert mlConstants section before classDefs
                mlConstLines = [f'piStructA00 {className}.piBody:piGenClass:mlConstants']
                
                # Add structure definitions
                for constName in mlConstants.keys():
                    mlConstLines.append(f'piStructL01 {constName} \'Multi-line constant {constName}\'')
                
                # Add constant lines
                for constName, constLines in mlConstants.items():
                    for constLine in constLines:
                        escapedLine = constLine.replace('"', '\\"')
                        mlConstLines.append(f'piValueA {className}.piBody:piGenClass:mlConstants:{constName} "{escapedLine}"')
                
                # Insert at the insertion point
                for j, mlConstLine in enumerate(mlConstLines):
                    newLines.insert(insertionPoint + j, mlConstLine)
            else:
                # Append at the end if no insertion point found
                newLines.append(f'piStructA00 {className}.piBody:piGenClass:mlConstants')
                
                # Add structure definitions
                for constName in mlConstants.keys():
                    newLines.append(f'piStructL01 {constName} \'Multi-line constant {constName}\'')
                
                # Add constant lines
                for constName, constLines in mlConstants.items():
                    for constLine in constLines:
                        escapedLine = constLine.replace('"', '\\"')
                        newLines.append(f'piValueA {className}.piBody:piGenClass:mlConstants:{constName} "{escapedLine}"')

        return '\n'.join(newLines), changed

    except Exception as e:
        if devExept:
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(f'{tb_str}\n\n --- def updateGenClassSeedMlConstants', lable.ERROR)
        printIt(f"Error updating piGenClass seed multi-line constants: {e}", lable.ERROR)
        return seedContent, False


def updateGenClassSeedFromImports(seedContent: str, className: str, fromImports: Dict[str, Dict[str, str]]) -> Tuple[str, bool]:
    """Update from imports in piGenClass seed file"""
    printIt('updateGenClassSeedFromImports', showDefNames03)
    # This is similar to the piDefGC version but with piGenClass paths
    # Implementation would be similar to updateDefSeedFromImports but with piGenClass paths
    return seedContent, False  # Placeholder for now


def updateGenClassSeedConstants(seedContent: str, className: str, constants: List[str]) -> Tuple[str, bool]:
    """Update constants in piGenClass seed file"""
    printIt('updateGenClassSeedConstants', showDefNames03)
    try:
        lines = seedContent.split('\n')
        newLines = []
        changed = False

        # Pattern to match constants
        constantPattern = rf'^piValueA\s+{re.escape(className)}\.piBody:piGenClass:constants\s+'

        # First, extract existing constants for comparison
        existingConstants = []
        for line in lines:
            if re.match(constantPattern, line):
                # Extract the quoted content
                match = re.search(piSeedValuePattern, line)
                if match:
                    existingConstants.append(match.group(1))

        # Compare existing with new constants
        if existingConstants != constants:
            changed = True

        i = 0
        foundConstants = False
        insertionPoint = -1

        while i < len(lines):
            line = lines[i]

            if re.match(constantPattern, line):
                if not foundConstants:
                    foundConstants = True
                    # Replace with new constants only if changed
                    if changed:
                        for constant in constants:
                            escapedConstant = constant.replace('"', '\\"')
                            newLines.append(
                                f'piValueA {className}.piBody:piGenClass:constants "{escapedConstant}"')
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
                # Look for insertion point (after fromImports, before classDefs)
                if not foundConstants and 'piStructA00' in line and 'classDefs' in line:
                    insertionPoint = len(newLines)
                
                newLines.append(line)
                i += 1

        # If no existing constants were found but we have new constants, insert them
        if not foundConstants and constants and changed:
            if insertionPoint >= 0:
                # Insert constants before classDefs
                for j, constant in enumerate(constants):
                    escapedConstant = constant.replace('"', '\\"')
                    newLines.insert(insertionPoint + j, 
                        f'piValueA {className}.piBody:piGenClass:constants "{escapedConstant}"')
            else:
                # Append at the end if no insertion point found
                for constant in constants:
                    escapedConstant = constant.replace('"', '\\"')
                    newLines.append(
                        f'piValueA {className}.piBody:piGenClass:constants "{escapedConstant}"')

        return '\n'.join(newLines), changed

    except Exception as e:
        if devExept:
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(f'{tb_str}\n\n --- def updateGenClassSeedConstants', lable.ERROR)
        printIt(f"Error updating piGenClass seed constants: {e}", lable.ERROR)
        return seedContent, False

def updateGenClassSeedClassDefs(seedContent: str, className: str, classDefs: Dict[str, List[str]]) -> Tuple[str, bool]:
    """Update class definitions in piGenClass seed file"""
    printIt('updateGenClassSeedClassDefs', showDefNames03)
    try:
        lines = seedContent.split('\n')
        newLines = []
        changed = False

        # Patterns for class definitions
        structPattern = rf'^piStructA00\s+{re.escape(className)}\.piBody:piGenClass:classDefs\s*$'
        classStructPattern = rf'^piStructL01\s+(\w+)\s+'
        classDefPattern = rf'^piValueA\s+{re.escape(className)}\.piBody:piGenClass:classDefs:(\w+)\s+'

        # Extract existing class definitions for comparison
        existingClassDefs = {}
        for line in lines:
            match = re.match(classDefPattern, line)
            if match:
                className_match = match.group(1)
                if className_match not in existingClassDefs:
                    existingClassDefs[className_match] = []

                # Extract the quoted content
                contentMatch = re.search(piSeedValuePattern, line)
                if contentMatch:
                    existingClassDefs[className_match].append(
                        contentMatch.group(1))

        # Compare existing with new class definitions
        for classDefName, newClassCode in classDefs.items():
            existingClassCode = existingClassDefs.get(classDefName, [])

            # Normalize content for comparison
            existing_normalized = [line.replace(
                '\\"', '"') for line in existingClassCode]
            new_normalized = newClassCode[:]

            if existing_normalized != new_normalized:
                changed = True
                break

        # Check if any classes were removed
        if not changed:
            for classDefName in existingClassDefs:
                if classDefName not in classDefs:
                    changed = True
                    break

        # Only update if there are actual changes
        if not changed:
            return seedContent, False

        i = 0
        foundClassDefs = False

        while i < len(lines):
            line = lines[i]

            if re.match(structPattern, line):
                foundClassDefs = True
                newLines.append(line)
                i += 1

                # Skip existing class definitions
                while i < len(lines):
                    line = lines[i]
                    if (re.match(classStructPattern, line) or
                            re.match(classDefPattern, line)):
                        i += 1
                        continue
                    else:
                        break

                # Add new class definitions
                for classDefName, classLines in classDefs.items():
                    newLines.append(
                        f'piStructL01 {classDefName} \'Class definition for {classDefName}\'')

                for classDefName, classLines in classDefs.items():
                    for classLine in classLines:
                        escapedLine = classLine.replace('"', '\\"')
                        newLines.append(
                            f'piValueA {className}.piBody:piGenClass:classDefs:{classDefName} "{escapedLine}"')

                continue
            else:
                newLines.append(line)
                i += 1

        return '\n'.join(newLines), changed

    except Exception as e:
        printIt(
            f"Error updating piGenClass seed class definitions: {e}", lable.ERROR)
        return seedContent, False


def updateGenClassSeedGlobalCode(seedContent: str, className: str, globalCode: List[str]) -> Tuple[str, bool]:
    """Update global code in piGenClass seed file"""
    printIt('updateGenClassSeedGlobalCode', showDefNames03)
    try:
        lines = seedContent.split('\n')
        newLines = []
        changed = False

        # Pattern to match global code
        globalPattern = rf'^piValueA\s+{re.escape(className)}\.piBody:piGenClass:globalCode\s+'

        # First, extract existing global code for comparison
        existingGlobalCode = []
        for line in lines:
            if re.match(globalPattern, line):
                # Extract the quoted content using the same pattern as other functions
                match = re.search(r'["\'](.*)["\']\s*$', line)
                if match:
                    existingGlobalCode.append(match.group(1))

        # Normalize both lists by removing trailing empty strings and unescaping quotes
        def normalize_content(content_list):
            if not content_list:
                return []
            # Make a copy and remove trailing empty strings
            normalized = content_list[:]
            while normalized and not normalized[-1].strip():
                normalized.pop()
            # Unescape quotes for consistent comparison
            normalized = [line.replace('\\"', '"') for line in normalized]
            return normalized

        existing_normalized = normalize_content(existingGlobalCode[:])
        new_normalized = normalize_content(globalCode[:])

        # Only proceed if content is actually different
        if existing_normalized != new_normalized:
            changed = True
        else:
            changed = False

        i = 0
        foundGlobalCode = False
        while i < len(lines):
            line = lines[i]
            if re.match(globalPattern, line):
                if not foundGlobalCode:
                    foundGlobalCode = True
                    # Skip all existing global code lines
                    while i < len(lines) and re.match(globalPattern, lines[i]):
                        i += 1
                    # Add new global code lines
                    if changed:
                        for codeLine in globalCode:
                            # Escape quotes in the code
                            escapedCode = codeLine.replace('"', '\\"')
                            newLines.append(
                                f'piValueA {className}.piBody:piGenClass:globalCode "{escapedCode}"')
                    continue
            else:
                newLines.append(line)
            i += 1

        # If no existing global code was found but we have new code, add it at the end
        if not foundGlobalCode and globalCode and changed:
            for codeLine in globalCode:
                escapedCode = codeLine.replace('"', '\\"')
                newLines.append(
                    f'piValueA {className}.piBody:piGenClass:globalCode "{escapedCode}"')

        if changed:
            return '\n'.join(newLines), True
        else:
            return seedContent, False

    except Exception as e:
        if devExept:
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(f'{tb_str}\n\n --- def updateGenClassSeedGlobalCode', lable.ERROR)
        printIt(f"Error updating GenClass seed global code: {e}", lable.ERROR)
        return seedContent, False

