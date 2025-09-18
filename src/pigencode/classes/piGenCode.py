import os, json, ast
import inspect
from pathlib import Path
from ..defs.fileIO import getKeyItem, piGCDirs, readJson, piLoadPiClassGCJson
from ..defs.logIt import logIt, printIt, lable, getCodeFile, getCodeLine

class PiGenCode():
    def __init__(self):
        self.testStr = f'self.testStr: {__name__}'
        indent = 4
        self.indent = ' ' * indent
        self.savedCodeFiles = {}
    def __str__(self) -> str:
        return self.testStr
    def __setPiPiGCAtters(self) -> None:
        #print(json.dumps(self.pi_piClassGC,indent=2))
        #exit()
        self.piClassGC = self.pi_piClassGC["piBody"]["piClassGC"]

        try: self.fileDirectory = self.piClassGC["fileDirectory"]
        except: self.fileDirectory = ""

        try: self.fileName = self.piClassGC["fileName"]
        except: self.fileName = ""

        try: self.headers = self.piClassGC["headers"]
        except: self.headers = []
        try: self.imports = self.piClassGC["imports"]
        except: self.imports = []
        try: self.fromImports = self.piClassGC["fromImports"]
        except: self.fromImports = []
        try: self.fromPiClasses = self.piClassGC["fromPiClasses"]
        except: self.fromPiClasses = []
        try: self.rawFromImports = self.piClassGC["rawFromImports"]
        except: self.rawFromImports = []
        try: self.globals = self.piClassGC["globals"]
        except: self.globals = []
        try: self.piClassName = self.piClassGC["piClassName"]
        except: self.piClassName = ""
        try: self.inheritance = self.piClassGC["inheritance"]
        except: self.inheritance = []
        try:
            self.initArguments = self.piClassGC["initArguments"]
            self.uniqeParametersPiTypes = self.__getuniqeParametersPiTypes()
        except:
            self.initArguments = {}
            self.uniqeParametersPiTypes = {}
        try: self.classComment = self.piClassGC["classComment"]
        except: self.classComment = []
        self.supperSkip = []
        try: self.preSuperInitCode = self.piClassGC["preSuperInitCode"]
        except: self.preSuperInitCode = []
        try: self.postSuperInitCode = self.piClassGC["postSuperInitCode"]
        except: self.postSuperInitCode = []
        try: self.initAppendCode = self.piClassGC["initAppendCode"]
        except: self.initAppendCode = []
        try: self.genProps = self.piClassGC["genProps"]
        except: self.genProps = ""
        try: self.strCode = self.piClassGC["strCode"]
        except: self.strCode = []
        try: self.jsonCode = self.piClassGC["jsonCode"]
        except: self.jsonCode = []
        try: self.classDefCode = self.piClassGC["classDefCode"]
        except: self.classDefCode = {}
        try: self.globalCode = self.piClassGC["globalCode"]
        except: self.globalCode = []
    def __getuniqeParametersPiTypes(self):
        uniqeParametersPiTypes = []
        for parameter in self.initArguments:
            paramType = self.initArguments[parameter]["type"]
            if paramType[:2] == "Pi":
                if not paramType in uniqeParametersPiTypes:
                    uniqeParametersPiTypes.append(paramType)
        return uniqeParametersPiTypes
    def _genClassLine(self, iniLevel=0) -> str:
        indent = self.indent
        rtnLines = indent*iniLevel + f'class {self.piClassName}('
        if not self.inheritance:
            rtnLines += '):\n'
        else:
            removeComma = False
            for inheritClassName in self.inheritance:
                if inheritClassName != "object":
                    rtnLines += f'{inheritClassName}, '
                    
                    # Check if this class is already imported via fromImports before adding to fromPiClasses
                    if inheritClassName[:2] == 'Pi':
                        alreadyImported = False
                        for fromImport in self.fromImports:
                            importList = self.fromImports[fromImport]["import"]
                            # Check if the inheritClassName is in the import list (handle comma-separated imports)
                            if inheritClassName in [imp.strip() for imp in importList.split(',')]:
                                alreadyImported = True
                                break
                        
                        # Only add to fromPiClasses if not already imported
                        if not alreadyImported and inheritClassName not in self.fromPiClasses:
                            self.fromPiClasses.append(inheritClassName)
                    
                    removeComma = True
            if removeComma:
                rtnLines = rtnLines[:-2] + '):\n'
            else:
                rtnLines += '):\n'
        return rtnLines
    def _genInitSuperLine(self, iniLevel=0) -> str:
        indent = self.indent
        rtnLines = ""
        if "object" in self.inheritance:
            rtnLines += indent*(iniLevel) + f'super(object, self).__init__()\n'
        elif "dict" in self.inheritance:
            rtnLines += indent*(iniLevel) + f'super().__init__()\n'
        else:
            supperParameters = {}
            for InheritKey in self.inheritance:
                rtnLines += indent*(iniLevel) + f'super({self.piClassName}, self).__init__(\n'
                try:
                    supperParameters = self.__getInheritClassArgs(InheritKey, self.piClassDir)
                    
                    #aPiFilePI = self.__getInheritClassArgs(InheritKey, self.piClassDir)
                    # if aPiFilePI:
                    #     parameters = aPiFilePI["piBody"]["piClassGC"]["initArguments"]
                    #     supperParameters += [p for p in parameters if not p in supperParameters]
                    # else: raise Exception
                except:
                    printIt(' '.join((getCodeFile(), self.piClassName, f'InheritKey({getCodeLine()}):', InheritKey, str(self.piClassDir))),lable.ERROR)
                    printIt('Check title case for PiClass')
                    exit()
            for param in self.initArguments:
                if param in supperParameters.keys():
                    # supperParameters value is dict
                    # {
                    #     'type': 'str',  # Default type
                    #     'value': '""'   # Default value
                    # }
                    paramType = self.initArguments[param]["type"]
                    # For Pi-types that are assigned in preSuperInitCode, use self.parameter
                    if paramType.startswith("Pi") and any(f"self.{param} = " in line for line in self.preSuperInitCode):
                        rtnLines += f'{indent*(iniLevel+3)} {param} = self.{param},\n'
                    else:
                        rtnLines += f'{indent*(iniLevel+3)} {param} = {param},\n'
                else:
                    paramType = self.initArguments[param]["type"]
                    if paramType[:2] == "Pi":
                        self.supperSkip.append(param)
            if rtnLines[-2:] == ",\n":
                rtnLines = rtnLines[:-2] + ")\n"
            elif rtnLines[-2:] == "(\n":
                rtnLines = rtnLines[:-1] + ")\n"
        return rtnLines
    def _genInitCodeLines(self, iniLevel=0):
        indent = self.indent
        rtnLines = ""
        for param in self.initArguments:
            paramType = self.initArguments[param]["type"]
            if self.inheritance:
                if paramType[:2] != "Pi" and param != 'fileName':
                    rtnLines += indent*iniLevel + f'self.{param} = {param}\n'
                if param in self.supperSkip:
                    rtnLines += indent*iniLevel + f'self.{param} = {param}\n'
                # rtnLines += indent*iniLevel + "self.piJson: dict = {}\n"
                # rtnLines += indent*iniLevel + f'self.piJson["{param}"] = {param}\n'
            else:
                paramType = self.initArguments[param]["type"]
                if paramType[:2] == "Pi":
                    #lowerParamType = paramType[:2].lower() + paramType[2:]
                    rtnLines += indent*iniLevel + f'if {param}: self.{param}: {paramType} = {param}\n'
                    rtnLines += indent*iniLevel + f'else: self.{param} = {paramType}()\n'
                else:
                    rtnLines += indent*iniLevel + f'self.{param} = {param}\n'
        if rtnLines != "": rtnLines += '\n'
        return rtnLines
    def _genClassProperties(self, iniLevel=0):
        indent = self.indent
        rtnLines = ""
        for param in self.initArguments:
            paramType = self.initArguments[param]["type"]
            rtnLines += indent*iniLevel + '@property\n'
            rtnLines += indent*iniLevel + f'def {param}(self): return self._piJson["{param}"]\n'
            rtnLines += indent*iniLevel + f'@{param}.setter\n'
            rtnLines += indent*iniLevel + f'def {param}(self, {param}: {paramType}): self._piJson["{param}"] = {param}\n'
        if rtnLines != "": rtnLines += '\n'
        return rtnLines
    def __appednCodeLine(self,codeLine,iniLevel=0):
        indent = self.indent
        if len(codeLine) > 0:
            # Unescape quotes that were escaped during syncCode process
            unescaped_line = codeLine.replace('\\"', '"')
            rtnLines = indent*iniLevel + unescaped_line + '\n'
        else:
            rtnLines = codeLine + '\n'
        return rtnLines
    def __appendInitCodeLines(self, iniLevel=0):
        rtnLines = ""
        for InitCodeLine in self.initAppendCode:
            rtnLines += self.__appednCodeLine(InitCodeLine, iniLevel)
        rtnLines += '\n'
        return rtnLines
    def _genStrCodeLines(self, iniLevel=0):
        if len(self.strCode) > 0:
            rtnLines = self.__addStrCodeLines(iniLevel)
        else:
            indent = self.indent
            rtnLines = indent*iniLevel + 'def __str__(self) -> str:\n'
            iniLevel += 1
            printIniLevel = 1
            removeLastComma = False
            if self.inheritance:
                for InheritKey in self.inheritance:
                    if InheritKey == 'PiPi':
                        piClassName = self.piClassName[0].lower() + self.piClassName[1:]
                        rtnLines += f"{indent*iniLevel}'''return string of {piClassName} json '''\n"
                        rtnLines += f'{indent*iniLevel}rtnStr = super().__str__()\n'
                        rtnLines += f'{indent*iniLevel}return rtnStr'
                    elif InheritKey != "object" and self.uniqeParametersPiTypes:
                        rtnLines += indent*iniLevel
                        rtnLines += f'rtnStr = "{self.piClassName} = ' + '{\\n"\n'
                        if InheritKey not in self.uniqeParametersPiTypes:
                            # review why we read from an existing python file.
                            # try:
                            #     print('InheritKey',InheritKey)
                            #     aPiFilePI = piLoadPiClassGCJson(InheritKey, self.piClassDir)
                            #     if not aPiFilePI: raise Exception
                            # except:
                            #     printIt(' '.join((getCodeFile(), self.piClassName, f'InheritKey({getCodeLine()}):', InheritKey, str(
                            #         self.piClassDir))), lable.ERROR)
                            #     printIt('Check title case for PiClass')
                            #     exit()
                            parameters = self.__getInheritClassArgs(InheritKey, self.piClassDir)
                            # printIniLevel = 1
                            lowerInheritKey = InheritKey[:2].lower(
                            ) + InheritKey[2:]
                            rtnLines += f'{indent*iniLevel}rtnStr += \'{indent*(printIniLevel)}"{lowerInheritKey}":'
                            rtnLines += '{\\n\'\n'
                            # "title":"{self.title}",\n'
                            printIniLevel += 1
                            for parameter in parameters:
                                rtnLines += f'{indent*iniLevel}rtnStr += f\'{indent*(printIniLevel)}"{parameter}":'
                                rtnLines += '"{self.' + parameter + '}",\\n\'\n'
                            printIniLevel -= 1
                            rtnLines += f'{indent*iniLevel}rtnStr += \'{indent*(printIniLevel)}'
                            rtnLines += '}\\n\'\n'
                        for param in self.initArguments:
                            paramType = self.initArguments[param]["type"]
                            # next add lines for paramaters. Taking account to ignore inhareted parameters
                            if paramType[:2] == "Pi":
                                lowerParamType = paramType[:2].lower() + paramType[2:]
                                # try:
                                #     aPiFilePI = piLoadPiClassGCJson(paramType, self.piClassDir)
                                #     if not aPiFilePI: raise Exception
                                # except:
                                #     printIt(' '.join((getCodeFile(), self.piClassName, f'InheritKey({getCodeLine()}):', InheritKey, str(
                                #         self.piClassDir))), lable.ERROR)
                                #     printIt('Check title case for PiClass')
                                #     exit()
                                parameters = self.__getInheritClassArgs(paramType, self.piClassDir)
                                # parameters = aPiFilePI["piBody"]["piClassGC"]["initArguments"]
                                if paramType not in self.inheritance:
                                    rtnLines += f'{indent*(iniLevel)}rtnStr += \'{indent*(printIniLevel)}"{param}": '
                                    rtnLines += '{' + '\\n\'\n'
                                    printIniLevel += 1
                                    parmLen = len(parameters)
                                    parmIndex = 0
                                    for parameter in parameters:
                                        # print(f'parameter: {parameter}')
                                        if parameter[:2] == 'pi':
                                            rtnLines += f'{indent*(iniLevel)}rtnStr += f\'{indent*(printIniLevel)}"{parameter}":'
                                            rtnLines += '"{self.' + f'{param}.{parameter}' + '}"'
                                            if parmIndex == parmLen - 1:
                                                rtnLines += '\\n\'\n'
                                            else:
                                                rtnLines += ',\\n\'\n'
                                        parmIndex += 1
                                    printIniLevel -= 1
                                    rtnLines += f'{indent*(iniLevel)}rtnStr += \'{indent*(printIniLevel)}'
                                    rtnLines += '},' + '\\n\'\n'
                                else:
                                    for parameter in parameters:
                                        rtnLines += f'{indent*iniLevel}rtnStr += f\'{indent*(printIniLevel)}"{parameter}":'
                                        rtnLines += '"{self.' + f'{param}.{parameter}' + '}",\\n\'\n'
                            elif paramType[:2] == "pi":
                                upperParamType = paramType[:1].upper() + paramType[1:]
                                if upperParamType not in self.inheritance:
                                    rtnLines += f'{indent*iniLevel}rtnStr += f\'{indent*(printIniLevel)}"{param}":'
                                    rtnLines += '"{self.' + param + '}",\\n\'\n'
                            else:
                                rtnLines += f'{indent*iniLevel}rtnStr += f\'{indent*(printIniLevel)}"{param}":'
                                rtnLines += '"{self.' + param + '}",\\n\'\n'
                            removeLastComma = True
                        if removeLastComma:
                            rtnLines = rtnLines[:-5] + '\\n\'\n'

                        rtnLines += indent*iniLevel + 'rtnStr += "' + '}"\n'
                        rtnLines += indent*iniLevel + 'return rtnStr\n'
        rtnLines += '\n'
        return rtnLines
    def _genJsonCodeLines(self, iniLevel=0):
        rtnLines = ''
        InheritKey = ''
        if len(self.jsonCode) > 0:
            rtnLines = self.__addJsonCodeLines(iniLevel)
        elif self.initArguments or self.inheritance:
            indent = self.indent
            rtnLines = indent*iniLevel + 'def json(self) -> dict:\n'
            iniLevel += 1
            compleatCode = False
            try:
                if self.inheritance:
                    # print('self.inheritance',self.piClassName)
                    for InheritKey in self.inheritance:
                        if InheritKey == 'PiPi':
                            piClassName = self.piClassName[0].lower() + self.piClassName[1:]
                            rtnLines += f"{indent*iniLevel}'''return dict of {piClassName} json'''\n"
                            rtnLines += f'{indent*iniLevel}rtnDict = super().json()\n'
                            rtnLines += f'{indent*iniLevel}return rtnDict' + '\n'
                        elif InheritKey != "object" and self.uniqeParametersPiTypes:
                            rtnLines += indent*iniLevel + 'rtnDict = {\n'
                            iniLevel += 1
                            if InheritKey not in self.uniqeParametersPiTypes:
                                # Get list of arguments from inherited classes
                                # aPiFilePI = piLoadPiClassGCJson(InheritKey, self.piClassDir)
                                # if not aPiFilePI:raise Exception
                                # parameters = aPiFilePI["piBody"]["piClassGC"]["initArguments"]
                                parameters = self.__getInheritClassArgs(InheritKey, self.piClassDir)
                                iniLevel += 1
                                for parameter, values in parameters.items():
                                    # only parameter begining with pi are included in json
                                    if parameter[:2] == 'pi':
                                        if parameter in self.initArguments.keys(): chkType = self.initArguments[parameter]['type']
                                        else: chkType = values['type']
                                        if chkType in ['str', 'dict']:
                                            rtnLines += f'{indent*iniLevel}"{parameter}": self.{parameter},\n'
                                        else:
                                            rtnLines += f'{indent*iniLevel}"{parameter}": self.{parameter}.json(),\n'
                                iniLevel -= 1
                            rtnLines = rtnLines[:-2] + '\n'
                            compleatCode = True
                else:
                    # print('not self.inheritance',self.piClassName)
                    for param in self.initArguments:
                        paramType = self.initArguments[param]["type"]
                        # next add lines for paramaters. Taking account to ignore inhareted parameters
                        if paramType[:2] == "Pi":
                            # aPiFilePI = piLoadPiClassGCJson(paramType, self.piClassDir)
                            # if not aPiFilePI:
                            #     raise Exception
                            # parameters = aPiFilePI["piBody"]["piClassGC"]["initArguments"]
                            parameters = self.__getInheritClassArgs(paramType, self.piClassDir)
                            parmLen = 0
                            if paramType != 'PiPi':
                                rtnLines += f'{indent*iniLevel}"{param}":' + '{\n'
                                parmLen = len(parameters)
                                iniLevel += 1
                            parmIndex = 0
                            for parameter, values in parameters.items():
                                if parameter[:2] == 'pi':
                                    chkType = values['type']
                                    # print('parameter:',parameter,'chkType:',chkType)
                                    if chkType in ['int','float','str', 'dict','list']:
                                        rtnLines += f'{indent*iniLevel}"{parameter}": self.{param}.{parameter}'
                                    else:
                                        rtnLines += f'{indent*iniLevel}"{parameter}": self.{param}.{parameter}.json()'
                                    if parmIndex == parmLen - 1:
                                            rtnLines += '\n'
                                    else:
                                            rtnLines += ',\n'
                                    parmIndex += 1
                            if paramType != 'PiPi':
                                iniLevel -= 1
                                rtnLines += f'{indent*(iniLevel)}' + '},\n'
                        elif paramType[:2] == "pi":
                            upperParamType = paramType[:1].upper() + paramType[1:]
                            if upperParamType not in self.inheritance:
                                rtnLines += f'{indent*iniLevel}"{param}": self.{param},\n'
                        elif param != 'fileName':
                            rtnLines += f'{indent*iniLevel}"{param}": self.{param},\n'
                    rtnLines = rtnLines[:-2] + '\n'
                    compleatCode = True
                if compleatCode:
                    iniLevel -= 1
                    if len(self.initArguments) == 1:
                        if self.initArguments[list(self.initArguments.keys())[0]]:
                            rtnLines = rtnLines[:-1] + '{}\n'
                    else:
                        rtnLines += indent*iniLevel + '}\n'
                    rtnLines += indent*iniLevel + 'return rtnDict\n'
                    if rtnLines: rtnLines += '\n'
            except:
                printIt(' '.join((getCodeFile(), self.piClassName, f'InheritKey({getCodeLine()}):', InheritKey, str(self.piClassDir))),lable.ERROR)
                printIt('Check title case for PiClass')
                exit()

        return rtnLines
    def _genFromPiClassesLines(self, iniLevel=0) -> str:
        """Generate DEFAULT fromPiClasses imports when none exist"""
        if not self.initArguments:
            return ""

        # Analyze initArguments to determine what Pi classes need to be imported
        imports = []
        for argName, argData in self.initArguments.items():
            argType = argData.get('type', '')
            if argType.startswith('Pi') and argType not in ['str', 'int', 'float', 'bool', 'dict', 'list']:
                # Convert PiUserProfile -> piUserProfile for import path
                importPath = argType[2:3].lower() + argType[3:] if len(argType) > 2 else argType.lower()
                imports.append(f'from .{importPath} import {argType}')

        return '\n'.join(imports) + '\n' if imports else ""

    def __addFromPiClassesLines(self, iniLevel=0) -> str:
        """Use CUSTOM fromPiClasses imports"""
        rtnLines = ""
        for fromPiClass in self.fromPiClasses:
            rtnLines += fromPiClass + '\n'
        return rtnLines

    def _genGlobalsLines(self, iniLevel=0) -> str:
        """Generate DEFAULT globals when none exist"""
        # Most classes don't need default globals
        return ""

    def __addGlobalsLines(self, iniLevel=0) -> str:
        """Use CUSTOM globals"""
        rtnLines = ""
        for globalLine in self.globals:
            rtnLines += globalLine + '\n'
        return rtnLines

    def _genClassCommentLines(self, iniLevel=0) -> str:
        """Generate DEFAULT class comment when none exists"""
        # Generate a simple default docstring
        indent = self.indent
        return f'{indent * iniLevel}"""\n{indent * iniLevel}{self.piClassName} class\n{indent * iniLevel}"""\n'

    def __addClassCommentLines(self, iniLevel=0) -> str:
        """Use CUSTOM class comment"""
        rtnLines = ""
        for commentLine in self.classComment:
            rtnLines += self.__appednCodeLine(commentLine, iniLevel)
        return rtnLines

    def _genPreSuperInitCodeLines(self, iniLevel=0) -> str:
        """Generate DEFAULT preSuperInitCode when none exists"""
        # Most classes don't need default pre-super init code
        return ""

    def __addPreSuperInitCodeLines(self, iniLevel=0) -> str:
        """Use CUSTOM preSuperInitCode"""
        rtnLines = ""
        for preSuperInitCodeLine in self.preSuperInitCode:
            rtnLines += self.__appednCodeLine(preSuperInitCodeLine, iniLevel)
        return rtnLines

    def _genPostSuperInitCodeLines(self, iniLevel=0) -> str:
        """Generate DEFAULT postSuperInitCode when none exists"""
        # Most classes don't need default post-super init code
        return ""

    def __addPostSuperInitCodeLines(self, iniLevel=0) -> str:
        """Use CUSTOM postSuperInitCode"""
        rtnLines = ""
        for postSuperInitCodeLine in self.postSuperInitCode:
            rtnLines += self.__appednCodeLine(postSuperInitCodeLine, iniLevel)
        return rtnLines

    def _genInitAppendCodeLines(self, iniLevel=0) -> str:
        """Generate DEFAULT initAppendCode when none exists"""
        # Most classes don't need default init append code
        return ""

    def __addInitAppendCodeLines(self, iniLevel=0) -> str:
        """Use CUSTOM initAppendCode"""
        rtnLines = ""
        for initAppendCodeLine in self.initAppendCode:
            rtnLines += self.__appednCodeLine(initAppendCodeLine, iniLevel)
        return rtnLines

    def _genGenPropsLines(self, iniLevel=0) -> str:
        """Generate DEFAULT genProps when none exists"""
        # Most classes don't need default generated properties
        return ""

    def __addGenPropsLines(self, iniLevel=0) -> str:
        """Use CUSTOM genProps"""
        if self.genProps:
            return self.genProps + '\n'
        return ""

    # def _genGlobalCodeLines(self, iniLevel=0) -> str:
    #     """Generate DEFAULT globalCode when none exists"""
    #     # Most classes don't need default global code
    #     return ""

    # def __addGlobalCodeLines(self, iniLevel=0) -> str:
    #     """Use CUSTOM globalCode"""
    #     rtnLines = "\n"
    #     for globalCodeLine in self.globalCode:
    #         rtnLines += self.__appednCodeLine(globalCodeLine, iniLevel)
    #     print('rtnLines')
    #     print(rtnLines)
    #     return rtnLines

    def __addJsonCodeLines(self, iniLevel=0):
        """Use CUSTOM jsonCode"""
        indent = self.indent
        rtnLines = ""
        for JsonCodeLine in self.jsonCode:
            # Unescape quotes that were escaped during syncCode process
            unescaped_line = JsonCodeLine.replace('\\"', '"')
            rtnLines += indent*iniLevel + unescaped_line + '\n'
        return rtnLines
    def __addStrCodeLines(self, iniLevel=0):
        rtnLines = ""
        for StrCodeLine in self.strCode:
            rtnLines += self.__appednCodeLine(StrCodeLine, iniLevel)
        return rtnLines
    def __addDefCodeLines(self, iniLevel=0):
        rtnLines = ""
        method_count = 0
        for DefCode in self.classDefCode:
            if method_count > 0:
                rtnLines += '\n'  # Add blank line between methods
            DefCodeLine: str
            for DefCodeLine in self.classDefCode[DefCode]:
                if '\\n' in DefCodeLine and DefCodeLine.strip()[0] != '#':
                    if DefCodeLine.strip().startswith('"""') or DefCodeLine.strip().startswith("'''"):
                        print(self.piClassName)
                        splitlines = DefCodeLine.split('\\n')
                        for splitline in splitlines:
                            rtnLines += self.__appednCodeLine(splitline, iniLevel)
                else:
                    rtnLines += self.__appednCodeLine(DefCodeLine, iniLevel)
            method_count += 1
        return rtnLines
    def _genInitLines(self, iniLevel=0):
        indent = self.indent
        startDefLine = 'def __init__(self'
        rtnLines = indent*iniLevel + startDefLine
        for param in self.initArguments:
            paramType = self.initArguments[param]["type"]
            if paramType in ["none", "any", "Any",""]:
                if self.initArguments[param]["value"] in ["none",""]:
                    rtnLines += f',\n{indent*(iniLevel+3)} {param}'
                else:
                    rtnLines += f',\n{indent*(iniLevel+3)} {param} = {self.initArguments[param]["value"]}'
            elif paramType == "bool":
                rtnLines += f',\n{indent*(iniLevel+3)} {param}: {paramType} = {self.initArguments[param]["value"]}'
            elif paramType == "str":
                rtnLines += f',\n{indent*(iniLevel+3)} {param}: {paramType} = "{self.initArguments[param]["value"]}"'
            elif paramType == "int":
                rtnLines += f',\n{indent*(iniLevel+3)} {param}: {paramType} = {self.initArguments[param]["value"]}'
            elif paramType == "dict":
                if str(self.initArguments[param]["value"]).lower() == "none":
                    rtnLines += f',\n{indent*(iniLevel+3)} {param}: {paramType} = ' + 'None'
                else:
                    rtnLines += f',\n{indent*(iniLevel+3)} {param}: {paramType} = ' + '{}'
            elif paramType == "list":
                #print(self.initArguments[key]["value"])
                rtnLines += f',\n{indent*(iniLevel+3)} {param}: {paramType} = {self.initArguments[param]["value"]}'
            elif paramType == "Path":
                #print(self.initArguments[key]["value"])
                rtnLines += f',\n{indent*(iniLevel+3)} {param}: {paramType} = {self.initArguments[param]["value"]}'
            elif paramType[:2] == "Pi":
                # Extract base type from union types (e.g., "PiIndexer | None" -> "PiIndexer")
                baseType = paramType.split(' | ')[0].strip()
                
                # Check if this class is already imported via fromImports
                alreadyImported = False
                for fromImport in self.fromImports:
                    importList = self.fromImports[fromImport]["import"]
                    # Check if the baseType is in the import list (handle comma-separated imports)
                    if baseType in [imp.strip() for imp in importList.split(',')]:
                        alreadyImported = True
                        break
                
                # Only add to fromPiClasses if not already imported
                if not alreadyImported and baseType not in self.fromPiClasses: 
                    self.fromPiClasses.append(baseType)
                # Check if the value is None (either None object or string "None")
                paramValue = self.initArguments[param]["value"]
                if paramValue is None or str(paramValue).lower() == "none":
                    # Parameter value is None - use union type syntax
                    # Check if paramType already contains | None to avoid duplication
                    if "| None" in paramType:
                        rtnLines += f',\n{indent*(iniLevel+3)} {param}: {paramType} = None'
                    else:
                        rtnLines += f',\n{indent*(iniLevel+3)} {param}: {paramType} | None = None'
                elif paramValue:
                    # Parameter has a non-None value
                    rtnLines += f',\n{indent*(iniLevel+3)} {param}: {paramType} = ' + f'{paramValue}'
                else:
                    # Parameter has empty value - use default constructor
                    rtnLines += f',\n{indent*(iniLevel+3)} {param}: {paramType} = ' + f'{paramType}()'
            elif "Optional" in paramType:
                if str(self.initArguments[param]["value"]).lower() == "none":
                    rtnLines += f',\n{indent*(iniLevel+3)} {param}: {paramType} = ' + 'None'
                else:
                    rtnLines += f',\n{indent*(iniLevel+3)} {param}: {paramType} = ' + '{}'
            else:
                pass
                # printIt(f'{param} {paramType} from {self.PiFileName} not defined01.',lable.ERROR)
        rtnLines += '):\n'
        if len(self.initArguments) == 0:
            if not (self.preSuperInitCode or \
               self.inheritance or \
               self.postSuperInitCode or \
               self.initAppendCode):
                rtnLines += indent*(iniLevel+1) + 'pass\n'
        iniLevel += 1
        initLines = ""
        addAutoGenInitLines = True
        if self.preSuperInitCode:
            initLines += self.__addPreSuperInitCodeLines(iniLevel)
            addAutoGenInitLines = False
        if initLines: rtnLines += initLines; initLines = ""
        if self.inheritance: 
            rtnLines += self._genInitSuperLine(iniLevel)
        if self.postSuperInitCode:
            initLines += self.__addPostSuperInitCodeLines(iniLevel)
            addAutoGenInitLines = False
        if addAutoGenInitLines: initLines += self._genInitCodeLines(iniLevel)
        if initLines: rtnLines += initLines; initLines = ""
        if self.initAppendCode: initLines += self.__appendInitCodeLines(iniLevel)
        if initLines: rtnLines += initLines; initLines = ""
        if self.genProps: initLines += self._genClassProperties(iniLevel)
        if initLines: rtnLines += initLines; initLines = ""
        # else: rtnLines += indent*iniLevel + "pass\n"
        return rtnLines
    def _genClassLines(self, indent=4, iniLevel=0):
        """Main class generation using unified element-based architecture"""
        rtnLines = self._genClassLine(iniLevel)
        iniLevel += 1

        # Use unified element-based generation for all elements
        classComment = self._generateElementCode('classComment', iniLevel)
        if classComment:
            rtnLines += classComment
        
        initLines = self._genInitLines(iniLevel)  # Init is complex, keep existing logic for now
        if initLines:
            rtnLines += initLines
        
        strCode = self._generateElementCode('strCode', iniLevel)
        if strCode:
            rtnLines += '\n' + strCode  # Add blank line before __str__ method
        
        jsonCode = self._generateElementCode('jsonCode', iniLevel)
        if jsonCode:
            rtnLines += '\n' + jsonCode  # Add blank line before json method

        # Handle classDefCode (custom methods) - keep existing logic for now
        if len(self.classDefCode) > 0:
            classDefLines = self.__addDefCodeLines(iniLevel)
            if classDefLines:
                rtnLines += '\n' + classDefLines  # Add blank line before custom methods

        return rtnLines
    def _genAboveClassLines(self) -> str:
        indent = self.indent
        rtnLines = ''
        haveImports = False
        if len(self.headers) > 0:
            for headerStr in self.headers:
                rtnLines += f'{headerStr}\n'
        if len(self.imports) > 0:
            for importStr in self.imports:
                rtnLines += f'import {importStr}\n'
            haveImports = True
        if len(self.fromImports) > 0:
            for fromImport in self.fromImports:
                rtnLines += f'from {self.fromImports[fromImport]["from"]} import {self.fromImports[fromImport]["import"]}\n'
            haveImports = True
        if len(self.fromPiClasses) > 0:
            # print(self.fromPiClasses)
            for fromPiClasse in self.fromPiClasses:
                checkForTokens = fromPiClasse.split(", ")
                if len(checkForTokens) == 1:
                    rtnLines += f'from .{fromPiClasse[:2].lower() + fromPiClasse[2:]} import {fromPiClasse}\n'
                elif len(checkForTokens) > 1:
                    for token in checkForTokens:
                        if token == checkForTokens[0]:
                            rtnLines += f'from .{token[:2].lower() + token [2:]} import {token}, '
                        else:
                            rtnLines += f'{token}, '
                    # remove last comma-=space and add newline
                    rtnLines = rtnLines[:-2] + '\n'
                else:
                    printIt('No piClass specified for fromPiClasses.',lable.ERROR)
            haveImports = True
        if len(self.rawFromImports) > 0:
            for rawFromImportStr in self.rawFromImports:
                rtnLines += f'{rawFromImportStr}\n'
            haveImports = True
        if haveImports: rtnLines += '\n'
        if len(self.globals) > 0:
            for aGlobal in self.globals:
                globalType = type(self.globals[aGlobal])
                #printIt(str(globalType),lable.DEBUG)
                if globalType == str:
                    # Check if this is a full assignment (contains variable name and type annotation)
                    globalValue = self.globals[aGlobal]
                    if ' = ' in globalValue and globalValue.startswith(aGlobal):
                        # This is a full assignment like "baseRealms: dict = {...}"
                        rtnLines += f'{globalValue}\n'
                    else:
                        # This is just a value, use the old format
                        rtnLines += f'{aGlobal} = {globalValue}\n'
                elif globalType == int:
                    rtnLines += f'{aGlobal} = {self.globals[aGlobal]}\n'
                elif globalType == dict or str(globalType) == "<class 'piPis.piUtilties.piDict2PiDot.PiDot'>":
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
                                rtnLines += f'{aGlobal} = {json.dumps(str(self.globals[aGlobal]),indent=len(indent))}\n'
                    except:
                            rtnLines += f'{aGlobal} = {json.dumps(str(self.globals[aGlobal]),indent=len(indent))}\n'
                elif globalType == list:
                    if len(self.globals[aGlobal]) > 0:
                        rtnLines += f'{aGlobal} = [\n'
                        for listItem in self.globals[aGlobal]:
                            rtnLines += f'{indent}"{listItem}",\n'
                        rtnLines = rtnLines[:-2] + '\n]\n'
                    else:
                        rtnLines += f'{aGlobal} = []\n'
                else:
                    printIt(f'{aGlobal} = {json.dumps(str(self.globals[aGlobal]),indent=len(indent))}')
                    printIt(f'Incorrct type {str(globalType)} for {self.globals[aGlobal]}.',lable.ERROR)
                rtnLines += '\n'
        return rtnLines
    def _genBellowClassLines(self) -> str:
        indent = self.indent
        rtnLines = ''
        if len(self.globalCode) > 0:
            prev_line_was_function_end = False
            for i, globalCode in enumerate(self.globalCode):
                # Unescape quotes that were escaped during syncCode process
                unescaped_line = globalCode.replace('\\"', '"')
                
                # Check if this line starts a new function definition
                is_function_start = unescaped_line.strip().startswith('def ')
                
                # Add blank line before function definitions (except the first one)
                if is_function_start and i > 0:
                    rtnLines += '\n'
                
                rtnLines += f'{unescaped_line}\n'
        return rtnLines

    def __setPiClassDir(self):
        """Set up the piClasses directory for output files"""
        # Check if fileDirectory is specified in the piClassGC configuration
        if self.fileDirectory:
            # Use the specified fileDirectory (can be relative or absolute)
            piClassDir = Path(self.fileDirectory)
        else:
            # Fall back to configured piClassGCDir from .pigencoderc
            piClassDir = Path(getKeyItem(piGCDirs[2]))
        if not piClassDir.is_absolute():
            # If relative, make it relative to current working directory
            piClassDir = Path.cwd().joinpath(piClassDir)

        if not piClassDir.is_dir():
            logIt(f'Make direcory: {piClassDir}')
            piClassDir.mkdir(mode=511, parents=True, exist_ok=True)
        self.piClassDir = piClassDir

    def __updatePiClassTrackingFile(self, fileName):
        """Update the .piclass tracking file with generated filenames"""
        # Place tracking file in the same directory as the generated file
        trackingFile = os.path.join(self.piClassDir, ".piclass")
        generatedFiles = set()

        # Read existing tracking file if it exists
        if os.path.isfile(trackingFile):
            try:
                with open(trackingFile, 'r') as f:
                    # Skip comment lines starting with #
                    generatedFiles = set(line.strip() for line in f if line.strip() and not line.strip().startswith('#'))
            except Exception as e:
                logIt(f'Warning: Could not read tracking file {trackingFile}: {e}')

        # Add the new file (just the filename, not full path)
        generatedFiles.add(os.path.basename(fileName))

        # Write updated tracking file with metadata
        try:
            with open(trackingFile, 'w') as f:
                # Add header comment with directory info
                f.write(f"# piGenCode tracking file for directory: {self.piClassDir}\n")
                f.write(f"# Generated files in this directory:\n")
                for filename in sorted(generatedFiles):
                    f.write(f"{filename}\n")
        except Exception as e:
            logIt(f'Warning: Could not update tracking file {trackingFile}: {e}')

    def __savePiClass(self, piClassLines,verbose=False):
        # Use fileName field if specified, otherwise fall back to piTitle
        # strip out any blank line at the end of piClassLines first
        lastlineNum = len(piClassLines) - 1
        while True:
            if piClassLines[lastlineNum].strip(' ') == '\n':
                piClassLines = piClassLines[:-1]
                lastlineNum -= 1
            else:
                break
        if self.fileName:
            baseFileName = self.fileName
        else:
            baseFileName = self.pi_piClassGC["piBase"]["piTitle"]

        fileName = os.path.join(self.piClassDir, f"{baseFileName}.py")

        if os.path.isfile(fileName):
            if verbose: printIt(f'{fileName}',lable.REPLACED)
        else:
            if verbose: printIt(f'{fileName}',lable.SAVED)
        with open(fileName, 'w') as f:
            f.write(piClassLines)

        # Update tracking file
        self.__updatePiClassTrackingFile(fileName)

        # Use the base filename for the saved files dictionary
        self.savedCodeFiles[fileName] = fileName

    def _genPiClass(self, piJsonFileName, verbose = False) -> None:
        self.pi_piClassGC = readJson(piJsonFileName)
        self.PiFileName = piJsonFileName
        # printIt(f'piJsonFileName: {piJsonFileName}',lable.WARN)
        self.__setPiPiGCAtters()
        self.__setPiClassDir()
        piClassLines = self._genClassLines()
        piClassLines = self._genAboveClassLines() + piClassLines + self._genBellowClassLines()
        # piClassLines += f'\n{self.piClassName}_PI = ' + json.dumps(self.pi_piClassGC,indent=4)
        self.__savePiClass(piClassLines, verbose)
        logIt("GenPiClass: " + piJsonFileName)
    def genPiClasses(self, genFileName='', verbose = False):
        if genFileName:
            self._genPiClass(genFileName, verbose)
        else:
            piGermDir = getKeyItem(piGCDirs[1])
            piJsonGCDir = Path(piGermDir).joinpath(getKeyItem(piGCDirs[2]))
            piJsonGCFilenames = os.listdir(piJsonGCDir)
            piJsonGCFilenames.sort()
            #loop though json files in correct order
            for piJsonGCFilename in piJsonGCFilenames:
                piJsonFileName = os.path.join(piJsonGCDir, piJsonGCFilename)
                self._genPiClass(piJsonFileName)
