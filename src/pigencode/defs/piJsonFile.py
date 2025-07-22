from os import makedirs
import datetime
from traceback import format_exception
from pathlib import Path
from json import load, loads, dump, dumps, JSONDecodeError
from re import compile as reCompile
from .logIt import logIt, printIt, lable
from pigencode.classes.piSeeds import PiSeedTypes, PiSeed, PiSeedTypeREs
from pigencode.defs.fileIO import readRC, writeRC, getKeyItem, setKeyItem, piGenCodeDirs, piGCDirs
from pigencode.defs.piID import getPiIDs

def readJson(fileName: str, verbose=True) -> dict:
    rtnDict = {}
    try:
        with open(fileName, 'r') as rf:
            rtnDict = load(rf)
    except FileNotFoundError:
        if verbose: printIt("piGen|readJson -", fileName,lable.FileNotFound)
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
        if verbose: printIt("piGen|writeJson -", fileName,lable.FileNotFound)
    except JSONDecodeError as e:
        tb_str = ''.join(format_exception(None, e, e.__traceback__))
        printIt(tb_str,lable.ERROR)
    return rtnBool

def getPiStrucFileName(baseTitle) -> str:
    piGermDir = getKeyItem(piGCDirs[1])
    if not piGermDir:
        piGermDir = piGenCodeDirs[piGCDirs[1]]
        setKeyItem(piGCDirs[1], piGermDir)
    piStrucFileName = Path(piGermDir).joinpath(PiSeedTypes[0])
    makedirs(piStrucFileName, exist_ok=True)
    piStrucFileName = Path(piStrucFileName).joinpath(f'{PiSeedTypes[0]}_{baseTitle}.json')
    return str(piStrucFileName)

def writePiStruc(baseTitle: str, aDict: dict, verbose=True) -> bool:
    piStrucFileName = getPiStrucFileName(baseTitle)
    rtnBool = writeJson(piStrucFileName, aDict, verbose)
    if rtnBool and verbose: printIt(piStrucFileName,lable.SAVED)
    return rtnBool

def readPiStruc(baseTitle: str, verbose=True) -> dict:
    piStrucFileName = getPiStrucFileName(baseTitle)
    rtnDict = readJson(piStrucFileName, verbose)
    return rtnDict

def getPiDefaultFileName(baseTitle) -> str:
    piGermDir = getKeyItem(piGCDirs[1])
    if not piGermDir:
        piGermDir = piGenCodeDirs[piGCDirs[1]]
        setKeyItem(piGCDirs[1], piGermDir)
    piDefaultFileName = Path(piGermDir).joinpath(PiSeedTypes[1])
    makedirs(piDefaultFileName, exist_ok=True)
    piDefaultFileName = Path(piDefaultFileName).joinpath(f'{PiSeedTypes[1]}_{baseTitle}.json')
    return str(piDefaultFileName)

def writePiDefault(baseTitle: str, aDict: dict, verbose=True) -> bool:
    piStrucFileName = getPiDefaultFileName(baseTitle)
    # populate piID and piMD5
    if type(aDict.get("piID")) == str:
        piID, piMD5 = getPiIDs(aDict)
        aDict["piID"] = piID
        aDict["piIndexer"]["piMD5"] = piMD5
    rtnBool = writeJson(piStrucFileName, aDict, verbose)
    if type(aDict.get("piTouch")) == dict:
        now = str(datetime.datetime.now())
        aDict["piTouch"]["piCreationDate"] = now
        aDict["piTouch"]["piModificationDate"] = now
        aDict["piTouch"]["piTouchDate"] = now
    rtnBool = writeJson(piStrucFileName, aDict, verbose)
    if rtnBool and verbose: printIt(piStrucFileName,lable.SAVED)
    return rtnBool

def readPiDefault(baseTitle: str, verbose=True) -> dict:
    piStrucFileName = getPiDefaultFileName(baseTitle)
    rtnDict = readJson(piStrucFileName, verbose)
    return rtnDict


def getPiFilePath(aDict: dict) -> Path:
    piGermDir = getKeyItem(piGCDirs[1])
    if not piGermDir:
        piGermDir = piGenCodeDirs[piGCDirs[1]]
        setKeyItem(piGCDirs[1], piGermDir)
    piFilePath = Path(piGermDir)
    piFilePath = piFilePath.joinpath("pis")
    piFilePath = piFilePath.joinpath(aDict["piIndexer"]["piUser"])
    piFilePath = piFilePath.joinpath(aDict["piIndexer"]["piRealm"])
    piFilePath = piFilePath.joinpath(aDict["piIndexer"]["piDomain"])
    piFilePath = piFilePath.joinpath(aDict["piIndexer"]["piSubject"])
    piFilePath = piFilePath.joinpath(aDict["piBase"]["piType"])
    piFilePath.mkdir(mode=511,parents=True,exist_ok=True)
    return piFilePath

