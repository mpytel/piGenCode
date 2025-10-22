import ast, re
from json import load, loads, dump, JSONDecodeError
from traceback import format_exception
from pathlib import Path
from .logIt import printIt, lable, logIt, cStr, color
import difflib

PiSeedTypes = ["piScratchDir", "piStruct", "piValuesSetD", "piValue", "piClassGC", "piValueA", "piType", "piIndexer"]
piIndexerTypes_S = ["users", "realms", "domains", "subjects"]
piIndexerTypes = ["user", "realm", "domain", "subject"]
from decouple import config
piAPIURL = f'http://{config("piHost")}:{str(config("piPort"))}'

rcFileName = Path.cwd()
rcFileName = rcFileName.joinpath(f'.{rcFileName.name}rc')

baseDir = Path(__file__).resolve().parents[2]
piDirs = {
    "piSeedsDir": "pi/piSeeds",
    "piScratchDir": "pi/scratchPis",
    "piClassGCDir": "pi/scratchPis/piClassGC",
    "piClassDir": "pi/piClasses",
    "pisDir": str(Path.home().joinpath("pis"))
}
def resetPiRC():
    piRC = baseDir.joinpath('.pirc')
    if piRC.is_file(): piRC.unlink()
    for piDir, piDirPathStr in piDirs.items():
        writeRC(piDir, piDirPathStr)
def getKeyItem(key, defultValue="") -> str:
    rtnValue = readRC(key)
    if not rtnValue:
        rtnValue = defultValue
        writeRC(key, rtnValue)
    return rtnValue
def setKeyItem(key, Value):
    writeRC(key, Value)
def delKey(key):
    global rcFileName
    if rcFileName.is_file():
        with open(rcFileName, 'r') as rf:
            rawRC = load(rf)
        del rawRC[key]
    else:
        rawRC = {}
    #print(rawRC)
    with open(rcFileName, 'w') as wf:
        dump(rawRC, wf, indent=2)
def readRC(rcName: str):
    global rcFileName
    if rcFileName.is_file():
        # print(rcFileName)
        try:
            with open(rcFileName, 'r') as rf:
                rawRcJson = load(rf)
        except:
            resetPiRC()
            rcValue = readRC(rcName)
    try:
        rcValue = rawRcJson[rcName]
    except:
        rcValue = None
    return rcValue
def writeRC(rcName: str, rcValue: (int|float|str|list|dict)):
    global rcFileName
    if rcFileName.is_file():
        with open(rcFileName, 'r') as rf:
            rawRC = load(rf)
    else:
        rawRC = {}
    rawRC[rcName] = rcValue
    # print(rawRC)
    with open(rcFileName, 'w') as wf:
        dump(rawRC, wf, indent=2)
def readJson(fileName: str, verbose=True) -> dict:
    rtnDict = {}
    try:
        with open(fileName, 'r') as rf:
            rtnDict = load(rf)
    except FileNotFoundError:
        if verbose: printIt("pi|readJson -", fileName,lable.FileNotFound)
    except JSONDecodeError as e:
        tb_str = ''.join(format_exception(None, e, e.__traceback__))
    return rtnDict
def writeJson(fileName: str, aDict: dict, verbose=True) -> bool:
    rtnBool = False
    try:
        with open(fileName, 'w') as wf:
            dump(aDict, wf, indent=2)
        rtnBool = True
    except FileNotFoundError:
        if verbose: printIt("pi|writeJson -", fileName,lable.FileNotFound)
    except JSONDecodeError as e:
        tb_str = ''.join(format_exception(None, e, e.__traceback__))
        printIt(tb_str,lable.ERROR)
    return rtnBool
def piLoadPiClassGCJson(PiClassName, piClassGCDir) -> dict:
    rtnJson = {}
    lowerPiClassName = PiClassName[:2].lower() + PiClassName[2:]
    # look in class file for listm of parametersm being inharited as children of paramType
    fileName =Path(piClassGCDir).joinpath(lowerPiClassName + '.py')
    printIt(f'piLoadPiClassGCJson fileName: {fileName}',lable.ABORTPRT)
    if fileName.is_file():
        piStartStr = f'{PiClassName}_PI = '
        piJsonStr = ''
        with open(fileName, 'r') as f:
            while line := f.readline():
                if len(piJsonStr) > 0:
                    piJsonStr += line
                else:
                    if piStartStr in line:
                        piJsonStr = line[len(piStartStr):]
        printIt(f'piJsonStr: {piJsonStr}',lable.ABORTPRT)
        rtnJson = loads(piJsonStr)
    else:
        printIt('piLoadPiClassGCJson', fileName,lable.FileNotFound)
    return rtnJson