##### Public Functions
    def _generateElementCode(self, elementName: str, iniLevel: int = 0) -> str:
        """Unified element code generation - determines if custom or default code should be used"""
        elementData = getattr(self, elementName, None)

        # Check if custom code exists and has content
        hasCustomCode = False
        if elementData:
            if isinstance(elementData, list) and len(elementData) > 0:
                hasCustomCode = True
            elif isinstance(elementData, dict) and len(elementData) > 0:
                hasCustomCode = True
            elif isinstance(elementData, str) and elementData.strip():
                hasCustomCode = True

        if hasCustomCode:
            # Custom code exists - use it
            methodName = f'_{self.__class__.__name__}__add{elementName[0].capitalize()+elementName[1:]}Lines'
            if hasattr(self, methodName):
                return getattr(self, methodName)(iniLevel)
        else:
            # No custom code - generate default
            methodName = f'_gen{elementName[0].capitalize()+elementName[1:]}Lines'
            # print('methodName',methodName)
            #-print('\n'.join(dir(self)))
            if hasattr(self, methodName):
                return getattr(self, methodName)(iniLevel)
        return ""

    def getDefaultElementCode(self, elementName: str, iniLevel: int = 0) -> str:
        """Get what the default code should be for a given element - used by syncCode for comparison"""
        methodName = f'_gen{elementName.capitalize()}Lines'
        if hasattr(self, methodName):
            return getattr(self, methodName)(iniLevel)
        return ""

    def __getInheritClassArgs(self, PiClassName, piClassGCDir) -> dict[str, dict]:
        lowerPiClassName = PiClassName[:2].lower() + PiClassName[2:]
        # look in class file for listm of parametersm being inharited as children of paramType
        pythonFile = Path(piClassGCDir).joinpath(lowerPiClassName + '.py')
        #printIt(f'piLoadPiClassGCJson fileName: {str(pythonFile)}', lable.DEBUG)
        init_args = {}
        if pythonFile.is_file():
            with open(pythonFile, 'r', encoding='utf-8') as f:
                content = f.read()
            tree = ast.parse(content)

            for node in tree.body:
                if isinstance(node, ast.ClassDef):
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
                                                arg_info['type'] = str(
                                                    arg.annotation.value)
                                        init_args[arg.arg] = arg_info
        return init_args

def genPiPiClass(genFileName='', verbose = False) -> dict:
    '''Generate python file with genFileName piClassGC file.
       If genFileName is not specified, all piClassGC files in
       scratchPis/piClassGC direcory will be proccessed.
       Returns dirctory of ClassName keyed filename values.'''
    piClassGC = PiGenCode()
    piClassGC.genPiClasses(genFileName, verbose)
    return piClassGC.savedCodeFiles

