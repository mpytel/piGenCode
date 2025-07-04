from os import makedirs
import datetime
from traceback import format_exception
from pathlib import Path
from json import load, loads, dump, dumps, JSONDecodeError
from .logIt import logIt, printIt, lable
from ..classes.piSeeds import PiSeedTypes, PiSeed, PiSeedTypeREs
from ..defs.piRCFile import readRC, getKeyItem
from ..defs.piID import getPiIDs

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
    piStrucFileName = readRC(PiSeedTypes[0])
    piStrucFileName = Path(piStrucFileName).joinpath(PiSeedTypes[1])
    makedirs(piStrucFileName, exist_ok=True)
    piStrucFileName = Path(piStrucFileName).joinpath(f'{PiSeedTypes[1]}_{baseTitle}.json')
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
    piStrucFileName = readRC(PiSeedTypes[0])
    piStrucFileName = Path(piStrucFileName).joinpath(PiSeedTypes[2])
    makedirs(piStrucFileName, exist_ok=True)
    piStrucFileName = Path(piStrucFileName).joinpath(f'{PiSeedTypes[2]}_{baseTitle}.json')
    return str(piStrucFileName)

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
    piFilePath = Path(readRC('piScratchDir'))
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

def writePi(aDict: dict, verbose=True) -> bool:
    piStrucFileName = getPiFileName(aDict)
    rtnBool = writeJson(piStrucFileName, aDict, verbose)
    if rtnBool and verbose: printIt(piStrucFileName,lable.SAVED)
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

class PiClassGCFiles():
    def __init__(self) -> None:
        piScratchPath = Path(getKeyItem("piScratchDir"))
        self.fileDirName = piScratchPath.joinpath("piClassGC")
        self.fileDirName.mkdir(mode=511, parents=True, exist_ok=True)
        self.baseMaxFileInt = self._getBaseMaxFileInt()
        self.maxFileInt = self.baseMaxFileInt
        self.lastLineNumber = 0
        self.classGCFilePaths = []
    def _getPiClassGCFiles(self):
        return [p.name for p in self.fileDirName.iterdir() if p.is_file() and PiSeedTypeREs[PiSeedTypes[3]].match(p.name)]
    def _getBaseMaxFileInt(self):
        rtnInt = 1
        PiClassGCFiles = self._getPiClassGCFiles()
        if PiClassGCFiles:
            PiClassGCFiles.sort()
            fileMatch = PiSeedTypeREs[PiSeedTypes[3]].match(str(PiClassGCFiles[-1]))
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
                fileMatch = PiSeedTypeREs[PiSeedTypes[3]].match(PiClassGCFile)
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
                fileMatch = PiSeedTypeREs[PiSeedTypes[3]].match(PiClassGCFile)
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
            print(">>>",piTitle, self.lastLineNumber, self.baseMaxFileInt, self.maxFileInt, f'{piTitle} file exits')
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