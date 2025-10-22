from json import load, loads, dump, JSONDecodeError
from traceback import format_exception
from pathlib import Path
import difflib
from ..defs.logIt import printIt, lable, logIt, cStr, color

cswPath = Path.cwd()
rcFileName = Path.cwd()
rcFileName = cswPath.joinpath(f'.{cswPath.name.lower()}rc')

piGenCodeDirs = {
    "piSeedsDir": "piSeeds",
    "piGermDir": "piGerms",
    "piClassGCDir": "piClassGC",
    "piDefGCDir": "piDefsGC",
    "piGenClassDir": "piGenClasses",
    "piScratchDir": "piGerms"
}
piGCDirs = list(piGenCodeDirs.keys())

piIndexerTypes_S = ["users", "realms", "domains", "subjects"]
piIndexerTypes = ["user", "realm", "domain", "subject"]

def resetPiRC():
    if rcFileName.is_file():
        rcFileName.unlink()
    for piDir, piDirPathStr in piGenCodeDirs.items():
        writeRC(piDir, piDirPathStr)

def getKeyItem(key) -> str:
    rtnValue = readRC(key)
    if not rtnValue:
        if key in piGCDirs:
            rtnValue = piGenCodeDirs[key]
            writeRC(key, rtnValue)
            return rtnValue
    return str(rtnValue)

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

def readRC(rcName: str) -> (int | float | str | list | dict):
    global rcFileName
    if rcFileName.is_file():
        # print(rcFileName)
        try:
            with open(rcFileName, 'r') as rf:
                rawRcJson = load(rf)
                rcValue = rawRcJson[rcName]
        except:
            resetPiRC()
            rcValue = piGenCodeDirs[rcName]
    else:
        resetPiRC()
        rcValue = piGenCodeDirs[rcName]
    return rcValue

def writeRC(rcName: str, rcValue: (int | float | str | list | dict)):
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
# def getPisPath() -> Path:
#     pisPath = None
#     pisPathStr = getKeyItem('pisDir')
#     if not pisPathStr:
#         pisPath = Path.home().joinpath('pis')
#         pisPathStr = getKeyItem('pisDir')
#     else:
#         pisPath = Path(pisPathStr)
#     return pisPath


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