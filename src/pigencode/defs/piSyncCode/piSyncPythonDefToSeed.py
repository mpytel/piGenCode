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
    extractAssignmentCode, \
    escapeQuotesForPiSeed, \
    printPythonFileInfo, \
    extractIfMainCode, \
    extractMethodCode

piSeedValuePattern = r'["\'](.*)["\'].*$'
global options
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

def createNewPiDefGCSeedFile(defName: str, pythonFile: Path, seed_file: Path | None = None, dest_dir: str | None = None) -> Optional[Path]:
    """Create a new piDefGC piSeed file for the given function definition file"""
    printIt(f'createNewPiDefGCSeedFile: {defName}', showDefNames)
    try:
        seedPath = getSeedPath()

        if seed_file:
            seedFilePath = seed_file
        else:
            # Get next available number
            nextNum = getNextPiSeedNumber()

            # Create new piSeed file name
            seedFileName = f"piSeed{nextNum}_piDefGC_{defName}.pi"
            seedFilePath = seedPath.joinpath(seedFileName)

        # Determine file directory - use dest_dir if provided, otherwise use pythonFile's directory
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
        # Analyze the Python file to extract more information
        def_info = analyzePythonDefFile(pythonFile)

        #print('createNewPiDefGCSeedFile-fileDirectory',fileDirectory)
        # Create enhanced piDefGC piSeed content
        seedContent = f"""piDefGC {defName} 'Generated piDefGC for {defName} function definitions'
piValue {defName}.piProlog pi.piProlog
piValue {defName}.piBase:piType piDefGC
piValue {defName}.piBase:piTitle {defName}
piValue {defName}.piBase:piSD 'Python function definitions {defName} generated from existing code'
piValue {defName}.piBody:piDefGC:fileDirectory '{fileDirectory}'
piValue {defName}.piBody:piDefGC:fileName {defName}
piValueA {defName}.piBody:piDefGC:headers '# {defName} functions - synced from existing code'
"""

        # Add imports if found
        if def_info.get('imports'):
            for imp in def_info['imports']:
                seedContent += f"piValueA {defName}.piBody:piDefGC:imports {imp}\n"

        # Add from imports if found
        if def_info.get('from_imports'):
            seedContent += f"piStructA00 {defName}.piBody:piDefGC:fromImports\n"
            for module_name, import_info in def_info['from_imports'].items():
                clean_module = module_name.replace('.', '_').replace('-', '_')
                seedContent += f"piStructC01 fromImports {clean_module}.\n"
            for module_name, import_info in def_info['from_imports'].items():
                clean_module = module_name.replace('.', '_').replace('-', '_')
                seedContent += f"piValue {defName}.piBody:piDefGC:fromImports:{clean_module}:from \"{import_info['from']}\"\n"
                seedContent += f"piValue {defName}.piBody:piDefGC:fromImports:{clean_module}:import \"{import_info['import']}\"\n"

        # Add constants if found
        if def_info.get('constants'):
            for constant in def_info['constants']:
                #print('constant',constant)
                escaped_constant = constant.replace('"', '\\"')
                seedContent += f"piValueA {defName}.piBody:piDefGC:constants \"{escaped_constant}\"\n"

        # Add multi-line constants if found
        if def_info.get('mlConstants'):
            for var_name, constant_lines in def_info['mlConstants'].items():
                seedContent += f"piStructA00 {defName}.piBody:piDefGC:mlConstants\n"
                seedContent += f"piStructL01 {var_name} 'Multi-line constant {var_name}'\n"
                for line in constant_lines:
                    escaped_line = line.replace('"', '\\"')
                    seedContent += f"piValueA {defName}.piBody:piDefGC:mlConstants:{var_name} \"{escaped_line}\"\n"

        # Add function definitions if found
        if def_info.get('functions'):
            seedContent += f"piStructA00 {defName}.piBody:piDefGC:functionDefs\n"
            for func_name in def_info['functions']:
                seedContent += f"piStructL01 {func_name} 'Function definition for {func_name}'\n"

        # Write the new piSeed file
        with open(seedFilePath, 'w', encoding='utf-8') as f:
            f.write(seedContent)

        printIt(f"Created new piDefGC piSeed file: {seedFileName}", lable.INFO)
        return seedFilePath

    except Exception as e:
        if devExept:
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(f'{tb_str}\n\n --- def createNewPiDefGCSeedFile', lable.ERROR)
        printIt(
            f"Error creating new piDefGC piSeed file for {defName}: {e}", lable.ERROR)
        return None

