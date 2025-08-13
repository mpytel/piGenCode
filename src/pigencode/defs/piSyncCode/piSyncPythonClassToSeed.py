import re
import ast
import traceback
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from ...defs.logIt import printIt, lable
from ...defs.getSeedPath import getSeedPath
from ...classes.piSeeds import extractPiSeed
from .piSyncCodeUtil import getNextPiSeedNumber, \
                        getDocString, \
                        extract_ImportFrom, \
                        extractInitCodeWithComparison, \
                        shouldPreserveElegantPattern, \
                        updateSeedCodeElement, \
                        extractInitArguments, \
                        hasElegantValueReferences, \
                        updateSeedInitArguments, \
                        extractMethodCode, \
                        extractStrCodeWithComparison, \
                        extractJsonCodeWithComparison, \
                        mapMethodToCodeElement, \
                        extractImportStatements, \
                        extractPiClassTypesFromInitArgs, \
                        updateSeedFromImports, \
                        updateSeedImports, \
                        extractAssignmentCode, \
                        updateSeedGlobals, \
                        removeTrailingBlankLines, \
                        escapeQuotesForPiSeed

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


def createNewPiClassGCSeedFile(className: str, pythonFile: Path, seed_file: Path | None = None, dest_dir: str | None = None) -> Optional[Path]:
    """Create a new piClassGC piSeed file for the given class"""
    printIt(f'createNewPiClassGCSeedFile: {className}', showDefNames)
    try:
        seedPath = getSeedPath()
        if seed_file:
            seedFilePath = seed_file
        else:
            # Get next available number
            nextNum = getNextPiSeedNumber()

            # Create new piSeed file name
            seedFileName = f"piSeed{nextNum}_piClassGC_{className}.pi"
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
        class_info = analyzePythonClassFile(pythonFile)
        # print(dumps(class_info, indent=2))
        # Create  piClassGC piSeed content following the exact order from piStruct_piClassGC.json
        seedContent = f"""piClassGC {className} 'Generated piClassGC for {className} class'
piValue {className}.piProlog pi.piProlog
piValue {className}.piBase:piType piClassGC
piValue {className}.piBase:piTitle {className}
piValue {className}.piBase:piSD 'Python class {className} generated from existing code'
piValue {className}.piBody:piClassGC:fileDirectory '{fileDirectory}'
piValue {className}.piBody:piClassGC:fileName {className}
piValueA {className}.piBody:piClassGC:headers '# {className} class - synced from existing code'
"""


        # 2. Add from imports if found (temporarily disabled to fix ordering issue)
        if class_info.get('from_imports'):
            seedContent += f"piStructA00 {className}.piBody:piClassGC:fromImports\n"
            for module_name, import_info in class_info['from_imports'].items():
                clean_module = module_name.replace('.', '_').replace('-', '_')
                seedContent += f"piStructC01 fromImports {clean_module}.\n"
            for module_name, import_info in class_info['from_imports'].items():
                clean_module = module_name.replace('.', '_').replace('-', '_')
                seedContent += f"piValue {className}.piBody:piClassGC:fromImports:{clean_module}:from \"{import_info['from']}\"\n"
                seedContent += f"piValue {className}.piBody:piClassGC:fromImports:{clean_module}:import \"{import_info['import']}\"\n"

        # 1. Add imports if found
        if class_info.get('imports'):
            for imp in class_info['imports']:
                seedContent += f"piValueA {className}.piBody:piClassGC:imports {imp}\n"
        # 3. Add fromPiClasses (empty for now)

        # 4. Add rawFromImports (empty for now)

        # 5. Add globals (will be added by sync function)

        # 6. Add piClassName
        seedContent += f"piValue {className}.piBody:piClassGC:piClassName {class_info['classes'][0]}\n"

        # 7. Add inheritance (empty for now)
        # piValueA piTopic.piBody:piClassGC:inheritance PiPi
        if class_info['classes'][1]:
            for inheritance in class_info['classes'][1]:
                seedContent += f"piValueA {className}.piBody:piClassGC:inheritance {inheritance}\n"


        # 8. Add constructor arguments if found
        if class_info.get('init_args'):
            seedContent += f"piStructA00 {className}.piBody:piClassGC:initArguments\n"
            for arg_name in class_info['init_args']:
                seedContent += f"piStructC01 argument {arg_name}.\n"
            for arg_name, arg_info in class_info['init_args'].items():
                arg_type = arg_info.get('type', 'str')
                arg_value = arg_info.get('value', '""')
                seedContent += f"piValue {className}.piBody:piClassGC:initArguments:{arg_name}:type {arg_type}\n"
                seedContent += f"piValue {className}.piBody:piClassGC:initArguments:{arg_name}:value {arg_value}\n"

        # 9. Add classComment (empty for now)

        # 10. Add preSuperInitCode
        # 11. Add postSuperInitCode
        # 12. Add init method body if found
        if class_info.get('init_preSuper'):
            for init_line in class_info['init_preSuper']:
                seedContent += f"piValueA {className}.piBody:piClassGC:preSuperInitCode \"{init_line}\"\n"
        if class_info.get('init_postSuper'):
            printIt(f"class_info['init_postSuper']: {class_info['init_postSuper']}", lable.DEBUG)
            for init_line in class_info['init_postSuper']:
                seedContent += f"piValueA {className}.piBody:piClassGC:postSuperInitCode \"{init_line}\"\n"
        if class_info.get('init_body'):
            for init_line in class_info['init_body']:
                seedContent += f"piValueA {className}.piBody:piClassGC:initAppendCode \"{init_line}\"\n"
        # 13. Add genProps (empty for now)

        # 14. Add strCode (will be added by sync function)
        # 15. Add jsonCode (will be added by sync function)

        # 16. Add classDefCode (class methods)
        if class_info.get('class_methods'):
            # First, create the structure entries for each method
            seedContent += f"piStructA00 {className}.piBody:piClassGC:classDefCode\n"
            methodNameSeeds = {}
            for method_name in class_info['class_methods'].keys():
                methodNameSeeds[method_name] = f"piStructL01 {method_name} 'Method {method_name} extracted from existing code'\n"
            # Then add the actual code lines for each method
            line: str
            method_code: list
            methodContent = ''
            for method_name, method_code in class_info['class_methods'].items():
                # Look thugh method_code and extract the docString if any
                inLine = 0
                chk4ADocString = True
                while inLine < len(method_code):
                    line = method_code[inLine]
                    if chk4ADocString:
                        if '"""' in line or "'''" in line:
                            docStr, inLine = getDocString(inLine, method_name, methodNameSeeds, method_code)
                            methodNameSeeds[method_name] = docStr
                            chk4ADocString = False
                    if '"""' in line or "'''" in line:
                        pass
                    else:
                        methodContent += f"piValueA {className}.piBody:piClassGC:classDefCode:{method_name} \"{line}\"\n"
                    inLine += 1
                seedContent += methodNameSeeds[method_name]
            seedContent += methodContent
        # 17. Add globalCode (will be added by sync function)
        # Write the new piSeed file
        with open(seedFilePath, 'w', encoding='utf-8') as f:
            f.write(seedContent)
        printIt(
            f"Created new piClassGC piSeed file: {seedFileName}", lable.INFO)
        return seedFilePath

    except Exception as e:
        if devExept:
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(f'{tb_str}\n\n --- def createNewPiClassGCSeedFile', lable.ERROR)
        printIt(
            f"Error creating new piClassGC piSeed file for {className}: {e}", lable.ERROR)
        return None

