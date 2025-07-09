# Modified syncCode to handle directories and create piSeed files from existing Python code

import os, re, ast, traceback
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from ..classes.argParse import ArgParse
from ..defs.logIt import printIt, lable
from ..defs.piRCFile import getKeyItem

def syncCode(argParse: ArgParse):
    """
    Synchronize changes from modified Python files back to their corresponding piSeed files.
    This command analyzes changes in piClasses and piDefs directories and updates the appropriate piSeed files.
    
    Enhanced to handle:
    - Single files: piGenCode syncCode myfile.py
    - Directories: piGenCode syncCode src/pigencode/piApi
    - Default behavior: piGenCode syncCode (processes configured directories)
    """
    args = argParse.parser.parse_args()
    theArgs = args.arguments
    
    if len(theArgs) > 0:
        # Sync specific file or directory
        target = theArgs[0]
        targetPath = Path(target)
        
        if targetPath.is_file():
            # Single file
            syncSingleFile(target)
        elif targetPath.is_dir():
            # Directory - process all Python files recursively
            syncDirectory(targetPath)
        else:
            # Try to find the file/directory
            if not targetPath.exists():
                printIt(f"Target not found: {target}", lable.ERROR)
                return
    else:
        # Sync all changed files in piClasses and piDefs directories
        syncAllChangedFiles()

def syncDirectory(directory: Path):
    """Sync all Python files in a directory recursively"""
    try:
        printIt(f"Processing directory: {directory}", lable.INFO)
        
        # Find all Python files recursively
        python_files = []
        for py_file in directory.rglob("*.py"):
            # Skip __pycache__ and other system directories
            if "__pycache__" in str(py_file) or ".git" in str(py_file):
                continue
            python_files.append(py_file)
        
        if not python_files:
            printIt(f"No Python files found in {directory}", lable.WARN)
            return
        
        printIt(f"Found {len(python_files)} Python files to process", lable.INFO)
        
        processed = 0
        created_seeds = 0
        errors = 0
        
        for py_file in python_files:
            try:
                printIt(f"Processing: {py_file.relative_to(directory)}", lable.DEBUG)
                
                # Determine if this is a class file or function definition file
                isDefFile = isPythonFileDefType(py_file)
                
                if isDefFile:
                    # Handle as piDefGC
                    defName = py_file.stem
                    piSeedFile = findPiDefGCSeedFile(defName)
                    
                    if not piSeedFile:
                        printIt(f"Creating new piDefGC piSeed file for: {defName}", lable.INFO)
                        piSeedFile = createNewPiDefGCSeedFileEnhanced(defName, py_file)
                        if piSeedFile:
                            created_seeds += 1
                    
                    if piSeedFile:
                        changes = syncPythonDefToSeed(py_file, piSeedFile)
                        if changes:
                            printIt(f"  Synced {len(changes)} changes to {piSeedFile.name}", lable.DEBUG)
                        processed += 1
                    else:
                        printIt(f"  Failed to create piSeed file for {defName}", lable.ERROR)
                        errors += 1
                else:
                    # Handle as piClassGC
                    className = py_file.stem
                    piSeedFile = findPiClassGCSeedFile(className)
                    
                    if not piSeedFile:
                        printIt(f"Creating new piClassGC piSeed file for: {className}", lable.INFO)
                        piSeedFile = createNewPiClassGCSeedFileEnhanced(className, py_file)
                        if piSeedFile:
                            created_seeds += 1
                    
                    if piSeedFile:
                        changes = syncPythonClassToSeed(py_file, piSeedFile)
                        if changes:
                            printIt(f"  Synced {len(changes)} changes to {piSeedFile.name}", lable.DEBUG)
                        processed += 1
                    else:
                        printIt(f"  Failed to create piSeed file for {className}", lable.ERROR)
                        errors += 1
                        
            except Exception as e:
                printIt(f"Error processing {py_file}: {e}", lable.ERROR)
                errors += 1
        
        # Summary
        printIt(f"Directory sync complete:", lable.INFO)
        printIt(f"  Processed: {processed} files", lable.INFO)
        printIt(f"  Created piSeed files: {created_seeds}", lable.INFO)
        printIt(f"  Errors: {errors}", lable.INFO)
        
    except Exception as e:
        tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
        printIt(f'syncDirectory error:\n{tb_str}', lable.ERROR)