def analyzePythonDefFile(pythonFile: Path) -> Dict:
    """
    Analyze a Python file to extract function definition information for creating piSeed files.
    Returns dict with imports, from_imports, functions, constants, etc.
    """
    printIt('analyzePythonDefFile', showDefNames02)
    try:
        with open(pythonFile, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)

        info = {
            'imports': [],
            'from_imports': {},
            'functions': [],
            'constants': [],
            'mlConstants': {}
        }

        # Extract imports, functions, and constants
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

            elif isinstance(node, ast.FunctionDef):
                info['functions'].append(node.name)

            elif isinstance(node, ast.Assign):
                # Extract constants (module-level assignments)
                constantCode = extractAssignmentCode(content, node)
                if constantCode:
                    # Check if this is a multi-line constant
                    # Multi-line if: contains newlines OR contains triple quotes (multi-line strings)
                    if '\n' in constantCode or '"""' in constantCode or "'''" in constantCode:
                        # Multi-line constant - extract variable name and store in mlConstants
                        lines = constantCode.split('\n')
                        first_line = lines[0].strip()
                        if '=' in first_line:
                            var_name = first_line.split('=')[0].strip()
                            info['mlConstants'][var_name] = constantCode.split(
                                '\n')
                    else:
                        # Single-line constant
                        info['constants'].append(constantCode)
        #printPythonFileInfo(pythonFile, info)
        return info

    except Exception as e:
        if devExept:
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(f'{tb_str}\n\n --- def analyzePythonDefFile', lable.ERROR)
        printIt(f"Error analyzing Python def file {pythonFile}: {e}", lable.ERROR)
        return {}

def syncPythonDefToSeed(pythonFile: Path, piSeedFile: Path, dest_dir: str | None = None) -> List[str]:
    """
    Sync changes from Python function definition file back to piDefGC piSeed file.
    Returns list of changes made.
    """
    printIt(f'syncPythonDefToSeed: {pythonFile.name}', showDefNames)
    changes = []

    # Use the comprehensive rebuilding approach for better reliability
    rebuild_changes = rebuildDefSeedFromPython(pythonFile, piSeedFile, dest_dir)
    if rebuild_changes:
        return rebuild_changes
    else:
        return []

def updateDefSeedHeaders(seedContent: str, defName: str, headers: List[str]) -> Tuple[str, bool]:
    """Update headers in piDefGC seed file"""
    printIt('updateDefSeedHeaders', showDefNames03)
    try:
        lines = seedContent.split('\n')
        newLines = []
        changed = False

        # Pattern to match headers
        # ^piValueA\s+writePyProject\.piBody:piDefGC:headers\s+
        headerPattern = rf'^piValueA\s+{re.escape(defName)}\.piBody:piDefGC:headers\s+'

        # First, extract existing headers for comparison
        existingHeaders = []
        for line in lines:
            if re.match(headerPattern, line):
                # Extract the quoted content - use greedy match to handle escaped quotes
                match = re.search(piSeedValuePattern, line)
                if match:
                    existingHeaders.append(match.group(1))

        # Compare existing with new headers
        if existingHeaders != headers:
            print('existingHeaders\n', existingHeaders)
            print('headers\n', headers)
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
                            newLines.append(
                                f'piValueA {defName}.piBody:piDefGC:headers "{escapedHeader}"')
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
        if devExept:
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(f'{tb_str}\n\n --- def updateDefSeedHeaders', lable.ERROR)
        printIt(f"Error updating def seed headers: {e}", lable.ERROR)
        return seedContent, False