def getPiFileName(aDict: dict) -> str:
    baseType = aDict["piBase"]["piType"]
    baseTitle = aDict["piBase"]["piTitle"]
    piTypeDir = getPiFilePath(aDict)
    piStrucFileName = piTypeDir.joinpath(f'{baseTitle}.json')
    return str(piStrucFileName)

def writePi(aDict: dict, fileName = '', verbose=True) -> bool:
    if fileName:
        piFileName = fileName
    else:
       piFileName = getPiFileName(aDict)
    rtnBool = writeJson(piFileName, aDict, verbose)
    if rtnBool and verbose:
        printIt(piFileName, lable.SAVED)
    return rtnBool

def readPi(thePi: PiSeed, verbose=True) -> dict:
    piStrucFileName = getPiFileName(thePi.json())
    rtnDict = readJson(piStrucFileName, verbose)
    return rtnDict

def printDict(theDict, piDictTitle="no title"):
    ps = dumps(theDict, indent=2)
    printIt(f'{piDictTitle}:\n{ps}', lable.INFO)


def piLoadPiClassGCJson(PiClassName, piClassGCDir) -> dict:
    rtnJson: dict
    lowerPiClassName = PiClassName[:2].lower() + PiClassName[2:]
    # look in class file for listm of parametersm being inharited as children of paramType
    fileName = Path(piClassGCDir).joinpath(lowerPiClassName + '.py')
    # printIt(f'piLoadPiClassGCJson fileName: {fileName}', lable.DEBUG)
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
        printIt(f'piJsonStr: {piJsonStr}', lable.ABORTPRT)
        rtnJson = loads(piJsonStr)
    else:
        printIt('piLoadPiClassGCJson', fileName, lable.FileNotFound)
    return rtnJson