def createNewPiClassGCSeedFileEnhanced(className: str, pythonFile: Path) -> Optional[Path]:
    """
    Enhanced version of createNewPiClassGCSeedFile that better handles directory structures
    and creates more complete piSeed files from existing Python code.
    """
    try:
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
            seedPath.mkdir(parents=True, exist_ok=True)
        
        # Get next available number
        nextNum = getNextPiSeedNumber()
        
        # Create new piSeed file name
        seedFileName = f"piSeed{nextNum}_piClassGC_{className}.pi"
        seedFilePath = seedPath / seedFileName
        
        # Determine relative file directory from pythonFile
        try:
            # Get relative path from current directory
            relativeDir = pythonFile.parent.relative_to(Path.cwd())
            fileDirectory = str(relativeDir)
        except ValueError:
            # If not relative to cwd, use absolute path
            fileDirectory = str(pythonFile.parent)
        
        # Analyze the Python file to extract more information
        class_info = analyzePythonClassFile(pythonFile)
        
        # Create enhanced piClassGC piSeed content
        seedContent = f"""piClassGC {className} 'Generated piClassGC for {className} class'
piValue {className}.piProlog pi.piProlog
piValue {className}.piBase:piType piClassGC
piValue {className}.piBase:piTitle {className}
piValue {className}.piBase:piSD 'Python class {className} generated from existing code'
piValue {className}.piBody:piClassGC:fileDirectory '{fileDirectory}'
piValue {className}.piBody:piClassGC:fileName {className}
piValue {className}.piBody:piClassGC:piClassName {className}
piValueA {className}.piBody:piClassGC:headers '# {className} class - synced from existing code'
"""
        
        # Add imports if found
        if class_info.get('imports'):
            for imp in class_info['imports']:
                seedContent += f"piValueA {className}.piBody:piClassGC:imports {imp}\n"
        
        # Add from imports if found
        if class_info.get('from_imports'):
            seedContent += f"piStructA00 {className}.piBody:piClassGC:fromImports\n"
            for module_name, import_info in class_info['from_imports'].items():
                clean_module = module_name.replace('.', '_').replace('-', '_')
                seedContent += f"piStructC01 fromImports {clean_module}.\n"
            for module_name, import_info in class_info['from_imports'].items():
                clean_module = module_name.replace('.', '_').replace('-', '_')
                seedContent += f"piValue {className}.piBody:piClassGC:fromImports:{clean_module}:from \"{import_info['from']}\"\n"
                seedContent += f"piValue {className}.piBody:piClassGC:fromImports:{clean_module}:import \"{import_info['import']}\"\n"
        
        # Add constructor arguments if found
        if class_info.get('init_args'):
            seedContent += f"piStructA00 {className}.piBody:piClassGC:initArguments\n"
            for arg_name in class_info['init_args']:
                seedContent += f"piStructC01 argument {arg_name}.\n"
            for arg_name, arg_info in class_info['init_args'].items():
                seedContent += f"piValue {className}.piBody:piClassGC:initArguments:{arg_name}:type {arg_info.get('type', 'str')}\n"
                seedContent += f"piValue {className}.piBody:piClassGC:initArguments:{arg_name}:value {arg_info.get('value', '\"\"')}\n"
        
        # Write the new piSeed file
        with open(seedFilePath, 'w', encoding='utf-8') as f:
            f.write(seedContent)
        
        printIt(f"Created new piClassGC piSeed file: {seedFileName}", lable.INFO)
        return seedFilePath
        
    except Exception as e:
        printIt(f"Error creating new piClassGC piSeed file for {className}: {e}", lable.ERROR)
        return None

def createNewPiDefGCSeedFileEnhanced(defName: str, pythonFile: Path) -> Optional[Path]:
    """
    Enhanced version of createNewPiDefGCSeedFile that better handles directory structures
    and creates more complete piSeed files from existing Python code.
    """
    try:
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
            seedPath.mkdir(parents=True, exist_ok=True)
        
        # Get next available number
        nextNum = getNextPiSeedNumber()
        
        # Create new piSeed file name
        seedFileName = f"piSeed{nextNum}_piDefGC_{defName}.pi"
        seedFilePath = seedPath / seedFileName
        
        # Determine relative file directory from pythonFile
        try:
            # Get relative path from current directory
            relativeDir = pythonFile.parent.relative_to(Path.cwd())
            fileDirectory = str(relativeDir)
        except ValueError:
            # If not relative to cwd, use absolute path
            fileDirectory = str(pythonFile.parent)
        
        # Analyze the Python file to extract more information
        def_info = analyzePythonDefFile(pythonFile)
        
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
                seedContent += f"piValueA {defName}.piBody:piDefGC:constants \"{constant}\"\n"
        
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
        printIt(f"Error creating new piDefGC piSeed file for {defName}: {e}", lable.ERROR)
        return None