def updateDefSeedFileComments(seedContent: str, defName: str, fileComments: List[str]) -> Tuple[str, bool]:
    """Update file comments in piDefGC seed file"""
    printIt('updateDefSeedFileComments', showDefNames03)
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
                match = re.search(piSeedValuePattern, line)
                if match:
                    existingComments.append(match.group(1))

        # Filter new comments to only include non-empty ones (like the original logic)
        filteredComments = [comment.strip()
                            for comment in fileComments if comment.strip()]

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
                                newLines.append(
                                    f'piValueA {defName}.piBody:piDefGC:fileComment "{escapedComment}"')
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
        if devExept:
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(f'{tb_str}\n\n --- def updateDefSeedFileComments', lable.ERROR)
        printIt(f"Error updating def seed file comments: {e}", lable.ERROR)
        return seedContent, False


def updateDefSeedImports(seedContent: str, defName: str, imports: List[str]) -> Tuple[str, bool]:
    """Update regular imports in piDefGC seed file"""
    printIt('updateDefSeedImports', showDefNames03)
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
                match = re.match(
                    rf'^piValueA\s+{re.escape(defName)}\.piBody:piDefGC:imports\s+(.+)$', line)
                if match:
                    existingImports.append(match.group(1))

        # Compare existing with new imports (order doesn't matter for imports)
        if set(existingImports) != set(imports):
            changed = True

        # If no changes needed, return original content
        if not changed:
            return seedContent, False

        i = 0
        foundImports = False
        insertionPoint = -1

        while i < len(lines):
            line = lines[i]

            if re.match(importPattern, line):
                if not foundImports:
                    foundImports = True
                    # Replace with new imports
                    for imp in imports:
                        newLines.append(
                            f'piValueA {defName}.piBody:piDefGC:imports {imp}')

                # Skip all existing import lines
                while i < len(lines) and re.match(importPattern, lines[i]):
                    i += 1
                continue
            else:
                # Look for a good insertion point (after headers)
                if not foundImports and line.strip().startswith(f'piValueA {defName}.piBody:piDefGC:headers'):
                    insertionPoint = len(newLines) + 1

                newLines.append(line)
                i += 1

        # If no existing imports were found, insert them at the appropriate location
        if not foundImports and imports:
            if insertionPoint >= 0:
                # Insert after headers
                for imp in reversed(imports):
                    newLines.insert(
                        insertionPoint, f'piValueA {defName}.piBody:piDefGC:imports {imp}')
            else:
                # Append at the end
                for imp in imports:
                    newLines.append(
                        f'piValueA {defName}.piBody:piDefGC:imports {imp}')
            changed = True

        return '\n'.join(newLines), changed

    except Exception as e:
        if devExept:
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(f'{tb_str}\n\n --- def updateDefSeedImports', lable.ERROR)
        printIt(f"Error updating def seed imports: {e}", lable.ERROR)
        return seedContent, False


def updateDefSeedFromImports(seedContent: str, defName: str, fromImports: Dict[str, Dict[str, str]]) -> Tuple[str, bool]:
    """Update from imports in piDefGC seed file"""
    printIt('updateDefSeedFromImports', showDefNames03)
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
                contentMatch = re.search(piSeedValuePattern, line)
                if contentMatch:
                    if module_key not in existingFromImports:
                        existingFromImports[module_key] = {}
                    existingFromImports[module_key]['from'] = contentMatch.group(
                        1)
            elif importMatch:
                module_key = importMatch.group(1)
                # Extract the quoted content - use greedy match to handle escaped quotes
                contentMatch = re.search(piSeedValuePattern, line)
                if contentMatch:
                    if module_key not in existingFromImports:
                        existingFromImports[module_key] = {}
                    existingFromImports[module_key]['import'] = contentMatch.group(
                        1)

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
                        clean_module = module_name.replace(
                            '.', '_').replace('-', '_')
                        newLines.append(
                            f'piStructC01 fromImports {clean_module}.')

                    for module_name, import_info in fromImports.items():
                        clean_module = module_name.replace(
                            '.', '_').replace('-', '_')
                        newLines.append(
                            f'piValue {defName}.piBody:piDefGC:fromImports:{clean_module}:from "{import_info["from"]}"')
                        newLines.append(
                            f'piValue {defName}.piBody:piDefGC:fromImports:{clean_module}:import "{import_info["import"]}"')
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
        if devExept:
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(f'{tb_str}\n\n --- def updateDefSeedFromImports', lable.ERROR)
        printIt(f"Error updating def seed from imports: {e}", lable.ERROR)
        return seedContent, False


