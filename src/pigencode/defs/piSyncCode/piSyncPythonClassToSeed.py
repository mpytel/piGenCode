import re
import ast
import traceback
from json import dumps
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from ...defs.logIt import printIt, lable
from ...defs.getSeedPath import getSeedPath
from ...classes.piSeeds import extractPiSeed
from .piSyncCodeUtil import extractCodeDocStr, \
                        getNextPiSeedNumber, \
                        getDefDocString, \
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
            seedFileName = seed_file.name
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
        class_info = analyzePythonClassFile(className, pythonFile)
        #hprint(dumps(class_info, indent=2))
        # Create  piClassGC piSeed content following the exact order from piStruct_piClassGC.json
        seedContent = f"piClassGC {className} 'Generated piClassGC for {className} class'\n"
        seedContent += f"piValue {className}.piProlog pi.piProlog\n"
        seedContent += f"piValue {className}.piBase:piType piClassGC\n"
        seedContent += f"piValue {className}.piBase:piTitle {className}\n"
        seedContent += f"piValue {className}.piBase:piSD 'Python class {className} generated from existing code'\n"
        seedContent += f"piValue {className}.piBody:piClassGC:fileDirectory '{fileDirectory}'\n"
        seedContent += f"piValue {className}.piBody:piClassGC:fileName {className}\n"

        # 1. Add from Header comment or docStrings if found (temporarily disabled to fix ordering issue)
        if class_info.get('headers'):
            for line in class_info['headers']:
                seedContent += f'piValueA {className}.piBody:piClassGC:headers "{line}"\n'
        # 2. Add from imports if found (temporarily disabled to fix ordering issue)
        if class_info.get('from_imports'):
            #hprint(dumps(class_info['from_imports'],indent=2))
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

        # 5. Add globals - extract module-level variables
        with open(pythonFile, 'r', encoding='utf-8') as f:
            pythonContent = f.read()
        tree = ast.parse(pythonContent)
        
        # Extract module-level assignments (global variables)
        moduleGlobals = {}
        globalFunctions = []
        
        for node in tree.body:
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                # Module-level variable assignments
                assignmentCode = extractAssignmentCode(pythonContent, node)
                if assignmentCode:
                    # Parse the assignment to extract variable name and value, preserving type annotations
                    if ' = ' in assignmentCode:
                        varPart, varValue = assignmentCode.split(' = ', 1)
                        # Extract variable name but preserve the full assignment including type annotation
                        if ':' in varPart:
                            varName = varPart.split(':')[0].strip()
                            # Store the full assignment including type annotation
                            moduleGlobals[varName] = assignmentCode
                        else:
                            varName = varPart.strip()
                            # Store with just the variable name as key and value
                            moduleGlobals[varName] = varValue
            elif isinstance(node, ast.FunctionDef):
                # Module-level functions
                globalFunctions.append(node)
        
        # Add globals section if we have module assignments
        if moduleGlobals:
            seedContent += f"piStructA00 {className}.piBody:piClassGC:globals\n"
            for varName, varValue in moduleGlobals.items():
                seedContent += f"piValue {className}.piBody:piClassGC:globals:{varName} {varValue}\n"

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

        # 9. Add classComment
        if class_info.get('classComment'):
            spaceOffset = -1
            classComment: str
            for classComment in class_info['classComment']:
                if spaceOffset < 0:
                    spaceOffset = len(classComment) - len(classComment.lstrip())

                seedContent += f'piValueA {className}.piBody:piClassGC:classComment "{classComment[spaceOffset:]}"\n'

        # 10. Add preSuperInitCode
        # 11. Add postSuperInitCode
        # 12. Add init method body if found
        if class_info.get('init_preSuper'):
            for init_line in class_info['init_preSuper']:
                seedContent += f"piValueA {className}.piBody:piClassGC:preSuperInitCode \"{init_line}\"\n"
        if class_info.get('init_postSuper'):
            # printIt(f"class_info['init_postSuper']: {class_info['init_postSuper']}", lable.DEBUG)
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
            classDefCode = f"piStructA00 {className}.piBody:piClassGC:classDefCode\n"
            methodContent = ''
            methodNameSeeds = {}
            methodNameContent = []
            for method_name in class_info['class_methods'].keys():
                if method_name == '__str__':
                    lines = class_info['class_methods'][method_name]
                    for line in lines:
                        seedContent += f'piValueA {className}.piBody:piClassGC:strCode "{line}"\n'
                elif method_name == 'json':
                    lines = class_info['class_methods'][method_name]
                    for line in lines:
                        seedContent += f'piValueA {className}.piBody:piClassGC:jsonCode "{line}"\n'
                else:
                    # First, create the structure entries for each method
                    if method_name not in methodNameSeeds:
                        methodNameSeeds[method_name] = f"piStructL01 {method_name} 'Method {method_name} extracted from existing code'"
                        # Then add the actual code lines for each method
                        line: str
                        method_code: list = class_info['class_methods'][method_name]
                        inLine = 0
                        chk4ADocString = True
                        skipDocStr = True
                        while inLine < len(method_code):
                            line = method_code[inLine]
                            if line.startswith('@'):
                                skipDocStr = False
                                if line.startswith('@property'):
                                    skipDocStr = True
                            if chk4ADocString:
                                if '"""' in line or "'''" in line:
                                    docStr, inLine = getDefDocString(inLine, method_name, methodNameSeeds, method_code)
                                    inLine -= 1
                                    methodNameSeeds[method_name] = docStr
                                    chk4ADocString = False
                            if skipDocStr:
                                if not ('"""' in line or "'''" in line):
                                    methodContent += f"piValueA {className}.piBody:piClassGC:classDefCode:{method_name} \"{line}\"\n"
                            else:
                                methodContent += f"piValueA {className}.piBody:piClassGC:classDefCode:{method_name} \"{line}\"\n"
                            inLine += 1
                        methodNameContent.append(methodNameSeeds[method_name])
            seedContent += classDefCode
            seedContent += '\n'.join(methodNameContent) + '\n'
            seedContent += methodContent
        
        # 17. Add globalCode - extract module-level functions
        if globalFunctions:
            for func in globalFunctions:
                isProperty, funcCode = extractMethodCode('global', pythonContent, func)
                for line in funcCode:
                    seedContent += f"piValueA {className}.piBody:piClassGC:globalCode \"{line}\"\n"
        
        # Write the new piSeed file
        with open(seedFilePath, 'w', encoding='utf-8') as f:
            f.write(seedContent)
        printIt(f"Created new piClassGC piSeed file: {seedFileName}", lable.INFO)
        return seedFilePath

    except Exception as e:
        if devExept:
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(f'{tb_str}\n\n --- def createNewPiClassGCSeedFile', lable.ERROR)
        printIt(
            f"Error creating new piClassGC piSeed file for {className}: {e}", lable.ERROR)
        return None

