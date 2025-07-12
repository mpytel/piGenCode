
import os, json
import inspect
from pathlib import Path
from ..defs.fileIO import readRC, writeRC, piDirs, readJson, piLoadPiClassGCJson, PiSeedTypes
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
    def __genClassLine(self, iniLevel=0) -> str:
        indent = self.indent
        rtnLines = indent*iniLevel + f'class {self.piClassName}('
        if not self.inheritance:
            rtnLines += '):\n\n'
        else:
            removeComma = False
            for inheritClassName in self.inheritance:
                if inheritClassName != "object":
                    rtnLines += f'{inheritClassName}, '
                    if inheritClassName[:2] == 'Pi' and inheritClassName not in self.fromPiClasses: self.fromPiClasses.append(inheritClassName)
                    removeComma = True
            if removeComma:
                rtnLines = rtnLines[:-2] + '):\n\n'
            else:
                rtnLines += '):\n\n'
        return rtnLines
    def __genInitSuperLine(self, iniLevel=0) -> str:
        indent = self.indent
        rtnLines = ""
        if "object" in self.inheritance:
            rtnLines += indent*(iniLevel) + f'super(object, self).__init__()\n'
        elif "dict" in self.inheritance:
            rtnLines += indent*(iniLevel) + f'super().__init__()\n'
        else:
            rtnLines += indent*(iniLevel) + f'super({self.piClassName}, self).__init__(\n'
            supperParameters = []
            for InheritKey in self.inheritance:
                try:
                    aPiFilePI = piLoadPiClassGCJson(InheritKey, self.piClassDir)
                    if aPiFilePI:
                        parameters = aPiFilePI["piBody"]["piClassGC"]["initArguments"]
                        supperParameters += [p for p in parameters if not p in supperParameters]
                    else: raise Exception
                except:
                    printIt(' '.join((getCodeFile(), self.piClassName, f'InheritKey({getCodeLine()}):', InheritKey, str(self.piClassDir))),lable.ERROR)
                    printIt('Check title case for PiClass')
                    exit()
            for param in self.initArguments:
                if param in supperParameters:
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
    def __genInitCodeLines(self, iniLevel=0):
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
    def __genClassProperties(self, iniLevel=0):
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
            rtnLines = indent*iniLevel + codeLine + '\n'
        else:
            rtnLines = codeLine + '\n'
        return rtnLines
    def __appendInitCodeLines(self, iniLevel=0):
        rtnLines = ""
        for InitCodeLine in self.initAppendCode:
            rtnLines += self.__appednCodeLine(InitCodeLine, iniLevel)
        rtnLines += '\n'
        return rtnLines
    def __genStrCodeLines(self, iniLevel=0):
        if len(self.strCode) > 0:
            rtnLines = self.__addStrCodeLines(iniLevel)
        else:
            indent = self.indent
            rtnLines = indent*iniLevel + 'def __str__(self):\n'
            iniLevel += 1
            rtnLines += indent*iniLevel + \
                f'rtnStr = "{self.piClassName} = ' + '{\\n"\n'
            printIniLevel = 1
            removeLastComma = False
            if self.inheritance:
                for InheritKey in self.inheritance:
                    if InheritKey != "object" and self.uniqeParametersPiTypes:
                        if InheritKey not in self.uniqeParametersPiTypes:
                            # review why we read from an existing python file.
                            try:
                                aPiFilePI = piLoadPiClassGCJson(InheritKey, self.piClassDir)
                                if not aPiFilePI: raise Exception
                            except:
                                printIt(' '.join((getCodeFile(), self.piClassName, f'InheritKey({getCodeLine()}):', InheritKey, str(
                                    self.piClassDir))), lable.ERROR)
                                printIt('Check title case for PiClass')
                                exit()
                            parameters = aPiFilePI["piBody"]["piClassGC"]["initArguments"]
                            # printIniLevel = 1
                            lowerInheritKey = InheritKey[:2].lower(
                            ) + InheritKey[2:]
                            rtnLines += f'{indent*iniLevel}rtnStr += \'{indent*(printIniLevel)}"{lowerInheritKey}":' + \
                                '{\\n\'\n'
                            # "title":"{self.title}",\n'
                            printIniLevel += 1
                            for parameter in parameters:
                                rtnLines += f'{indent*iniLevel}rtnStr += f\'{indent*(printIniLevel)}"{parameter}":' + \
                                    '"{self.' + parameter + '}",\\n\'\n'
                            printIniLevel -= 1
                            rtnLines += f'{indent*iniLevel}rtnStr += \'{indent*(printIniLevel)}' + \
                                '}\\n\'\n'
            for param in self.initArguments:
                paramType = self.initArguments[param]["type"]
                # next add lines for paramaters. Taking account to ignore inhareted parameters
                if paramType[:2] == "Pi":
                    lowerParamType = paramType[:2].lower() + paramType[2:]
                    try:
                        aPiFilePI = piLoadPiClassGCJson(paramType, self.piClassDir)
                        if not aPiFilePI: raise Exception
                    except:
                        printIt(' '.join((getCodeFile(), self.piClassName, f'InheritKey({getCodeLine()}):', InheritKey, str(
                            self.piClassDir))), lable.ERROR)
                        printIt('Check title case for PiClass')
                        exit()
                    parameters = aPiFilePI["piBody"]["piClassGC"]["initArguments"]
                    if paramType not in self.inheritance:
                        rtnLines += f'{indent*(iniLevel)}rtnStr += \'{indent*(printIniLevel)}"{param}": ' + \
                            '{' + '\\n\'\n'
                        printIniLevel += 1
                        parmLen = len(parameters)
                        parmIndex = 0
                        for parameter in parameters:
                            # print(f'parameter: {parameter}')
                            if parameter[:2] == 'pi':
                                rtnLines += f'{indent*(iniLevel)}rtnStr += f\'{indent*(printIniLevel)}"{parameter}":' + \
                                    '"{self.' + f'{param}.{parameter}' + '}"'
                                if parmIndex == parmLen - 1:
                                    rtnLines += '\\n\'\n'
                                else:
                                    rtnLines += ',\\n\'\n'
                            parmIndex += 1
                        printIniLevel -= 1
                        rtnLines += f'{indent*(iniLevel)}rtnStr += \'{indent*(printIniLevel)}' + \
                            '},' + '\\n\'\n'
                    else:
                        for parameter in parameters:
                            rtnLines += f'{indent*iniLevel}rtnStr += f\'{indent*(printIniLevel)}"{parameter}":' + \
                                '"{self.' + f'{param}.{parameter}' + '}",\\n\'\n'
                elif paramType[:2] == "pi":
                    upperParamType = paramType[:1].upper() + paramType[1:]
                    if upperParamType not in self.inheritance:
                        rtnLines += f'{indent*iniLevel}rtnStr += f\'{indent*(printIniLevel)}"{param}":' + \
                            '"{self.' + param + '}",\\n\'\n'
                else:
                    rtnLines += f'{indent*iniLevel}rtnStr += f\'{indent*(printIniLevel)}"{param}":' + \
                        '"{self.' + param + '}",\\n\'\n'
                removeLastComma = True
            if removeLastComma:
                rtnLines = rtnLines[:-5] + '\\n\'\n'

            rtnLines += indent*iniLevel + 'rtnStr += "' + '}"\n'
            rtnLines += indent*iniLevel + 'return rtnStr\n'
        rtnLines += '\n'
        return rtnLines
    def __genJsonCodeLines(self, iniLevel=0):
        rtnLines = ""
        if len(self.jsonCode) > 0:
            rtnLines = self.__addJsonCodeLines(iniLevel)
        elif self.initArguments or self.inheritance:
            indent = self.indent
            rtnLines = indent*iniLevel + 'def json(self) -> dict:\n'
            iniLevel += 1
            rtnLines += indent*iniLevel + 'rtnDict = {\n'
            iniLevel += 1
            try:
                if self.inheritance:
                    # print('self.inheritance',self.piClassName)
                    for InheritKey in self.inheritance:
                        if InheritKey != "object" and self.uniqeParametersPiTypes:
                            if InheritKey not in self.uniqeParametersPiTypes:
                                # Get list of arguments from inherited classes
                                aPiFilePI = piLoadPiClassGCJson(InheritKey, self.piClassDir)
                                if not aPiFilePI:raise Exception
                                parameters = aPiFilePI["piBody"]["piClassGC"]["initArguments"]
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
                else:
                    # print('not self.inheritance',self.piClassName)
                    for param in self.initArguments:
                        paramType = self.initArguments[param]["type"]
                        # next add lines for paramaters. Taking account to ignore inhareted parameters
                        if paramType[:2] == "Pi":
                            aPiFilePI = piLoadPiClassGCJson(paramType, self.piClassDir)
                            if not aPiFilePI:
                                raise Exception
                            parameters = aPiFilePI["piBody"]["piClassGC"]["initArguments"]
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
    def __genFromPiClassesLines(self, iniLevel=0) -> str:
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

    def __genGlobalsLines(self, iniLevel=0) -> str:
        """Generate DEFAULT globals when none exist"""
        # Most classes don't need default globals
        return ""

    def __addGlobalsLines(self, iniLevel=0) -> str:
        """Use CUSTOM globals"""
        rtnLines = ""
        for globalLine in self.globals:
            rtnLines += globalLine + '\n'
        return rtnLines

    def __genClassCommentLines(self, iniLevel=0) -> str:
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

    def __genPreSuperInitCodeLines(self, iniLevel=0) -> str:
        """Generate DEFAULT preSuperInitCode when none exists"""
        # Most classes don't need default pre-super init code
        return ""

    def __addPreSuperInitCodeLines(self, iniLevel=0) -> str:
        """Use CUSTOM preSuperInitCode"""
        rtnLines = ""
        for preSuperInitCodeLine in self.preSuperInitCode:
            rtnLines += self.__appednCodeLine(preSuperInitCodeLine, iniLevel)
        return rtnLines

    def __genPostSuperInitCodeLines(self, iniLevel=0) -> str:
        """Generate DEFAULT postSuperInitCode when none exists"""
        # Most classes don't need default post-super init code
        return ""

    def __addPostSuperInitCodeLines(self, iniLevel=0) -> str:
        """Use CUSTOM postSuperInitCode"""
        rtnLines = ""
        for postSuperInitCodeLine in self.postSuperInitCode:
            rtnLines += self.__appednCodeLine(postSuperInitCodeLine, iniLevel)
        return rtnLines

    def __genInitAppendCodeLines(self, iniLevel=0) -> str:
        """Generate DEFAULT initAppendCode when none exists"""
        # Most classes don't need default init append code
        return ""

    def __addInitAppendCodeLines(self, iniLevel=0) -> str:
        """Use CUSTOM initAppendCode"""
        rtnLines = ""
        for initAppendCodeLine in self.initAppendCode:
            rtnLines += self.__appednCodeLine(initAppendCodeLine, iniLevel)
        return rtnLines

    def __genGenPropsLines(self, iniLevel=0) -> str:
        """Generate DEFAULT genProps when none exists"""
        # Most classes don't need default generated properties
        return ""

    def __addGenPropsLines(self, iniLevel=0) -> str:
        """Use CUSTOM genProps"""
        if self.genProps:
            return self.genProps + '\n'
        return ""

    def __genGlobalCodeLines(self, iniLevel=0) -> str:
        """Generate DEFAULT globalCode when none exists"""
        # Most classes don't need default global code
        return ""

    def __addGlobalCodeLines(self, iniLevel=0) -> str:
        """Use CUSTOM globalCode"""
        rtnLines = ""
        for globalCodeLine in self.globalCode:
            rtnLines += self.__appednCodeLine(globalCodeLine, iniLevel)
        return rtnLines

    def __addJsonCodeLines(self, iniLevel=0):
        """Use CUSTOM jsonCode"""
        indent = self.indent
        rtnLines = ""
        for JsonCodeLine in self.jsonCode:
            rtnLines += indent*iniLevel + JsonCodeLine + '\n'
        return rtnLines
    def __addStrCodeLines(self, iniLevel=0):
        rtnLines = ""
        for StrCodeLine in self.strCode:
            rtnLines += self.__appednCodeLine(StrCodeLine, iniLevel)
        return rtnLines
    def __addDefCodeLines(self, iniLevel=0):
        rtnLines = ""
        for DefCode in self.classDefCode:
            for DefCodeLine in self.classDefCode[DefCode]:
                rtnLines += self.__appednCodeLine(DefCodeLine, iniLevel)
        return rtnLines
    def __genInitLines(self, iniLevel=0):
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
                if paramType not in self.fromPiClasses: self.fromPiClasses.append(paramType)
                # Check if the value is None (either None object or string "None")
                paramValue = self.initArguments[param]["value"]
                if paramValue is None or str(paramValue).lower() == "none":
                    # Parameter value is None - use union type syntax
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
        if self.inheritance: rtnLines += self.__genInitSuperLine(iniLevel)
        if self.postSuperInitCode:
            initLines += self.__addPostSuperInitCodeLines(iniLevel)
            addAutoGenInitLines = False
        if addAutoGenInitLines: initLines += self.__genInitCodeLines(iniLevel)
        if initLines: rtnLines += initLines; initLines = ""
        if self.initAppendCode: initLines += self.__appendInitCodeLines(iniLevel)
        if initLines: rtnLines += initLines; initLines = ""
        if self.genProps: initLines += self.__genClassProperties(iniLevel)
        if initLines: rtnLines += initLines; initLines = ""
        # else: rtnLines += indent*iniLevel + "pass\n"
        return rtnLines
    def __genClassLines(self, indent=4, iniLevel=0):
        """Main class generation using unified element-based architecture"""
        rtnLines = self.__genClassLine(iniLevel)
        iniLevel += 1

        # Use unified element-based generation for all elements
        rtnLines += self.__generateElementCode('classComment', iniLevel)
        rtnLines += self.__genInitLines(iniLevel)  # Init is complex, keep existing logic for now
        rtnLines += self.__generateElementCode('strCode', iniLevel)
        rtnLines += self.__generateElementCode('jsonCode', iniLevel)

        # Handle classDefCode (custom methods) - keep existing logic for now
        if len(self.classDefCode) > 0:
            rtnLines += self.__addDefCodeLines(iniLevel)

        return rtnLines
    def __genAboveClassLines(self) -> str:
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
                    rtnLines += f'{aGlobal} = {self.globals[aGlobal]}\n'
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
    def __genBellowClassLines(self) -> str:
        indent = self.indent
        rtnLines = ''
        if len(self.globalCode) > 0:
            for globalCode in self.globalCode:
                rtnLines += f'{globalCode}\n'
        return rtnLines

    def __setPiClassDir(self):
        """Set up the piClasses directory for output files"""
        # Check if fileDirectory is specified in the piClassGC configuration
        if self.fileDirectory:
            # Use the specified fileDirectory (can be relative or absolute)
            piClassDir = Path(self.fileDirectory)
            if not piClassDir.is_absolute():
                # If relative, make it relative to current working directory
                piClassDir = Path.cwd().joinpath(piClassDir)
        else:
            # Fall back to configured piClassGCDir from .pigencoderc
            piClassGCDir = readRC("piClassGCDir")
            if piClassGCDir:
                # Use the RC configured directory
                piClassDir = Path(piClassGCDir)
                if not piClassDir.is_absolute():
                    piClassDir = Path.cwd().joinpath(piClassDir)
            else:
                # Ultimate fallback to old behavior for backward compatibility
                piClassDir = readRC(PiSeedTypes[0])
                if piClassDir:
                    piClassDir = Path(piClassDir).parent.joinpath("piClasses")
                else:
                    piClassDir = Path.cwd().joinpath("piClasses")

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
        self.savedCodeFiles[baseFileName] = fileName
    def __genPiClass(self, piJsonFileName, verbose = False) -> None:
        self.pi_piClassGC = readJson(piJsonFileName)
        self.PiFileName = piJsonFileName
        # printIt(f'piJsonFileName: {piJsonFileName}',lable.WARN)
        self.__setPiPiGCAtters()
        self.__setPiClassDir()
        piClassLines = self.__genClassLines()
        piClassLines = self.__genAboveClassLines() + piClassLines + self.__genBellowClassLines()
        piClassLines += f'\n{self.piClassName}_PI = ' + json.dumps(self.pi_piClassGC,indent=4)
        self.__savePiClass(piClassLines, verbose)
        logIt("GenPiClass: " + piJsonFileName)
    def genPiClasses(self, genFileName='', verbose = False):
        if genFileName:
            self.__genPiClass(genFileName, verbose)
        else:
            piJsonGCDir = readRC(PiSeedTypes[0])
            if not piJsonGCDir:
                piJsonGCDir = piDirs[PiSeedTypes[0]]
                writeRC(PiSeedTypes[0], piJsonGCDir)
            piJsonGCDir = Path(piJsonGCDir).joinpath(PiSeedTypes[4])
            piJsonGCFilenames = os.listdir(piJsonGCDir)
            piJsonGCFilenames.sort()
            #loop though json files in correct order
            for piJsonGCFilename in piJsonGCFilenames:
                piJsonFileName = os.path.join(piJsonGCDir, piJsonGCFilename)
                self.__genPiClass(piJsonFileName)
##### Public Functions
    def __generateElementCode(self, elementName: str, iniLevel: int = 0) -> str:
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
            methodName = f'__add{elementName.capitalize()}Lines'
            if hasattr(self, methodName):
                return getattr(self, methodName)(iniLevel)

        # No custom code - generate default
        methodName = f'__gen{elementName.capitalize()}Lines'
        if hasattr(self, methodName):
            return getattr(self, methodName)(iniLevel)

        return ""

    def getDefaultElementCode(self, elementName: str, iniLevel: int = 0) -> str:
        """Get what the default code should be for a given element - used by syncCode for comparison"""
        methodName = f'__gen{elementName.capitalize()}Lines'
        if hasattr(self, methodName):
            return getattr(self, methodName)(iniLevel)
        return ""

#[ genPiPiClass, genPiPisFromSeedPiPiGCFile ]
def genPiPiClass(genFileName='', verbose = False) -> dict:
    '''Generate python file with genFileName piClassGC file.
       If genFileName is not specified, all piClassGC files in
       scratchPis/piClassGC direcory will be proccessed.
       Returns dirctory of ClassName keyed filename values.'''
    piClassGC = PiGenCode()
    piClassGC.genPiClasses(genFileName, verbose)
    return piClassGC.savedCodeFiles