def writePiLink(piRealm: str, piRootLink: str, piUserLink: str, piPath: Path):
    pass
def getMD5(fileName: str) -> str:
    theJson = readJson(fileName)
    rtnStr: str = ""
    if theJson:
        rtnStr = str(theJson.get("piID"))
    return rtnStr
def updatePiItem(fileName: str, keyPath: str, theValue):
    keys = keyPath.split(".")
    if keys:
        theJson = readJson(fileName)
        if len(keys) == 1:
            theJson[keys[0]] = theValue
        elif len(keys) >= 2:
            aJson = theJson[keys[0]]
            for key in keys[1:-1]:
                aJson = aJson[key]
            aJson[keys[-1]] = theValue
        writeJson(fileName, theJson)
def appendPiListItem(fileName: str, keyPath: str, theValue):
    keys = keyPath.split(".")
    if keys:
        theJson = readJson(fileName)
        if len(keys) == 1:
            theJson[keys[0]].append(theValue)
        elif len(keys) >= 2:
            aJson = theJson[keys[0]]
            for key in keys[1:]:
                aJson = aJson[key]
            aJson.append(theValue)
        writeJson(fileName, theJson)
#   piLn is a soft link to a pi json file using the piID as the link name
def savePiLn(softLinkMD5: Path, fileNameMD5: Path, suppress=True):
    if fileNameMD5:
        softLinkMD5.parent.mkdir(mode=511,parents=True,exist_ok=True)
        if softLinkMD5.is_symlink():
            chkPiFilePath = softLinkMD5.readlink()
            if chkPiFilePath.is_file() and fileNameMD5.is_file() and (chkPiFilePath == fileNameMD5):
                softLinkMD5.unlink()
            elif not chkPiFilePath.is_file():
                logStr, loglbl = (f'Broken link found {chkPiFilePath}', lable.WARN)
                if not suppress: printIt(logStr, loglbl)
                logIt(logStr, loglbl)
                softLinkMD5.unlink()
            if fileNameMD5.is_file():
                if softLinkMD5.is_symlink(): softLinkMD5.unlink()
                softLinkMD5.symlink_to(fileNameMD5)
                logStr, loglbl = (f'Current pi changed: {fileNameMD5}', lable.INFO)
                if not suppress: printIt(logStr, loglbl)
                logIt(logStr, loglbl)
            else:
                logStr, loglbl = (fileNameMD5, lable.FileNotFound)
                if not suppress: printIt(logStr, loglbl)
                logIt(logStr, loglbl)
        else:
            if fileNameMD5.is_file():
                softLinkMD5.symlink_to(fileNameMD5)
                logStr, loglbl = (f'Current pi changed: {fileNameMD5}', lable.INFO)
                if not suppress: printIt(logStr, loglbl)
                logIt(logStr, loglbl)
    else:
        thePiFilePath = softLinkMD5.readlink()
        softLinkMD5.unlink()
        softLinkMD5.symlink_to(thePiFilePath)
def getPisPath() -> Path:
    pisPath = None
    pisPathStr = getKeyItem('pisDir', '')
    if not pisPathStr:
        pisPath = Path.home().joinpath('pis')
        pisPathStr = getKeyItem('pisDir', str(pisPath))
    else:
        pisPath = Path(pisPathStr)
    return pisPath
def highlight_differences(str1, str2):
    diff = difflib.ndiff(str1.splitlines(), str2.splitlines())
    for line in diff:
        if line.startswith('- '):
            print(f"{cStr(line,color.RED)}")  # Blue for lines in str1
        elif line.startswith('+ '):
            print(f"{cStr(line,color.BLUE)}")  # Blue for lines in str1
        else:
            pass
            #print(line)

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
                    