def _extract_compound_statement(stmt, contentList, lenContent, init_preSuper, init_postSuper, init_body):
    """
    Extract compound statements (if, for, while, etc.) with their complete bodies
    by extracting the source code lines from start to end of the statement.
    Normalizes indentation by removing the base indentation level.
    """
    start_line = stmt.lineno - 1
    end_line = stmt.end_lineno - 1 if hasattr(stmt, 'end_lineno') and stmt.end_lineno else start_line
    
    if start_line < lenContent and end_line < lenContent:
        # Determine the base indentation level from the first line
        first_line = contentList[start_line]
        base_indent = len(first_line) - len(first_line.lstrip())
        
        # Extract all lines from the compound statement
        for line_num in range(start_line, end_line + 1):
            source_line = contentList[line_num].rstrip()
            if source_line.strip():  # Skip empty lines
                # Normalize indentation by removing base indentation
                if len(source_line) >= base_indent and source_line[:base_indent].isspace():
                    normalized_line = source_line[base_indent:]
                else:
                    # Handle lines with less indentation than base (shouldn't happen in well-formed code)
                    normalized_line = source_line.lstrip()
                
                if init_preSuper:
                    init_postSuper.append(normalized_line)
                else:
                    init_body.append(normalized_line)

def analyzePythonClassFile(className: str, pythonFile: Path) -> Dict:
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

        info = {
            'headers': [],
            'imports': [],
            'from_imports': {},
            'classes': [],
            'classComment': [],
            'init_args': {},
            'init_body': [],
            'init_preSupe': [],
            'init_postSuper': [],
            'class_methods': {}
        }
        # Extract headers from content
        codeLines, _ = extractCodeDocStr(contentList)
        info['headers'].extend(codeLines)

        tree = ast.parse(content)
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

                    info['classes'].append(base_names)
                # Extract comments or class docstr from class
                startline = node.lineno
                codeLines, _ = extractCodeDocStr(contentList,startline)
                info['classComment'].extend(codeLines)

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
                                            if isinstance(arg.annotation, ast.Subscript) and isinstance(arg.annotation.value, ast.Name) and arg.annotation.value.id == 'Optional':
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
                                            print('arg_name =', arg_name)
                                            if isinstance(default, ast.Constant):
                                                if isinstance(default.value, str):
                                                    init_args[arg_name]['value'] = f'"{default.value}"'
                                                else:
                                                    init_args[arg_name]['value'] = str(default.value)
                                            elif isinstance(default, ast.Call):
                                                # Handle function calls like PiBase("user", "piDev_piUser65", "root user")
                                                # Extract the source code for this default value
                                                default_line = default.lineno - 1
                                                if default_line < lenContent:
                                                    # Find the default value in the source line
                                                    source_line = contentList[default_line]
                                                    # Extract the part after the '=' sign for this parameter
                                                    if '=' in source_line:
                                                        # Find the parameter name and extract its default value
                                                        # Look for the parameter pattern and then extract the balanced parentheses
                                                        param_start_pattern = rf'\b{re.escape(arg_name)}\s*:\s*[^=]*=\s*'
                                                        match = re.search(param_start_pattern, source_line)
                                                        # add to source line becase the argument is on multiple lines.
                                                        if "(" in source_line:
                                                            while ")" not in source_line:
                                                                print('default_line',default_line)
                                                                default_line += 1
                                                                source_line += contentList[default_line].strip()
                                                        if match:
                                                            start_pos = match.end()
                                                            # Extract the function call with balanced parentheses
                                                            paren_count = 0
                                                            end_pos = start_pos
                                                            in_string = False
                                                            string_char = None
                                                            
                                                            for i, char in enumerate(source_line[start_pos:], start_pos):
                                                                if char in ['"', "'"] and not in_string:
                                                                    in_string = True
                                                                    string_char = char
                                                                elif char == string_char and in_string:
                                                                    in_string = False
                                                                    string_char = None
                                                                elif not in_string:
                                                                    if char == '(':
                                                                        paren_count += 1
                                                                    elif char == ')':
                                                                        paren_count -= 1
                                                                        if paren_count == 0:
                                                                            end_pos = i + 1
                                                                            break
                                                                    elif char == ',' and paren_count == 0:
                                                                        # We've reached the next parameter
                                                                        break
                                                            if paren_count == 0:
                                                                default_value = source_line[start_pos:end_pos].strip()
                                                                # Escape double quotes for piSeed format
                                                                default_value = default_value.replace('"', '\\"')
                                                                init_args[arg_name]['value'] = default_value

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

                                elif isinstance(stmt, ast.AnnAssign):
                                    # Extract annotated assignment statements like userFilePath: Path = self.setPiFileName()
                                    line_num = stmt.lineno - 1
                                    if line_num < lenContent:
                                        assign_line = contentList[line_num].strip()
                                        if init_preSuper:
                                            init_postSuper.append(assign_line)
                                        else:
                                            init_body.append(assign_line)

                                elif isinstance(stmt, ast.For):
                                    # Extract for loops like for piTitle, piSD in baseRealms.items():
                                    _extract_compound_statement(stmt, contentList, lenContent, init_preSuper, init_postSuper, init_body)

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
                                    _extract_compound_statement(stmt, contentList, lenContent, init_preSuper, init_postSuper, init_body)            
                        else:
                            # Extract other class methods for classDefCode
                            isProperty, method_code = extractMethodCode(method_name, content, item)
                            #hprint('method_code', '\n'.join(method_code))
                            defaltCode: list[str] = []
                            if method_code:
                                if isProperty:
                                    if method_name in class_methods:
                                        class_methods[method_name].extend(method_code)
                                    else:
                                        class_methods[method_name] = method_code
                                    #hprint(f'class_methods[{method_name}]--------- ')
                                    #hprint('\n'.join(method_code))
                                elif method_name == '__str__':
                                    indent = ' ' * 4
                                    iniLevel = 0
                                    defaltCode.append(indent*iniLevel + 'def __str__(self) -> str:')
                                    iniLevel += 1
                                    defaltCode.append(f'{indent*iniLevel}""" return string of {className[0].lower()+class_name[1:]} json """')
                                    defaltCode.append(f'{indent*iniLevel}rtnStr = super().__str__()')
                                    defaltCode.append(f'{indent*iniLevel}return rtnStr')
                                elif method_name == 'json':
                                    indent = ' ' * 4
                                    iniLevel = 0
                                    defaltCode.append(indent*iniLevel + 'def json(self) -> dict:')
                                    iniLevel += 1
                                    defaltCode.append(f'{indent*iniLevel}""" return dict of {className[0].lower()+class_name[1:]} json """')
                                    defaltCode.append(f'{indent*iniLevel}rtnDict = super().json()')
                                    defaltCode.append(f'{indent*iniLevel}return rtnDict')
                                else:
                                    class_methods[method_name] = method_code
                            if defaltCode:
                                #hprint('method_code == defaltCode',method_code == defaltCode)
                                if method_code == defaltCode:   
                                    class_methods[method_name] = ''
                                else:
                                    #hprint(f'method_code\n: {method_code}')
                                    #hprint(f'defaltCode\n: {defaltCode}')
                                    class_methods[method_name] = method_code

                info['init_args'] = init_args
                info['init_preSuper'] = init_preSuper
                info['init_postSuper'] = init_postSuper
                info['init_body'] = init_body
                info['class_methods'] = class_methods

                #hprint(f'class_methods[user] act--------- ')
                #hprint('\n'.join(class_methods['user']))
                #hprint(class_methods, dumps(info['class_methods'],indent=2))

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
        #hprint('seedContent00', seedContent)
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
                            #hprint('currDef01',currDef)
                            sections['fromImports'][currDef] = []
                            sections['fromImports'][currDef].append(line)
                        elif 'fromImports' in piTitle:
                            currDef = piTitle.split(':')[-2]
                            #hprint('currDef02',currDef)
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
                            #hprint('currDef01',currDef)
                            sections['initArguments'][currDef] = []
                            sections['initArguments'][currDef].append(line)
                        elif 'initArguments' in piTitle:
                            currDef = piTitle.split(':')[-2]
                            #hprint('currDef02',currDef)
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
                #hprint('** currDef', currDef)
                if currDef == 'piStructA':
                    # here lines is a string for fist line declaring fromImports append
                    result.extend([lines])
                else:
                    # here lines is a list for all piValueA classDefCode code
                    #hprint('** currDef', currDef)
                    #hprint('** lines',lines)
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
        #hprint("sections['globalCode']", sections['globalCode'])
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