def updateDefSeedConstants(seedContent: str, defName: str, constants: List[str]) -> Tuple[str, bool]:
    """Update constants in piDefGC seed file"""
    printIt('updateDefSeedConstants', showDefNames03)
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
                if 'mlConstants' in line: print(line)
                match = re.search(piSeedValuePattern, line)
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
                            # constant.replace('"', '\\"')
                            escapedConstant = constant
                            newLines.append(
                                f'piValueA {defName}.piBody:piDefGC:constants "{escapedConstant}"')
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
        if devExept:
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(f'{tb_str}\n\n --- def updateDefSeedConstants', lable.ERROR)
        printIt(f"Error updating def seed constants: {e}", lable.ERROR)
        return seedContent, False


def updateDefSeedFunctionDefs(seedContent: str, defName: str, functionDefs: Dict[str, List[str]]) -> Tuple[str, bool]:
    """Update function definitions in piDefGC seed file"""
    printIt('updateDefSeedFunctionDefs', showDefNames03)
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
                contentMatch = re.search(piSeedValuePattern, line)
                if contentMatch:
                    existingFunctionDefs[funcName].append(
                        contentMatch.group(1))

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

            existing_normalized = normalize_content(
                existingFuncCode[:])  # Make copy
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
                    newLines.append(
                        f'piStructL01 {funcName} \'Function definition for {funcName}\'')

                for funcName, funcLines in functionDefs.items():
                    for funcLine in funcLines:
                        # Fix docstring quotes: convert ''' to ''''
                        if funcLine.strip() == "'''":
                            escapedLine = "''''"
                        else:
                            escapedLine = funcLine.replace('"', '\\"')
                        newLines.append(
                            f'piValueA {defName}.piBody:piDefGC:functionDefs:{funcName} "{escapedLine}"')

                continue
            else:
                newLines.append(line)
                i += 1

        return '\n'.join(newLines), changed

    except Exception as e:
        if devExept:
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(f'{tb_str}\n\n --- def updateDefSeedFunctionDefs', lable.ERROR)
        printIt(f"Error updating def seed function definitions: {e}", lable.ERROR)
        return seedContent, False


def updateDefSeedGlobalCode(seedContent: str, defName: str, globalCode: List[str]) -> Tuple[str, bool]:
    """Update global code in piDefGC seed file"""
    printIt('updateDefSeedGlobalCode', showDefNames03)
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
                match = re.search(piSeedValuePattern, line)
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

        existing_normalized = normalize_content(
            existingGlobalCode[:])  # Make copy
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
                            newLines.append(
                                f'piValueA {defName}.piBody:piDefGC:globalCode "{escapedCode}"')
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
        if devExept:
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(f'{tb_str}\n\n --- def updateDefSeedGlobalCode', lable.ERROR)
        printIt(f"Error updating def seed global code: {e}", lable.ERROR)
        return seedContent, False