def analyzePythonClassFile(pythonFile: Path) -> Dict:
    """
    Analyze a Python file to extract class information for creating piSeed files.
    Returns dict with imports, from_imports, classes, init_args, etc.
    """
    printIt('analyzePythonClassFile', showDefNames02)
    try:
        with open(pythonFile, 'r', encoding='utf-8') as f:
            content = f.read()
        contentList = content.split('\n')
        lenContent = len(contentList)
        tree = ast.parse(content)

        info = {
            'imports': [],
            'from_imports': {},
            'classes': [],
            'init_args': {},
            'init_body': [],
            'init_preSupe': [],
            'init_postSuper': [],
            'class_methods': {},
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
                module_name, imports = extract_ImportFrom(node)
                # Don't override module_name - extract_ImportFrom already handles relative imports correctly

                info['from_imports'][module_name] = {
                    'from': module_name,
                    'import': ', '.join(imports)
                }

            elif isinstance(node, ast.ClassDef):
                class_name = node.name
                info['classes'].append(class_name)
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

                info['classes'].append(base_names
                )
                # Extract all methods from the class
                class_methods = {}
                init_args = {}
                init_body = []
                init_preSuper = []
                init_postSuper = []

                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_name = item.name

                        if method_name == '__init__':
                            # Special handling for __init__ method
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
                                        elif isinstance(arg.annotation, ast.BinOp) and isinstance(arg.annotation.op, ast.BitOr):
                                            # Handle union types like PiIndexer | None
                                            left_type = ""
                                            right_type = ""
                                            if isinstance(arg.annotation.left, ast.Name):
                                                left_type = arg.annotation.left.id
                                            if isinstance(arg.annotation.right, ast.Constant) and arg.annotation.right.value is None:
                                                right_type = "None"
                                            elif isinstance(arg.annotation.right, ast.Name):
                                                right_type = arg.annotation.right.id

                                            if left_type and right_type:
                                                arg_info['type'] = f"{left_type} | {right_type}"
                                        elif hasattr(arg.annotation, 'slice'):
                                            # Handle generic types like Optional[PiIndexer]
                                            if isinstance(arg.annotation.value, ast.Name) and arg.annotation.value.id == 'Optional':
                                                if isinstance(arg.annotation.slice, ast.Name):
                                                    arg_info['type'] = f"{arg.annotation.slice.id} | None"

                                    init_args[arg.arg] = arg_info

                            # Process default values
                            if item.args.defaults:
                                num_defaults = len(item.args.defaults)
                                num_args = len(item.args.args) - 1  # Exclude 'self'

                                for i, default in enumerate(item.args.defaults):
                                    arg_index = num_args - num_defaults + i
                                    if arg_index >= 0:
                                        # +1 to skip 'self'
                                        arg_name = item.args.args[arg_index + 1].arg

                                        if arg_name in init_args:
                                            if isinstance(default, ast.Constant):
                                                if isinstance(default.value, str):
                                                    init_args[arg_name]['value'] = f'"{default.value}"'
                                                else:
                                                    init_args[arg_name]['value'] = str(
                                                        default.value)

                            # Extract the __init__ method body for initAppendCode
                            for stmt in item.body:
                                if isinstance(stmt, ast.Assign):
                                    # Extract assignment statements like self.switchFlags = switchFlags
                                    line_num = stmt.lineno - 1
                                    if line_num < lenContent:
                                        assign_line = contentList[line_num].strip()

                                        # Skip auto-generated assignments (self.param = param)
                                        # These are already handled by __genInitCodeLines
                                        is_auto_generated = False
                                        for arg_name in init_args:
                                            if assign_line == f"self.{arg_name} = {arg_name}":
                                                is_auto_generated = True
                                                break

                                        if not is_auto_generated:
                                            if init_preSuper:
                                                init_postSuper.append(assign_line)
                                            else:
                                                init_body.append(assign_line)

                                elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                                    # Extract method calls like self.optSwitches = readOptSwitches()
                                    line_num = stmt.lineno - 1
                                    if line_num < lenContent:
                                        call_line = contentList[line_num].strip()
                                        if "super(" in call_line:
                                            init_preSuper.extend(init_body)
                                            init_body = []

                                            # Capture the complete super() call
                                            super_call_lines = [call_line]
                                            openParentheses = call_line.count('(') - call_line.count(')')
                                            while openParentheses > 0:
                                                line_num += 1
                                                if line_num < lenContent:
                                                    call_line = contentList[line_num].strip()
                                                    super_call_lines.append(call_line)
                                                    openParentheses = openParentheses + call_line.count('(') - call_line.count(')')
                                                else:
                                                    break

                                            # Store the super() call - it will be auto-generated by the code generator
                                            # We don't need to store it explicitly as it's handled by inheritance logic
                                        else:
                                            if init_preSuper:
                                                init_postSuper.append(call_line)
                                            else:
                                                init_body.append(call_line)
                                elif isinstance(stmt, ast.If):
                                    # Extract if statements like if self.packageOK: self.packageOK = self._chkBaseDirs()
                                    line_num = stmt.lineno - 1
                                    if line_num < lenContent:
                                        removeLSpaceCount = len(contentList[line_num])
                                        if_line = contentList[line_num].lstrip()
                                        removeLSpaceCount -= len(if_line)
                                        if_line = if_line.strip()
                                        if init_preSuper:
                                            init_postSuper.append(if_line)
                                        else:
                                            init_body.append(if_line)

                                        # Also extract the body of the if statement
                                        for if_stmt in stmt.body:
                                            if isinstance(if_stmt, ast.Assign):
                                                if_body_line_num = if_stmt.lineno - 1
                                                if if_body_line_num < lenContent:
                                                    if_body_line = contentList[if_body_line_num][removeLSpaceCount:]
                                                    if_body_line = if_body_line.rstrip()
                                                    if init_preSuper:
                                                        init_postSuper.append(if_body_line)
                                                    else:
                                                        init_body.append(if_body_line)

                                        # Handle else clause if present
                                        if stmt.orelse:
                                            for else_stmt in stmt.orelse:
                                                if isinstance(else_stmt, ast.Assign):
                                                    else_line_num = else_stmt.lineno - 1
                                                    if else_line_num < lenContent:
                                                        else_line = contentList[else_line_num][removeLSpaceCount:]
                                                        else_line = else_line.rstrip()
                                                        if init_preSuper:
                                                            init_postSuper.append(else_line)
                                                        else:
                                                            init_body.append(else_line)
                                                elif isinstance(else_stmt, ast.If):
                                                    # Handle elif
                                                    elif_line_num = else_stmt.lineno - 1
                                                    if elif_line_num < lenContent:
                                                        elif_line = contentList[elif_line_num][removeLSpaceCount:]
                                                        elif_line = elif_line.rstrip()
                                                        if init_preSuper:
                                                            init_postSuper.append(elif_line)
                                                        else:
                                                            init_body.append(elif_line)
                        else:
                            # Extract other class methods for classDefCode
                            isProperty, method_code = extractMethodCode(method_name, content, item)
                            if method_code:
                                if isProperty:
                                    if method_name in class_methods:
                                        class_methods[method_name].extend(method_code)
                                    else:
                                        class_methods[method_name] = method_code
                                else:
                                    class_methods[method_name] = method_code

                info['init_args'] = init_args
                info['init_preSuper'] = init_preSuper
                info['init_postSuper'] = init_postSuper
                info['init_body'] = init_body
                info['class_methods'] = class_methods
                # print(class_methods, dumps(info['class_methods'],indent=2))

                break  # Assuming single class per file for piClassGC
        # printPythonFileInfo(pythonFile, info)
        return info

    except Exception as e:
        if devExept:
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(f'{tb_str}\n\n --- def analyzePythonClassFile', lable.ERROR)
        printIt(f"Error analyzing Python class file {pythonFile}: {e}", lable.ERROR)
        return {}

def syncPythonClassToSeed(pythonFile: Path, piSeedFile: Path, options: dict | None = None) -> List[str]:
    """
    Sync changes from Python class file back to piClassGC piSeed file.
    Returns list of changes made.
    """
    printIt(f'syncPythonClassToSeed: {pythonFile.name}', showDefNames)
    changes = []
    if options is None:
        options = {}

    try:
        # Read the Python file and extract method/function bodies
        with open(pythonFile, 'r', encoding='utf-8') as f:
            pythonContent = f.read()

        # Read the piSeed file
        with open(piSeedFile, 'r', encoding='utf-8') as f:
            seedContent = f.read()
        #print('seedContent00', seedContent)
        # Parse Python file to extract methods and code elements

        try:
            tree = ast.parse(pythonContent)
        except SyntaxError as e:
            printIt(
                f"WARN: Syntax error in {pythonFile.name}: {e}. Skipping sync.", lable.WARN)
            return []  # Return empty changes list
        except Exception as e:
            printIt(
                f"WARN: Parse error in {pythonFile.name}: {e}. Skipping sync.", lable.WARN)
            return []  # Return empty changes list

        try:
            className = pythonFile.stem

            # Find class definition and global code
            classNode = None
            globalFunctions = []
            importStatements = []
            moduleAssignments = []  # Add this to capture module-level assignments

            for node in tree.body:
                if isinstance(node, ast.ClassDef) and node.name.lower() == className.lower():
                    classNode = node
                elif isinstance(node, ast.FunctionDef):
                    # Global function
                    globalFunctions.append(node)
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    # Import statements
                    importStatements.append(node)
                elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                    # Module-level variable assignments (like rcFileDir, rcFileName)
                    # Include both regular assignments and annotated assignments (baseRealms: dict = {...})
                    moduleAssignments.append(node)

            if classNode:
                # Process each method in the class
                for item in classNode.body:
                    if isinstance(item, ast.FunctionDef):
                        methodName = item.name
                        if methodName == '__init__':
                            # Special handling for __init__ method - compare with expected method from piSeed
                            initCodeElements = extractInitCodeWithComparison(
                                pythonContent, item, className, seedContent)

                            for codeType, codeLines in initCodeElements.items():
                                # IMPROVED LOGIC: Use intelligent pattern detection instead of force flag
                                if shouldPreserveElegantPattern(seedContent, className, codeType, codeLines, options):
                                    if options.get('stats', False):
                                        printIt(
                                            f"PRESERVE: Skipping {codeType} for {className} - preserving elegant pattern", lable.DEBUG)
                                    continue

                                # Real changes detected - sync them
                                if codeLines:
                                    newSeedContent, changed = updateSeedCodeElement(
                                        seedContent, className, codeType, codeLines
                                    )
                                    if changed:
                                        seedContent = newSeedContent
                                        changes.append(f"{codeType}")

                            # Extract and sync initArguments only if no elegant references exist
                            initArgs = extractInitArguments(item)
                            if initArgs and not hasElegantValueReferences(seedContent, className):
                                newSeedContent, changed = updateSeedInitArguments(seedContent, className, initArgs)
                                if changed:
                                    seedContent = newSeedContent
                                    changes.append("initArguments")
                        elif methodName == '__str__':
                            # IMPROVED LOGIC: Always extract and check for real changes
                            isPropertry, methodCode = extractMethodCode(methodName, pythonContent, item)
                            if methodCode:
                                # Use intelligent pattern detection
                                if shouldPreserveElegantPattern(seedContent, className, 'strCode', methodCode, options):
                                    if options.get('stats', False):
                                        printIt(
                                            f"PRESERVE: strCode for {className} - preserving default pattern", lable.DEBUG)
                                else:
                                    # Real changes detected - sync them
                                    strCodeLines = extractStrCodeWithComparison(
                                        pythonContent, item, className, seedContent)
                                    if strCodeLines:
                                        newSeedContent, changed = updateSeedCodeElement(
                                            seedContent, className, 'strCode', strCodeLines
                                        )
                                        if changed:
                                            seedContent = newSeedContent
                                            changes.append("strCode (__str__)")
                        elif methodName == 'json':
                            # Special handling for json method - compare with expected default method from piGenCode
                            jsonCodeLines = extractJsonCodeWithComparison(
                                pythonContent, item, className, seedContent)

                            # Only sync if there are actual custom jsonCode lines (not default)
                            if jsonCodeLines:
                                newSeedContent, changed = updateSeedCodeElement(
                                    seedContent, className, 'jsonCode', jsonCodeLines
                                )
                                if changed:
                                    seedContent = newSeedContent
                                    changes.append("jsonCode (json)")
                        else:
                            # Map Python method names to piSeed code element names
                            codeElementName = mapMethodToCodeElement(methodName)
                            if codeElementName:
                                isPropertry, methodCode = extractMethodCode(codeElementName, pythonContent, item)

                                # IMPROVED LOGIC: Use intelligent pattern detection for all methods
                                if shouldPreserveElegantPattern(seedContent, className, codeElementName, methodCode, options):
                                    if options.get('stats', False):
                                        printIt(
                                            f"PRESERVE: {codeElementName} for {className} - preserving pattern", lable.DEBUG)
                                    continue  # Skip this sync
                                # Real changes detected - sync them
                                if methodCode:
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
                                        changes.append(
                                            f"{codeElementName} ({methodName})")

            # Handle import statements
            if importStatements:
                fromImports, regularImports = extractImportStatements(
                    importStatements)

                if fromImports:
                    # IMPROVED LOGIC: Filter out Pi class imports that are already handled by initArguments
                    piClassTypes = extractPiClassTypesFromInitArgs(
                        seedContent, className)

                    # Filter out Pi class imports that genCode will automatically generate
                    filteredFromImports = {}
                    for module_name, import_info in fromImports.items():
                        from_part = import_info.get('from', '')
                        import_part = import_info.get('import', '')

                        # Check if this is a Pi class import that's already in initArguments
                        shouldSkip = False
                        if import_part in piClassTypes or module_name in piClassTypes:
                            shouldSkip = True
                            if options.get('stats', False):
                                printIt(
                                    f"SKIP: fromImports for {className} - {import_part} from {from_part} already handled by initArguments", lable.DEBUG)

                        # Also check for common Pi class patterns
                        if (from_part.startswith('.') and import_part.startswith('Pi')) or \
                           (from_part.startswith('pi') and import_part.startswith('Pi')):
                            # Check if the imported class matches any initArgument types
                            for piType in piClassTypes:
                                if import_part == piType or module_name == piType:
                                    shouldSkip = True
                                    if options.get('stats', False):
                                        printIt(
                                            f"SKIP: fromImports for {className} - {import_part} matches initArgument type {piType}", lable.DEBUG)
                                    break

                        if not shouldSkip:
                            filteredFromImports[module_name] = import_info

                    # Only process remaining imports
                    if filteredFromImports:
                        # Convert filtered imports to a list format for shouldPreserveElegantPattern
                        importLines = []
                        for module_name, import_info in filteredFromImports.items():
                            from_part = import_info.get('from', '')
                            import_part = import_info.get('import', '')
                            if from_part and import_part:
                                importLines.append(
                                    f"from {from_part} import {import_part}")

                        if shouldPreserveElegantPattern(seedContent, className, 'fromImports', importLines, options):
                            if options.get('stats', False):
                                printIt(
                                    f"PRESERVE: fromImports for {className} - preserving auto-generated imports", lable.DEBUG)
                        else:
                            # Real changes detected - sync them
                            newSeedContent, changed = updateSeedFromImports(
                                seedContent, className, filteredFromImports
                            )
                            if changed:
                                seedContent = newSeedContent
                                changes.append("fromImports")
                    elif options.get('stats', False):
                        printIt(
                            f"SKIP: All fromImports for {className} filtered out - handled by initArguments", lable.DEBUG)

                if regularImports:
                    newSeedContent, changed = updateSeedImports(
                        seedContent, className, regularImports
                    )
                    if changed:
                        seedContent = newSeedContent
                        changes.append("imports")

            # Handle global functions and code
            if globalFunctions or moduleAssignments:
                globalCode = []
                moduleGlobals = {}

                # Process module-level assignments first (these go in globals, not globalCode)
                for assignment in moduleAssignments:
                    assignmentCode = extractAssignmentCode(
                        pythonContent, assignment)
                    if assignmentCode:
                        # Parse the assignment to extract variable name and value
                        # Handle both "varName = value" and "varName: type = value" formats
                        if ' = ' in assignmentCode:
                            varPart, varValue = assignmentCode.split(' = ', 1)
                            # Extract just the variable name (remove type annotation if present)
                            if ':' in varPart:
                                varName = varPart.split(':')[0].strip()
                            else:
                                varName = varPart.strip()
                            # Store with just the variable name as key
                            moduleGlobals[varName] = varValue

                # Add global functions to globalCode
                for func in globalFunctions:
                    isPropertry, funcCode = extractMethodCode('global',  pythonContent, func)
                    globalCode.extend(funcCode)
                    globalCode.append("")  # Add blank line between functions

                # Update globals section if we have module assignments
                if moduleGlobals:
                    newSeedContent, changed = updateSeedGlobals(
                        seedContent, className, moduleGlobals
                    )
                    if changed:
                        seedContent = newSeedContent
                        changes.append("globals")

                # Update globalCode section if we have global functions
                if globalCode:
                    # Remove trailing blank lines more robustly
                    globalCode = removeTrailingBlankLines(globalCode)

                    newSeedContent, changed = updateSeedCodeElement(
                        seedContent, className, 'globalCode', globalCode
                    )
                    if changed:
                        seedContent = newSeedContent
                        changes.append("globalCode")

            # Write updated piSeed file if changes were made
            if changes:
                # Rebuild the piSeed file in the correct order
                seedContent = rebuildPiSeedInCorrectOrder(
                    seedContent, className)

                with open(piSeedFile, 'w', encoding='utf-8') as f:
                    f.write(seedContent)

        except SyntaxError as e:
            printIt(
                f"Syntax error in Python file {pythonFile}: {e}", lable.ERROR)

    except Exception as e:
        if devExept:
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(f'{tb_str}\n\n --- def syncPythonClassToSeed', lable.ERROR)
        printIt(f"Error syncing {pythonFile} to {piSeedFile}: {e}", lable.ERROR)

    return changes

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
    printIt('updateSeedClassDefCode', showDefNames03)
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
                    escapedCode = escapeQuotesForPiSeed(codeLine)
                    newLines.append(
                        f'piValueA {className}.piBody:piClassGC:classDefCode:{methodName} "{escapedCode}"')
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
            newLines.insert(
                insertIndex, f'piStructA00 {className}.piBody:piClassGC:classDefCode')
            insertIndex += 1
            newLines.insert(
                insertIndex, f'piStructL01 {methodName} \'Custom method {methodName}\'')
            insertIndex += 1

            # Add method code
            for codeLine in methodCode:
                escapedCode = escapeQuotesForPiSeed(codeLine)
                newLines.insert(
                    insertIndex, f'piValueA {className}.piBody:piClassGC:classDefCode:{methodName} "{escapedCode}"')
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
            newLines.insert(
                insertIndex, f'piStructL01 {methodName} \'Custom method {methodName}\'')
            insertIndex += 1

            for codeLine in methodCode:
                escapedCode = escapeQuotesForPiSeed(codeLine)
                newLines.insert(
                    insertIndex, f'piValueA {className}.piBody:piClassGC:classDefCode:{methodName} "{escapedCode}"')
                insertIndex += 1

            changed = True

        return '\n'.join(newLines), changed

    except Exception as e:
        printIt(f"Error updating seed classDefCode: {e}", lable.ERROR)
        return seedContent, False

def rebuildPiSeedInCorrectOrder(seedContent: str, className: str) -> str:
    """
    Rebuild piSeed file content in the correct order according to piStruct_piClassGC.json.
    This ensures all elements appear in the proper sequence.
    """
    printIt(f'rebuildPiSeedInCorrectOrder: {className}', showDefNames)
    try:
        lines = seedContent.split('\n')
        # Parse existing content into sections
        sections = {
            'header': [],
            'fileDirectory': '',
            'fileName': '',
            'headers': [],
            'fromImports': {},
            'imports': [],
            'fromPiClasses': [],
            'rawFromImports': [],
            'globals': {},
            'piClassName': '',
            'inheritance': [],
            'initArguments': {},
            'classComment': [],
            'preSuperInitCode': [],
            'postSuperInitCode': [],
            'initAppendCode': [],
            'genProps': '',
            'strCode': [],
            'jsonCode': [],
            'classDefCode': {},
            'globalCode': []
        }

        # Parse the existing content
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines
            if not line:
                i += 1
                continue

            # Header lines (piClassGC, piProlog, piBase)
            if (line.startswith(f'piClassGC {className}') or
                line.startswith(f'piValue {className}.piProlog') or
                    line.startswith(f'piValue {className}.piBase')):
                sections['header'].append(line)

            # fileDirectory
            elif f'{className}.piBody:piClassGC:fileDirectory' in line:
                sections['fileDirectory'] = line

            # fileName
            elif f'{className}.piBody:piClassGC:fileName' in line:
                sections['fileName'] = line

            # headers
            elif f'{className}.piBody:piClassGC:headers' in line:
                sections['headers'].append(line)

            # fromImports
            elif f'{className}.piBody:piClassGC:fromImports' in line:
                while i < len(line):
                    line = lines[i].strip()
                    if line:
                        piType, piTitle, piSD = extractPiSeed(line)
                        if 'piStructA' in piType and piTitle == f'{className}.piBody:piClassGC:fromImports':
                            sections['fromImports']['piStructA'] = line
                        elif 'piStructC' in piType:
                            currDef = piSD
                            if currDef[-1] == '.':  # strip . copy over key
                                currDef = currDef[:-1]
                            # print('currDef01',currDef)
                            sections['fromImports'][currDef] = []
                            sections['fromImports'][currDef].append(line)
                        elif 'fromImports' in piTitle:
                            currDef = piTitle.split(':')[-2]
                            # print('currDef02',currDef)
                            sections['fromImports'][currDef].append(line)
                        else:
                            i -= 1
                            break
                    i += 1

            # imports
            elif f'{className}.piBody:piClassGC:imports' in line and 'fromImports' not in line:
                sections['imports'].append(line)

            # fromPiClasses  piValueA piPi.piBody:piClassGC:fromPiClasses "PiRealmBody"
            elif f'{className}.piBody:piClassGC:fromPiClasses' in line:
                sections['fromPiClasses'].append(line)

            # rawFromImports
            elif f'{className}.piBody:piClassGC:rawFromImports' in line:
                sections['rawFromImports'].append(line)

            # inheritance
            elif f'{className}.piBody:piClassGC:inheritance' in line:
                sections['inheritance'].append(line)

            # globals
            elif f'{className}.piBody:piClassGC:globals' in line:
                while True:
                    line = lines[i].strip()
                    if line:
                        piType, piTitle, piSD = extractPiSeed(line)
                        if 'piStructA' in piType and piTitle == f'{className}.piBody:piClassGC:globals':
                            sections['globals']['lines'] = []
                            sections['globals']['lines'].append(line)
                        elif 'piValue' == piType:
                            sections['globals']['lines'].append(line)
                        else:
                            i -= 1
                            break
                    i += 1
            # piClassName
            elif f'{className}.piBody:piClassGC:piClassName' in line:
                sections['piClassName'] = line
            # classComment
            elif f'{className}.piBody:piClassGC:classComment' in line:
                sections['classComment'] = line
            # preSuperInitCode
            elif f'{className}.piBody:piClassGC:preSuperInitCode' in line:
                while True:
                    line = lines[i]
                    if f'{className}.piBody:piClassGC:preSuperInitCode' in line:
                        sections['preSuperInitCode'].append(line)
                    else:
                        i -= 1
                        break
                    i += 1
            # postSuperInitCode
            elif f'{className}.piBody:piClassGC:postSuperInitCode' in line:
                while True:
                    line = lines[i]
                    if f'{className}.piBody:piClassGC:postSuperInitCode' in line:
                        sections['postSuperInitCode'].append(line)
                    else:
                        i -= 1
                        break
                    i += 1
            # initArguments
            elif f'{className}.piBody:piClassGC:initArguments' in line:
                while True:
                    line = lines[i].strip()
                    if line:
                        piType, piTitle, piSD = extractPiSeed(line)
                        if 'piStructA' in piType and piTitle == f'{className}.piBody:piClassGC:initArguments':
                            sections['initArguments']['piStructA'] = line
                        elif 'piStructC' in piType:
                            currDef = piSD
                            if currDef[-1] == '.':  # strip . copy over key
                                currDef = currDef[:-1]
                            # print('currDef01',currDef)
                            sections['initArguments'][currDef] = []
                            sections['initArguments'][currDef].append(line)
                        elif 'initArguments' in piTitle:
                            currDef = piTitle.split(':')[-2]
                            # print('currDef02',currDef)
                            sections['initArguments'][currDef].append(line)
                        else:
                            i -= 1
                            break
                    i += 1

            # initAppendCode
            elif f'{className}.piBody:piClassGC:initAppendCode' in line:
                sections['initAppendCode'].append(line)
            # genProps
            elif f'{className}.piBody:piClassGC:genProps' in line:
                sections['genProps'].append(line)
            # strCode
            elif f'{className}.piBody:piClassGC:strCode' in line:
                sections['strCode'].append(line)
            # jsonCode
            elif f'{className}.piBody:piClassGC:jsonCode' in line:
                sections['jsonCode'].append(line)

            # classDefCode
            elif f'{className}.piBody:piClassGC:classDefCode' in line:
                while True:
                    line = lines[i].strip()
                    if line:
                        piType, piTitle, piSD = extractPiSeed(line)
                        if 'piStructA' in piType and piTitle == f'{className}.piBody:piClassGC:classDefCode':
                            sections['classDefCode']['piStructA'] = line
                        elif 'piStructL' in piType:
                            currDef = piTitle
                            sections['classDefCode'][currDef] = []
                            sections['classDefCode'][currDef].append(line)
                        elif 'piValueA' in piType and 'classDefCode' in piTitle:
                            currDef = piTitle.split(':')[-1]
                            sections['classDefCode'][currDef].append(line)
                        else:
                            i -= 1
                            break
                    i += 1
                    if i >= len(lines):
                        break

            # globalCode
            elif f'{className}.piBody:piClassGC:globalCode' in line:
                while True:
                    line = lines[i].strip()
                    if line:
                        piType, piTitle, piSD = extractPiSeed(line)
                        if 'piValueA' in piType:
                            sections['globalCode'].append(line)
                        else:
                            i -= 1
                            break
                    i += 1
                    if i >= len(lines):
                        break
            i += 1
        #  ------ end with ----

        # Rebuild in correct order
        result = []

        # 1. Header
        result.extend(sections['header'])

        # 2. fileDirectory
        if sections['fileDirectory']:
            result.append(sections['fileDirectory'])

        # 3. fileName
        if sections['fileName']:
            result.append(sections['fileName'])

        # 4. headers
        result.extend(sections['headers'])

        # 5. imports
        result.extend(sections['imports'])

        # 6. fromImports
        fromImports = sections['fromImports']
        if fromImports:
            capturedLines = []
            for currDef, lines in fromImports.items():
                # print('** currDef', currDef)
                if currDef == 'piStructA':
                    # here lines is a string for fist line declaring fromImports append
                    result.extend([lines])
                else:
                    # here lines is a list for all piValueA classDefCode code
                    # print('** currDef', currDef)
                    # print('** lines',lines)
                    assert len(lines) == 3
                    result.extend(lines[:1])
                    capturedLines.extend(lines[1:])
            result.extend(capturedLines)

        # 7. fromPiClasses
        result.extend(sections['fromPiClasses'])

        # 8. rawFromImports
        result.extend(sections['rawFromImports'])

        # 9. globals
        if sections['globals']:
            result.extend(sections['globals']['lines'])

        # 10. piClassName
        if sections['piClassName']:
            result.append(sections['piClassName'])

        # 11. inheritance
        if sections['inheritance']:
            result.extend(sections['inheritance'])

        # 12. initArguments
        capturedLines = []
        initArguments = sections['initArguments']
        if initArguments:
            for currDef, lines in initArguments.items():
                if currDef == 'piStructA':
                    # here lines is a string for fist line declaring classDefCode append
                    result.extend([lines])
                else:
                    result.extend(lines[:1])
                    capturedLines.extend(lines[1:])
            result.extend(capturedLines)

        # 13. classComment
        result.extend(sections['classComment'])
        # 14. preSuperInitCode
        result.extend(sections['preSuperInitCode'])
        # 15. postSuperInitCode
        result.extend(sections['postSuperInitCode'])
        # 16. initAppendCode
        result.extend(sections['initAppendCode'])
        # 17. genProps
        result.extend(sections['genProps'])
        # 18. strCode
        result.extend(sections['strCode'])
        # 19. jsonCode
        result.extend(sections['jsonCode'])
        # 20. classDefCode
        capturedLines = []
        classDefCode = sections['classDefCode']
        if classDefCode:
            for currDef, lines in classDefCode.items():
                if currDef == 'piStructA':
                    # here lines is a string for fist line declaring classDefCode append
                    result.extend([lines])
                else:
                    result.extend(lines[:1])
                    capturedLines.extend(lines[1:])
            result.extend(capturedLines)
        # 21. globalCode
        #print("sections['globalCode']", sections['globalCode'])
        result.extend(sections['globalCode'])
        # i = 1
        # for i1 in result:
        #     print(i,i1)
        #     i += 1
        return '\n'.join(result)

    except Exception as e:
        if devExept:
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(f'{tb_str}\n\n --- def rebuildPiSeedInCorrectOrder', lable.ERROR)
        printIt(f"Error rebuilding piSeed order: {e}", lable.ERROR)
        return seedContent