def analyzePythonClassFile(pythonFile: Path) -> Dict:
    """
    Analyze a Python file to extract class information for creating piSeed files.
    Returns dict with imports, from_imports, classes, init_args, etc.
    """
    try:
        with open(pythonFile, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        info = {
            'imports': [],
            'from_imports': {},
            'classes': [],
            'init_args': {},
            'methods': []
        }
        
        # Extract imports and classes
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    import_name = alias.name
                    if alias.asname:
                        import_name = f"{alias.name} as {alias.asname}"
                    info['imports'].append(import_name)
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_name = node.module
                    imports = []
                    for alias in node.names:
                        import_name = alias.name
                        if alias.asname:
                            import_name = f"{alias.name} as {alias.asname}"
                        imports.append(import_name)
                    
                    info['from_imports'][module_name] = {
                        'from': module_name,
                        'import': ', '.join(imports)
                    }
            
            elif isinstance(node, ast.ClassDef):
                class_name = node.name
                info['classes'].append(class_name)
                
                # Look for __init__ method to extract arguments
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                        init_args = {}
                        for arg in item.args.args:
                            if arg.arg != 'self':
                                arg_info = {
                                    'type': 'str',  # Default type
                                    'value': '""'   # Default value
                                }
                                
                                # Try to infer type from annotation
                                if arg.annotation:
                                    if isinstance(arg.annotation, ast.Name):
                                        arg_info['type'] = arg.annotation.id
                                    elif isinstance(arg.annotation, ast.Constant):
                                        arg_info['type'] = str(arg.annotation.value)
                                
                                init_args[arg.arg] = arg_info
                        
                        # Process default values
                        if item.args.defaults:
                            num_defaults = len(item.args.defaults)
                            num_args = len(item.args.args) - 1  # Exclude 'self'
                            
                            for i, default in enumerate(item.args.defaults):
                                arg_index = num_args - num_defaults + i
                                if arg_index >= 0:
                                    arg_name = item.args.args[arg_index + 1].arg  # +1 to skip 'self'
                                    
                                    if arg_name in init_args:
                                        if isinstance(default, ast.Constant):
                                            if isinstance(default.value, str):
                                                init_args[arg_name]['value'] = f'"{default.value}"'
                                            else:
                                                init_args[arg_name]['value'] = str(default.value)
                        
                        info['init_args'] = init_args
                        break
        
        return info
        
    except Exception as e:
        printIt(f"Error analyzing Python class file {pythonFile}: {e}", lable.ERROR)
        return {}

def analyzePythonDefFile(pythonFile: Path) -> Dict:
    """
    Analyze a Python file to extract function definition information for creating piSeed files.
    Returns dict with imports, from_imports, functions, constants, etc.
    """
    try:
        with open(pythonFile, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        info = {
            'imports': [],
            'from_imports': {},
            'functions': [],
            'constants': []
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
                if node.module:
                    module_name = node.module
                    imports = []
                    for alias in node.names:
                        import_name = alias.name
                        if alias.asname:
                            import_name = f"{alias.name} as {alias.asname}"
                        imports.append(import_name)
                    
                    info['from_imports'][module_name] = {
                        'from': module_name,
                        'import': ', '.join(imports)
                    }
            
            elif isinstance(node, ast.FunctionDef):
                info['functions'].append(node.name)
            
            elif isinstance(node, ast.Assign):
                # Extract constants (module-level assignments)
                lines = content.split('\n')
                line_num = node.lineno - 1
                if line_num < len(lines):
                    constant_line = lines[line_num].strip()
                    info['constants'].append(constant_line)
        
        return info
        
    except Exception as e:
        printIt(f"Error analyzing Python def file {pythonFile}: {e}", lable.ERROR)
        return {}

# Import the existing functions we need
from .syncCode import (
    isPythonFileDefType, findPiClassGCSeedFile, findPiDefGCSeedFile, 
    getNextPiSeedNumber, syncPythonClassToSeed, syncPythonDefToSeed,
    syncAllChangedFiles
)
