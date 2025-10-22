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
        if def_info.get('globalCode'):
            print('pythonFile:',pythonFile)
            for globalCode in def_info['globalCode']:
                escaped_line = escapeQuotesForPiSeed(globalCode)
                seedContent += f"piValueA {defName}.piBody:piDefGC:globalCode \"{escaped_line}\"\n"
            print(seedContent)
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
            'globalCode': []
        }
        import_name = ""
        module_name = ""
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
        # extract the rest of the cope as globalCode elements
        lines = content.split("\n")
        linesLen = len(lines)
        startLine = 0
        if module_name:
            lineNum = 0
            while lineNum < linesLen:
                line = lines[lineNum]
                if f"from {module_name}" in line:
                    startLine = lineNum + 1
                lineNum += 1
        elif import_name:
            lineNum = 0
            while lineNum < linesLen:
                line = lines[lineNum]
                if f"import {import_name}" in line:
                    startLine = lineNum + 1
                lineNum += 1

        lineNum = startLine
        line = lines[lineNum]
        while lineNum < linesLen:
            line = lines[lineNum]
            info['globalCode'].append(line)
            lineNum += 1
        
        return info

    except Exception as e:
        if devExept:
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(f'{tb_str}\n\n --- def analyzePythonDefFile', lable.ERROR)
        printIt(f"Error analyzing Python def file {pythonFile}: {e}", lable.ERROR)
        return {}