class PiDefGCFiles():
    def __init__(self) -> None:
        piScratchPath = Path(getKeyItem("piGermDir"))
        self.fileDirName = piScratchPath.joinpath(getKeyItem("piDefGCDir"))
        self.fileDirName.mkdir(mode=511, parents=True, exist_ok=True)
        self.baseMaxFileInt = self._getBaseMaxFileInt()
        self.maxFileInt = self.baseMaxFileInt
        self.lastLineNumber = 0
        self.defGCFilePaths = []

    def _getPiDefGCFiles(self):
        # Pattern for piDefGC files: piDefGC001_filename.json
        defgc_pattern = reCompile(r'piDefGC(\d{3})_(.+)\.json')
        return [p.name for p in self.fileDirName.iterdir() if p.is_file() and defgc_pattern.match(p.name)]

    def _getBaseMaxFileInt(self):
        rtnInt = 1
        PiDefGCFiles = self._getPiDefGCFiles()
        if PiDefGCFiles:
            PiDefGCFiles.sort()
            defgc_pattern = reCompile(r'piDefGC(\d{3})_(.+)\.json')
            fileMatch = defgc_pattern.match(str(PiDefGCFiles[-1]))
            if fileMatch:
                fileParts = fileMatch.groups()
                rtnInt = int(fileParts[0]) + 1
        return rtnInt

    def _shiftFilesUpOneFromBaseMaxFileInt(self, pad=3):
        PiDefGCFiles = self._getPiDefGCFiles()
        if PiDefGCFiles:
            PiDefGCFiles.sort(reverse=True)
            defgc_pattern = reCompile(r'piDefGC(\d{3})_(.+)\.json')
            for PiDefGCFile in PiDefGCFiles:
                fileMatch = defgc_pattern.match(PiDefGCFile)
                if fileMatch:
                    fileParts = fileMatch.groups()
                    fileInt = int(fileParts[0])
                    if fileInt >= self.baseMaxFileInt:
                        newName = self.fileDirName.joinpath(f'piDefGC{str(int(fileParts[0])+1).zfill(pad)}_{fileParts[1]}.json')
                        oldName = self.fileDirName.joinpath(PiDefGCFile)
                        self.fileDirName.joinpath(PiDefGCFile).rename(newName)

    def _chkForExistingFile(self, piTitle, fileDirectory=None):
        fileInt = 0
        PiDefGCFiles = self._getPiDefGCFiles()
        if PiDefGCFiles:
            PiDefGCFiles.sort()
            defgc_pattern = reCompile(r'piDefGC(\d{3})_(.+)\.json')
            for PiDefGCFile in PiDefGCFiles:
                fileMatch = defgc_pattern.match(PiDefGCFile)
                if fileMatch:
                    fileParts = fileMatch.groups()
                    if fileParts[0].isnumeric():
                        chkFileName = fileParts[1]
                        # Only consider it a match if both title and file path match
                        # If fileDirectory is None, fall back to just checking the title
                        if chkFileName == piTitle:
                            # If we have a file directory, we need to check if it matches
                            # by reading the JSON file and checking the fileDirectory field
                            if fileDirectory:
                                jsonFile = self.fileDirName.joinpath(PiDefGCFile)
                                if jsonFile.exists():
                                    try:
                                        with open(jsonFile, 'r') as f:
                                            data = load(f)
                                            if data.get("piBody", {}).get("piDefGC", {}).get("fileDirectory") == fileDirectory:
                                                fileInt = int(fileParts[0])
                                                break
                                    except Exception:
                                        # If we can't read the file, just continue
                                        pass
                            else:
                                # If no fileDirectory specified, just match on title
                                fileInt = int(fileParts[0])
                                break
        return fileInt

    def _getFileIntZFill(self, piTitle: str, lineNumber, fileDirectory=None, pad=3) -> str:
        fileInt = self._chkForExistingFile(piTitle, fileDirectory)
        if not fileInt:
            if not self.lastLineNumber:
                self.lastLineNumber = lineNumber
            if lineNumber < self.lastLineNumber:
                self._shiftFilesUpOneFromBaseMaxFileInt(pad)
                fileInt = self.baseMaxFileInt
            else:
                self.lastLineNumber = lineNumber
                fileInt = self.maxFileInt
            self.maxFileInt += 1
        else:
            pass
            #print(">>>", piTitle, self.lastLineNumber, self.baseMaxFileInt, self.maxFileInt, f'{piTitle} file exists')
        return str(fileInt).zfill(3)

    def _getPiDefGCFileName(self, piType, piTitle, lineNumber=0, aDict=None) -> str:
        makedirs(self.fileDirName, exist_ok=True)
        fileDirectory = None
        if aDict and "piBody" in aDict and "piDefGC" in aDict["piBody"] and "fileDirectory" in aDict["piBody"]["piDefGC"]:
            fileDirectory = aDict["piBody"]["piDefGC"]["fileDirectory"]
        fileIntStr = self._getFileIntZFill(piTitle, lineNumber, fileDirectory)
        fileName = self.fileDirName.joinpath(f'{piType}{fileIntStr}_{piTitle}.json')
        return str(fileName)

    def writePiDefGC(self, piType, piTitle, lineNumber, aDict: dict, verbose=True) -> bool:
        piStrucFileName = self._getPiDefGCFileName(piType, piTitle, lineNumber, aDict)
        rtnBool = writeJson(piStrucFileName, aDict, verbose)
        if rtnBool:
            self.defGCFilePaths.append(piStrucFileName)
        if rtnBool and verbose:
            printIt(piStrucFileName, lable.SAVED)
        return rtnBool

    def readPiDefGC(self, piType, piTitle, verbose=True) -> dict:
        piStrucFileName = self._getPiDefGCFileName(piType, piTitle, 0, None)
        rtnDict = readJson(piStrucFileName, verbose)
        return rtnDict