def piLoadPiClassInitVars(PiClassName, piClassGCDir) -> dict:
    piClassInitVars = {}
    piClassInitVars['inheritance'] = False
    info = {
        'init_args': {},
        'init_body': [],
        'init_preSuper': [],
        'init_postSuper': [],
        }
    pythonContent = ""
    lowerPiClassName = PiClassName[:2].lower() + PiClassName[2:]
    # look in class file for listm of parametersm being inharited as children of paramType
    fileName =Path(piClassGCDir).joinpath(lowerPiClassName + '.py')
    if fileName.is_file():
        with open(fileName, 'r') as f:
            pythonContent = f.read()
        pythonContentList = pythonContent.split('\n')
        lenContent = len(pythonContentList)

        tree = ast.parse(pythonContent)

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                # print('class_name',class_name)
                # Create description based on inheritance
                if node.bases:
                    base_name = ""
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            base_name = base.id
                        elif isinstance(base, ast.Attribute):
                            if isinstance(base.value, ast.Name):
                                base_name = f"{base.value.id}.{base.attr}"
                        if base_name == "PiPi":
                            piClassInitVars['inheritance'] = True
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
                            piClassInitVars['init_args'] = {}

                            for arg in item.args.args:
                                if arg.arg != 'self':
                                    arg_info = {
                                        'type': 'str',  # Default type
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
                                                # arg_info['type'] = f"{left_type} | {right_type}"
                                                arg_info['type'] = f"{left_type}"
                                        elif hasattr(arg.annotation, 'slice'):
                                            # Handle generic types like Optional[PiIndexer]
                                            if isinstance(arg.annotation, ast.Subscript) and isinstance(arg.annotation.value, ast.Name) and arg.annotation.value.id == 'Optional':
                                                if isinstance(arg.annotation.slice, ast.Name):
                                                    # arg_info['type'] = f"{arg.annotation.slice.id} | None"
                                                    arg_info['type'] = f"{arg.annotation.slice.id}"
                                    piClassInitVars['init_args'][arg.arg] = arg_info
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
                                                    init_args[arg_name]['value'] = str(default.value)
                                            elif isinstance(default, ast.Call):
                                                # Handle function calls like PiBase("user", "piDev_piUser65", "root user")
                                                # Extract the source code for this default value
                                                default_line = default.lineno - 1
                                                if default_line < lenContent:
                                                    # Find the default value in the source line
                                                    source_line = pythonContentList[default_line]
                                                    # Extract the part after the '=' sign for this parameter
                                                    if '=' in source_line:
                                                        # Find the parameter name and extract its default value
                                                        # Look for the parameter pattern and then extract the balanced parentheses
                                                        param_start_pattern = rf'\b{re.escape(arg_name)}\s*:\s*[^=]*=\s*'
                                                        match = re.search(param_start_pattern, source_line)
                                                        # add to source line becase the argument is on multiple lines.
                                                        if "(" in source_line:
                                                            while ")" not in source_line:
                                                                default_line += 1
                                                                source_line += pythonContentList[default_line].strip()
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
                                        assign_line = pythonContentList[line_num].strip()

                                        # Skip auto-generated assignments (self.param = param)
                                        # These are already handled by __genInitCodeLines
                                        if init_preSuper:
                                            init_postSuper.append(assign_line)
                                        else:
                                            init_body.append(assign_line)

                                elif isinstance(stmt, ast.AnnAssign):
                                    # Extract annotated assignment statements like userFilePath: Path = self.setPiFileName()
                                    line_num = stmt.lineno - 1
                                    if line_num < lenContent:
                                        assign_line = pythonContentList[line_num].strip()
                                        if init_preSuper:
                                            init_postSuper.append(assign_line)
                                        else:
                                            init_body.append(assign_line)

                                elif isinstance(stmt, ast.For):
                                    # Extract for loops like for piTitle, piSD in baseRealms.items():
                                    _extract_compound_statement(stmt, pythonContentList, lenContent, init_preSuper, init_postSuper, init_body)

                                elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                                    # Extract method calls like self.optSwitches = readOptSwitches()
                                    line_num = stmt.lineno - 1
                                    if line_num < lenContent:
                                        call_line = pythonContentList[line_num].strip()
                                        if "super(" in call_line:
                                            # Previous calls are befor supper call
                                            init_preSuper.extend(init_body)
                                            init_body = []

                                            # Capture the complete super() call
                                            super_call_lines = [call_line]
                                            openParentheses = call_line.count('(') - call_line.count(')')
                                            while openParentheses > 0:
                                                line_num += 1
                                                if line_num < lenContent:
                                                    call_line = pythonContentList[line_num].strip()
                                                    super_call_lines.append(call_line)
                                                    openParentheses = openParentheses + call_line.count('(') - call_line.count(')')
                                                else:
                                                    break
                                            # print('super_call_lines','\n'.join(super_call_lines))
                                            # Store the super() call - it will be auto-generated by the code generator
                                            # We don't need to store it explicitly as it's handled by inheritance logic
                                        else:
                                            if init_preSuper:
                                                init_postSuper.append(call_line)
                                            else:
                                                init_body.append(call_line)
                                elif isinstance(stmt, ast.If):
                                    # Extract if statements like if self.packageOK: self.packageOK = self._chkBaseDirs()
                                    _extract_compound_statement(stmt, pythonContentList, lenContent, init_preSuper, init_postSuper, init_body)

                            piClassInitVars['init_preSuper'] = init_preSuper
                            piClassInitVars['init_body'] = init_body
                            piClassInitVars['init_postSuper'] = init_postSuper
    else:
        printIt('piLoadPiClassGCJson', fileName,lable.FileNotFound)
    return piClassInitVars