def rebuildDefSeedFromPython(pythonFile: Path, piSeedFile: Path, dest_dir: str | None = None) -> List[str]:
    """
    Rebuild the entire piDefGC piSeed file from Python content.
    This is more reliable than trying to update individual sections.
    """
    printIt(f'rebuildDefSeedFromPython: {pythonFile.name}', showDefNames)
    changes = []

    try:
        # Read the Python file
        with open(pythonFile, 'r', encoding='utf-8') as f:
            pythonContent = f.read()

        # Read the existing piSeed file to preserve basic info
        with open(piSeedFile, 'r', encoding='utf-8') as f:
            seedContent = f.read()

        # Extract basic info from existing piSeed
        defName = pythonFile.stem

        # Determine file directory
        if dest_dir is not None:
            fileDirectory = dest_dir
        else:
            try:
                relativeDir = pythonFile.parent.relative_to(Path.cwd())
                fileDirectory = str(relativeDir)
            except ValueError:
                fileDirectory = str(pythonFile.parent)

        # Parse Python file to extract all elements
        try:
            tree = ast.parse(pythonContent)
        except SyntaxError as e:
            printIt(
                f"WARN: Syntax error in {pythonFile.name}: {e}. Cannot create piSeed file.", lable.WARN)
            return changes
        except Exception as e:
            printIt(
                f"WARN: Parse error in {pythonFile.name}: {e}. Cannot create piSeed file.", lable.WARN)
            return changes

        # Extract elements
        regularImports = []
        fromImports = {}
        constants = []
        mlConstants = {}
        functionDefs = {}
        globalCode = []
        headers = []

        # Process top-level nodes
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    import_name = alias.name
                    if alias.asname:
                        import_name = f"{alias.name} as {alias.asname}"
                    regularImports.append(import_name)

            elif isinstance(node, ast.ImportFrom):
                module_name, imports = extract_ImportFrom(node)

                # Clean module name for piSeed structure
                clean_module = module_name.replace('.', '_').replace('-', '_')
                escaped_module = module_name  # module_name.replace(".","//.")
                fromImports[clean_module] = {
                    'from': escaped_module,
                    'import': ', '.join(imports)
                }
            elif isinstance(node, ast.FunctionDef):
                # Extract complete function definition
                isPropertry, funcCode = extractMethodCode(
                    'functions', pythonContent, node)
                functionDefs[node.name] = funcCode

            elif isinstance(node, ast.Assign):
                # Extract constants (module-level assignments)
                constantCode = extractAssignmentCode(pythonContent, node)
                if constantCode:
                    # Check if this is a multi-line constant
                    # Multi-line if: contains newlines OR contains triple quotes (multi-line strings)
                    if '\n' in constantCode or '"""' in constantCode or "'''" in constantCode:
                        # Multi-line constant - extract variable name and store in mlConstants
                        lines = constantCode.split('\n')
                        first_line = lines[0].strip()
                        if '=' in first_line:
                            var_name = first_line.split('=')[0].strip()
                            mlConstants[var_name] = constantCode.split('\n')
                    else:
                        # Single-line constant
                        constants.append(constantCode)

            elif isinstance(node, ast.If):
                # Handle if __name__ == '__main__': blocks
                if isinstance(node.test, ast.Compare):
                    if isinstance(node.test.left, ast.Name):
                        if (node.test.left.id == '__name__' and
                            hasattr(node.test.comparators[0], 's') and
                                node.test.comparators[0].__getattribute__('s') == '__main__'):
                            globalCode.extend(
                                extractIfMainCode(pythonContent, node))
        # Extract file headers from the beginning of the file
        lines = pythonContent.split('\n')
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#'):
                headers.append(stripped)
            elif stripped and not stripped.startswith('#'):
                break
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
        # print('rebuildDefSeedFromPython-fileDirectory', fileDirectory)
        # Build new piSeed content
        newSeedContent = f"""piDefGC {defName} 'Generated piDefGC for {defName} function definitions'
piValue {defName}.piProlog pi.piProlog
piValue {defName}.piBase:piType piDefGC
piValue {defName}.piBase:piTitle {defName}
piValue {defName}.piBase:piSD 'Python function definitions {defName} generated from existing code'
piValue {defName}.piBody:piDefGC:fileDirectory '{fileDirectory}'
piValue {defName}.piBody:piDefGC:fileName {defName}
"""

        # Add headers
        if headers:
            for header in headers:
                escaped_header = header.replace("'", "\\'")
                newSeedContent += f"piValueA {defName}.piBody:piDefGC:headers '{escaped_header}'\n"
        else:
            newSeedContent += f"piValueA {defName}.piBody:piDefGC:headers '# {defName} functions - synced from existing code'\n"

        # Add regular imports
        if regularImports:
            for imp in regularImports:
                newSeedContent += f"piValueA {defName}.piBody:piDefGC:imports {imp}\n"

        # Add from imports
        if fromImports:
            newSeedContent += f"piStructA00 {defName}.piBody:piDefGC:fromImports\n"
            # First add all the structure definitions
            for clean_module in fromImports.keys():
                newSeedContent += f"piStructC01 fromImports {clean_module}.\n"
            # Then add the actual import data
            for clean_module, import_info in fromImports.items():
                newSeedContent += f"piValue {defName}.piBody:piDefGC:fromImports:{clean_module}:from \"{import_info['from']}\"\n"
                newSeedContent += f"piValue {defName}.piBody:piDefGC:fromImports:{clean_module}:import \"{import_info['import']}\"\n"

        # Add constants
        if constants:
            for constant in constants:
                escaped_constant = constant.replace('"', '\\"')
                newSeedContent += f"piValueA {defName}.piBody:piDefGC:constants \"{escaped_constant}\"\n"

        # Add multi-line constants
        if mlConstants:
            newSeedContent += f"piStructA00 {defName}.piBody:piDefGC:mlConstants\n"
            # First add all the structure definitions
            for var_name in mlConstants.keys():
                newSeedContent += f"piStructL01 {var_name} 'Multi-line constant {var_name}'\n"
            # Then add the actual constant lines
            for var_name, constant_lines in mlConstants.items():
                for line in constant_lines:
                    escaped_line = line.replace('"', '\\"')
                    newSeedContent += f"piValueA {defName}.piBody:piDefGC:mlConstants:{var_name} \"{escaped_line}\"\n"
        # Add function definitions
        if functionDefs:
            newSeedContent += f"piStructA00 {defName}.piBody:piDefGC:functionDefs\n"
            # First add all the structure definitions
            for func_name in functionDefs.keys():
                newSeedContent += f"piStructL01 {func_name} 'Function definition for {func_name}'\n"
            # Then add the actual function code
            for func_name, func_code in functionDefs.items():
                for line in func_code:
                    escaped_line = escapeQuotesForPiSeed(line)
                    newSeedContent += f"piValueA {defName}.piBody:piDefGC:functionDefs:{func_name} \"{escaped_line}\"\n"

        # Add global code
        if globalCode:
            for line in globalCode:
                escaped_line = escapeQuotesForPiSeed(line)
                newSeedContent += f"piValueA {defName}.piBody:piDefGC:globalCode \"{escaped_line}\"\n"

        # Compare with existing content
        if newSeedContent.strip() != seedContent.strip():
            # Write the new content
            with open(piSeedFile, 'w', encoding='utf-8') as f:
                f.write(newSeedContent)

            # Determine what changed
            if regularImports:
                changes.append("imports")
            if fromImports:
                changes.append("fromImports")
            if constants:
                changes.append("constants")
            if mlConstants:
                changes.append("mlConstants")
            if functionDefs:
                changes.append("functionDefs")
            if globalCode:
                changes.append("globalCode")
            if headers:
                changes.append("headers")
        return changes

    except Exception as e:
        if devExept:
            tb_str = ''.join(traceback.format_exception(
                None, e, e.__traceback__))
            printIt(f'{tb_str}\n\n --- def rebuildDefSeedFromPython', lable.ERROR)
        printIt(f"Error rebuilding def seed from Python: {e}", lable.ERROR)
        return []