class PiGenClassFiles():
    def __init__(self) -> None:
        piScratchPath = Path(getKeyItem("piGermDir"))
        self.fileDirName = piScratchPath.joinpath("piGenClass")
        self.fileDirName.mkdir(mode=0o755, parents=True, exist_ok=True)
        self.baseMaxFileInt = self._getBaseMaxFileInt()
        self.maxFileInt = self.baseMaxFileInt
        self.lastLineNumber = 0
        self.genClassFilePaths = []

    def _getPiGenClassFiles(self):
        # Pattern for piGenClass files: piGenClass001_filename.json
        genclass_pattern = reCompile(r'piGenClass(\d{3})_(.+)\.json')
        return [p.name for p in self.fileDirName.iterdir() if p.is_file() and genclass_pattern.match(p.name)]

    def _getBaseMaxFileInt(self):
        rtnInt = 1
        PiGenClassFiles = self._getPiGenClassFiles()
        if PiGenClassFiles:
            PiGenClassFiles.sort()
            genclass_pattern = reCompile(r'piGenClass(\d{3})_(.+)\.json')
            fileMatch = genclass_pattern.match(str(PiGenClassFiles[-1]))
            if fileMatch:
                fileParts = fileMatch.groups()
                rtnInt = int(fileParts[0]) + 1
        return rtnInt

    def _shiftFilesUpOneFromBaseMaxFileInt(self, pad=3):
        PiGenClassFiles = self._getPiGenClassFiles()
        if PiGenClassFiles:
            PiGenClassFiles.sort(reverse=True)
            genclass_pattern = reCompile(r'piGenClass(\d{3})_(.+)\.json')
            for PiGenClassFile in PiGenClassFiles:
                fileMatch = genclass_pattern.match(PiGenClassFile)
                if fileMatch:
                    fileParts = fileMatch.groups()
                    fileInt = int(fileParts[0])
                    if fileInt >= self.baseMaxFileInt:
                        newName = self.fileDirName.joinpath(f'piGenClass{str(int(fileParts[0])+1).zfill(pad)}_{fileParts[1]}.json')
                        oldName = self.fileDirName.joinpath(PiGenClassFile)
                        self.fileDirName.joinpath(PiGenClassFile).rename(newName)

    def _chkForExistingFile(self, piTitle):
        fileInt = 0
        PiGenClassFiles = self._getPiGenClassFiles()
        if PiGenClassFiles:
            PiGenClassFiles.sort()
            genclass_pattern = reCompile(r'piGenClass(\d{3})_(.+)\.json')
            for PiGenClassFile in PiGenClassFiles:
                fileMatch = genclass_pattern.match(PiGenClassFile)
                if fileMatch:
                    fileParts = fileMatch.groups()
                    if fileParts[0].isnumeric():
                        chkFileName = fileParts[1]
                        if chkFileName == piTitle:
                            fileInt = int(fileParts[0])
                            break
        return fileInt

    def _getFileIntZFill(self, piTitle: str, lineNumber, pad=3) -> str:
        fileInt = self._chkForExistingFile(piTitle)
        if not fileInt:
            if not self.lastLineNumber:
                self.lastLineNumber = lineNumber
            if lineNumber < self.lastLineNumber:
                self._shiftFilesUpOneFromBaseMaxFileInt(pad)
                fileInt = self.baseMaxFileInt
            else:
                self.lastLineNumber = lineNumber
                fileInt = self.maxFileInt
            self.maxFileInt += 1
        else:
            pass
            # print(">>>", piTitle, self.lastLineNumber, self.baseMaxFileInt, self.maxFileInt, f'{piTitle} file exists')
        return str(fileInt).zfill(3)

    def _getPiGenClassFileName(self, piType, piTitle, lineNumber=0) -> str:
        makedirs(self.fileDirName, exist_ok=True)
        fileIntStr = self._getFileIntZFill(piTitle, lineNumber)
        fileName = self.fileDirName.joinpath(f'{piType}{fileIntStr}_{piTitle}.json')
        return str(fileName)

    def writePiGenClass(self, piType, piTitle, lineNumber, aDict: dict, verbose=True) -> bool:
        piStrucFileName = self._getPiGenClassFileName(piType, piTitle, lineNumber)
        rtnBool = writeJson(piStrucFileName, aDict, verbose)
        if rtnBool:
            self.genClassFilePaths.append(piStrucFileName)
        if rtnBool and verbose:
            printIt(piStrucFileName, lable.SAVED)
        return rtnBool

    def readPiGenClass(self, piType, piTitle, verbose=True) -> dict:
        piStrucFileName = self._getPiGenClassFileName(piType, piTitle)
        rtnDict = readJson(piStrucFileName, verbose)
        return rtnDict


