import os, json
from pathlib import Path
from ..defs.fileIO import getKeyItem, piGCDirs
from ..defs.piJsonFile import readJson
from ..defs.logIt import logIt, printIt, label

class PiGenDefCode():
    def __init__(self):
        self.testStr = f'self.testStr: {__name__}'
        indent = 4
        self.indent = ' ' * indent
        self.savedCodeFiles = {}

    def __str__(self) -> str:
        return self.testStr

    def __setPiDefGCAttrs(self) -> None:
        """Extract attributes from piDefGC JSON structure"""
        self.piDefGC = self.pi_piDefGC["piBody"]["piDefGC"]

        try: self.headers = self.piDefGC["headers"]
        except: self.headers = []

        try: self.imports = self.piDefGC["imports"]
        except: self.imports = []

        try: self.fromImports = self.piDefGC["fromImports"]
        except: self.fromImports = {}

        try: self.fromPiClasses = self.piDefGC["fromPiClasses"]
        except: self.fromPiClasses = []

        try: self.rawFromImports = self.piDefGC["rawFromImports"]
        except: self.rawFromImports = []

        try: self.globals = self.piDefGC["globals"]
        except: self.globals = {}

        try: self.fileDirectory = self.piDefGC["fileDirectory"]
        except: self.fileDirectory = ""

        try: self.fileName = self.piDefGC["fileName"]
        except: self.fileName = "functions"

        try: self.fileComment = self.piDefGC["fileComment"]
        except: self.fileComment = []

        try: self.functionDefs = self.piDefGC["functionDefs"]
        except: self.functionDefs = {}

        try: self.constants = self.piDefGC["constants"]
        except: self.constants = []

        try: self.mlConstants = self.piDefGC["mlConstants"]
        except: self.mlConstants = {}

        try: self.globalCode = self.piDefGC["globalCode"]
        except: self.globalCode = []

    def __genHeaderLines(self) -> str:
        """Generate header comment lines"""
        rtnLines = ''
        if len(self.headers) > 0:
            for headerStr in self.headers:
                rtnLines += f'{headerStr}\n'
        return rtnLines

    def __genFileCommentLines(self) -> str:
        """Generate file-level comment lines"""
        rtnLines = ''
        if len(self.fileComment) > 0:
            rtnLines += '"""\n'
            for commentLine in self.fileComment:
                rtnLines += f'{commentLine}\n'
            rtnLines += '"""\n\n'
        return rtnLines

    def __genImportLines(self) -> str:
        """Generate import statements"""
        rtnLines = ''
        haveImports = False

        # Standard imports
        if len(self.imports) > 0:
            for importStr in self.imports:
                rtnLines += f'import {importStr}\n'
            haveImports = True

        # From imports
        if len(self.fromImports) > 0:
            for fromImport in self.fromImports:
                rtnLines += f'from {self.fromImports[fromImport]["from"]} import {self.fromImports[fromImport]["import"]}\n'
            haveImports = True

        # From piClasses imports
        if len(self.fromPiClasses) > 0:
            for fromPiClasse in self.fromPiClasses:
                checkForTokens = fromPiClasse.split(", ")
                if len(checkForTokens) == 1:
                    rtnLines += f'from .{fromPiClasse[:2].lower() + fromPiClasse[2:]} import {fromPiClasse}\n'
                elif len(checkForTokens) > 1:
                    for token in checkForTokens:
                        if token == checkForTokens[0]:
                            rtnLines += f'from .{token[:2].lower() + token[2:]} import {token}, '
                        else:
                            rtnLines += f'{token}, '
                    # remove last comma-space and add newline
                    rtnLines = rtnLines[:-2] + '\n'
                else:
                    printIt('No piClass specified for fromPiClasses.', label.ERROR)
            haveImports = True

        # Raw from imports
        if len(self.rawFromImports) > 0:
            for rawFromImportStr in self.rawFromImports:
                rtnLines += f'{rawFromImportStr}\n'
            haveImports = True

        if haveImports:
            rtnLines += '\n'

        return rtnLines

    def __genConstantLines(self) -> str:
        """Generate module-level constants"""
        rtnLines = ''

        # Global variables from globals dict
        if len(self.globals) > 0:
            for aGlobal in self.globals:
                globalType = type(self.globals[aGlobal])
                if globalType == str:
                    rtnLines += f'{aGlobal} = {self.globals[aGlobal]}\n'
                elif globalType == int:
                    rtnLines += f'{aGlobal} = {self.globals[aGlobal]}\n'
                elif globalType == dict:
                    try:
                        aType = self.globals[aGlobal]["type"]
                        try:
                            aValue = self.globals[aGlobal]["value"]
                            if aType:
                                rtnLines += f'{aGlobal}: {aType} = {aValue}\n'
                            else:
                                rtnLines += f'{aGlobal} = {aValue}\n'
                        except:
                            if len(self.globals[aGlobal].keys()) == 1:
                                rtnLines += f'{aGlobal}: {aType} = None\n'
                            else:
                                rtnLines += f'{aGlobal} = {json.dumps(str(self.globals[aGlobal]), indent=4)}\n'
                    except:
                        rtnLines += f'{aGlobal} = {json.dumps(str(self.globals[aGlobal]), indent=4)}\n'
                elif globalType == list:
                    if len(self.globals[aGlobal]) > 0:
                        rtnLines += f'{aGlobal} = [\n'
                        for listItem in self.globals[aGlobal]:
                            rtnLines += f'    "{listItem}",\n'
                        rtnLines = rtnLines[:-2] + '\n]\n'
                    else:
                        rtnLines += f'{aGlobal} = []\n'
                else:
                    printIt(f'Incorrect type {str(globalType)} for {self.globals[aGlobal]}.', label.ERROR)

        # Constants from constants list
        if len(self.constants) > 0:
            for constantLine in self.constants:
                # Unescape quotes that were escaped during syncCode process
                unescaped_line = constantLine.replace('\\"', '"')
                rtnLines += f'{unescaped_line}\n'

        # Multi-line constants from mlConstants dictionary
        if len(self.mlConstants) > 0:
            for constantName, constantLines in self.mlConstants.items():
                if isinstance(constantLines, list):
                    for line in constantLines:
                        # Unescape quotes that were escaped during syncCode process
                        unescaped_line = line.replace('\\"', '"')
                        rtnLines += f'{unescaped_line}\n'
                else:
                    # Handle case where it's stored as a single string
                    unescaped_line = constantLines.replace('\\"', '"')
                    rtnLines += f'{unescaped_line}\n'

        if rtnLines:
            rtnLines += '\n'

        return rtnLines

    def __genFunctionLines(self) -> str:
        """Generate function definitions"""
        rtnLines = ''

        if len(self.functionDefs) > 0:
            for functionName, functionLines in self.functionDefs.items():
                if isinstance(functionLines, list):
                    for line in functionLines:
                        if '\n' in line:
                            print('- ', line)
                            #line = str(line).replace('\\n', '\\\\n')
                            #print('+ ', line)
                        # Fix docstring quotes: convert '''' to '''
                        if line.strip() == "''''":
                            rtnLines += "    '''\n"
                        else:
                            # Unescape quotes that were escaped during syncCode process
                            unescaped_line = line.replace('\\"', '"')
                            rtnLines += f'{unescaped_line}\n'
                    rtnLines += '\n'  # Add blank line after each function
                else:
                    printIt(f'Warning: Function {functionName} is not a list of lines', label.WARN)

        return rtnLines

    def __genGlobalCodeLines(self) -> str:
        """Generate global code at end of file"""
        rtnLines = ''

        if len(self.globalCode) > 0:
            for globalCodeLine in self.globalCode:
                # Unescape quotes that were escaped during syncCode process
                unescaped_line = globalCodeLine.replace('\\"', '"')
                rtnLines += f'{unescaped_line}\n'

        return rtnLines

    def __setPiDefDir(self):
        """Set up the piDefs directory for output files"""
        # Check if fileDirectory is specified in the piDefGC configuration
        if self.fileDirectory:
            # Use the specified fileDirectory (can be relative or absolute)
            piDefDir = Path(self.fileDirectory)
        else:
            # Fall back to default behavior using RC configuration
            piDefDir = Path(getKeyItem(piGCDirs[3]))
        if not piDefDir.is_absolute():
            piDefDir = Path.cwd().joinpath(piDefDir)

        if not piDefDir.is_dir():
            logIt(f'Make directory: {piDefDir}')
            piDefDir.mkdir(mode=511, parents=True, exist_ok=True)
        self.piDefDir = piDefDir

    def __updatePiDefTrackingFile(self, fileName):
        """Update the .pidefs tracking file with generated filenames"""
        # Place tracking file in the same directory as the generated file
        trackingFile = os.path.join(self.piDefDir, ".pidefs")
        generatedFiles = set()

        # Read existing tracking file if it exists
        if os.path.isfile(trackingFile):
            try:
                with open(trackingFile, 'r') as f:
                    generatedFiles = set(line.strip() for line in f if line.strip())
            except Exception as e:
                logIt(f'Warning: Could not read tracking file {trackingFile}: {e}')

        # Add the new file (just the filename, not full path)
        generatedFiles.add(os.path.basename(fileName))

        # Write updated tracking file with metadata
        try:
            with open(trackingFile, 'w') as f:
                # Add header comment with directory info
                f.write(f"# piGenCode tracking file for directory: {self.piDefDir}\n")
                f.write(f"# Generated files in this directory:\n")
                for filename in sorted(generatedFiles):
                    f.write(f"{filename}\n")
        except Exception as e:
            logIt(f'Warning: Could not update tracking file {trackingFile}: {e}')

    def __savePiDefFile(self, piDefLines, verbose=False):
        """Save the generated Python file"""
        fileName = os.path.join(self.piDefDir, f"{self.fileName}.py")
        if os.path.isfile(fileName):
            if verbose:
                printIt(f'{fileName}', label.REPLACED)
        else:
            if verbose:
                printIt(f'{fileName}', label.SAVED)

        with open(fileName, 'w') as f:
            f.write(piDefLines)

        # Update tracking file
        self.__updatePiDefTrackingFile(fileName)

        self.savedCodeFiles[fileName] = fileName

    def __genPiDefFile(self, piJsonFileName, verbose=False) -> None:
        """Generate a Python function definition file from piDefGC JSON"""
        self.pi_piDefGC = readJson(piJsonFileName)
        self.PiFileName = piJsonFileName

        self.__setPiDefGCAttrs()
        self.__setPiDefDir()

        # Build the complete Python file content
        piDefLines = ""
        piDefLines += self.__genHeaderLines()
        piDefLines += self.__genFileCommentLines()
        piDefLines += self.__genImportLines()
        piDefLines += self.__genConstantLines()
        piDefLines += self.__genFunctionLines()
        piDefLines += self.__genGlobalCodeLines()

        self.__savePiDefFile(piDefLines, verbose)
        logIt("GenPiDefFile: " + piJsonFileName)

    def genPiDefFiles(self, genFileName='', verbose=False):
        """Generate Python function definition files from piDefGC JSON files"""
        if genFileName:
            self.__genPiDefFile(genFileName, verbose)
        else:
            # Process all piDefGC files in the directory
            piGermDir = getKeyItem(piGCDirs[1])  # Get piGermDir
            piJsonDefGCDir = Path(piGermDir).joinpath(getKeyItem(piGCDirs[3]))

            if piJsonDefGCDir.is_dir():
                piJsonDefGCFilenames = os.listdir(piJsonDefGCDir)
                piJsonDefGCFilenames.sort()

                # Loop through JSON files in correct order
                for piJsonDefGCFilename in piJsonDefGCFilenames:
                    if piJsonDefGCFilename.endswith('.json'):
                        piJsonFileName = os.path.join(piJsonDefGCDir, piJsonDefGCFilename)
                        self.__genPiDefFile(piJsonFileName, verbose)
            else:
                printIt(f'piDefGC directory not found: {piJsonDefGCDir}', label.WARN)


##### Public Functions
def genPiDefCode(genFileName='', verbose=False) -> dict:
    '''Generate Python function definition file from piDefGC JSON file.
       If genFileName is not specified, all piDefGC files in
       piGerms/piDefGC directory will be processed.
       Returns dictionary of fileName keyed filename values.'''
    piDefGC = PiGenDefCode()
    piDefGC.genPiDefFiles(genFileName, verbose)
    return piDefGC.savedCodeFiles