class PiClassGCFiles():
    def __init__(self) -> None:
        piScratchPath = Path(getKeyItem("piGermDir"))
        self.fileDirName = piScratchPath.joinpath("piClassGC")
        self.fileDirName.mkdir(mode=511, parents=True, exist_ok=True)
        self.baseMaxFileInt = self._getBaseMaxFileInt()
        self.maxFileInt = self.baseMaxFileInt
        self.lastLineNumber = 0
        self.classGCFilePaths = []
    def _getPiClassGCFiles(self):
        return [p.name for p in self.fileDirName.iterdir() if p.is_file() and PiSeedTypeREs[PiSeedTypes[2]].match(p.name)]
    def _getBaseMaxFileInt(self):
        rtnInt = 1
        PiClassGCFiles = self._getPiClassGCFiles()
        if PiClassGCFiles:
            PiClassGCFiles.sort()
            fileMatch = PiSeedTypeREs[PiSeedTypes[2]].match(str(PiClassGCFiles[-1]))
            if fileMatch:
                fileParts = fileMatch.groups()
                rtnInt = int(fileParts[0]) + 1
        return rtnInt

    def _shiftFilesUpOneFromBaseMaxFileInt(self, pad = 3):
        PiClassGCFiles = self._getPiClassGCFiles()
        if PiClassGCFiles:
            PiClassGCFiles.sort(reverse=True)
            for PiClassGCFile in PiClassGCFiles:
                # PiSeedTypes[3]: reCompile('piClassGC(\d{3})_(.+).json'),
                fileMatch = PiSeedTypeREs[PiSeedTypes[2]].match(PiClassGCFile)
                if fileMatch:
                    fileParts = fileMatch.groups()
                    fileInt = int(fileParts[0])
                    if fileInt >= self.baseMaxFileInt:
                        # print(f'self.baseMaxFileInt >= fileInt: {self.baseMaxFileInt} >= {fileInt}')
                        newName = self.fileDirName.joinpath(f'piClassGC{str(int(fileParts[0])+1).zfill(pad)}_{fileParts[1]}.json')
                        oldName = self.fileDirName.joinpath(PiClassGCFile)
                        # print("oldName",oldName.stem)
                        self.fileDirName.joinpath(PiClassGCFile).rename(newName)
                        # print("newName",newName.stem)

    def _chkForExistingFile(self, piTitle):
        fileInt = 0
        PiClassGCFiles = self._getPiClassGCFiles()
        if PiClassGCFiles:
            PiClassGCFiles.sort()
            for PiClassGCFile in PiClassGCFiles:
                # print('PiClassGCFile',PiClassGCFile)
                # PiSeedTypes[3]: reCompile('piClassGC(\d{3})_(.+).json'),
                fileMatch = PiSeedTypeREs[PiSeedTypes[2]].match(PiClassGCFile)
                if fileMatch:
                    fileParts = fileMatch.groups()
                    # print(fileParts)
                    if fileParts[0].isnumeric():
                        chkFileName = fileParts[1]
                        if chkFileName == piTitle:
                            fileInt = int(fileParts[0])
                            break
        return fileInt

    def _getFileIntZFill(self, piTitle: str, lineNumber, pad = 3) -> str:
        fileInt = self._chkForExistingFile(piTitle)
        # print("piTitle", "self.lastLineNumber", "self.baseMaxFileInt", "self.maxFileInt", fileInt)
        # print(f'piTitle: {piTitle} {"-"*8}')
        if not fileInt:
            if not self.lastLineNumber:
                self.lastLineNumber = lineNumber
            if lineNumber < self.lastLineNumber:
                # print(">",piTitle, self.lastLineNumber, self.baseMaxFileInt, self.maxFileInt, fileInt)
                #  piWordsBody 29 18 19 0
                self._shiftFilesUpOneFromBaseMaxFileInt(pad)
                fileInt = self.baseMaxFileInt
            else:
                # print(">>",piTitle, self.lastLineNumber, self.baseMaxFileInt, self.maxFileInt, fileInt)
                self.lastLineNumber = lineNumber
                fileInt = self.maxFileInt
            self.maxFileInt += 1
        else:
            pass
            # print(">>>",piTitle, self.lastLineNumber, self.baseMaxFileInt, self.maxFileInt, f'{piTitle} file exits')
        return str(fileInt).zfill(3)

    def _getPiClassGCFileName(self, piType, piTitle, lineNumber = 0) -> str:

        makedirs(self.fileDirName, exist_ok=True)
        fileIntStr = self._getFileIntZFill(piTitle, lineNumber)
        fileName = self.fileDirName.joinpath(f'{piType}{fileIntStr}_{piTitle}.json')
        return str(fileName)

    def writePiClassGC(self, piType, piTitle, lineNumber, aDict: dict, verbose=True) -> bool:
        piStrucFileName = self._getPiClassGCFileName(piType, piTitle, lineNumber)
        #print('piStrucFileName:', piStrucFileName)
        rtnBool = writeJson(piStrucFileName, aDict, verbose)
        if rtnBool: self.classGCFilePaths.append(piStrucFileName)
        if rtnBool and verbose: printIt(piStrucFileName,lable.SAVED)
        return rtnBool

    def readPiClassGC(self, piType, piTitle, verbose=True) -> dict:
        piStrucFileName = self._getPiClassGCFileName(piType, piTitle)
        rtnDict = readJson(piStrucFileName, verbose)
        return rtnDict