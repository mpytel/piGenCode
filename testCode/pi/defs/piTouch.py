import json, traceback
from datetime import datetime
from pathlib import Path
from .logIt import printIt, logIt, lable
from .piFileIO import getKeyItem
from re import compile as reCompile

def isPiID(chkStr:str) -> bool:
    reUUID4 = reCompile(r"([0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[0-9a-f]{4}-[0-9a-f]{12})\Z")
    if reUUID4.match(chkStr): return True
    else: return False

def touchPiDir(dirName):
    dirPath = Path(dirName)
    if not dirPath.is_dir():
        logIt(f'{dirName}',lable.MKDIR)
        dirPath.mkdir(mode=511, parents=True, exist_ok=True)

def touchPiFile(fileName)-> dict:
    try:
        with open(fileName, "r") as fr:
            rtnJson: dict = json.load(fr)
        rtnJson["piTouch"]["piTouchDate"] = str(datetime.now())
        rtnJson["piTouch"]["piTouches"] += 1
        with open(fileName, "w") as fw:
            json.dump(rtnJson, fw, indent=2)
        return rtnJson
    except Exception as e:
        tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
        printIt(f'touchPiFile\n{tb_str}',lable.ERROR)
        exit()

def piPathLn(theLink:str, PiPiLnDir: str|Path) -> Path | None:
    try:
        if type(PiPiLnDir) == Path:
            linkName = PiPiLnDir.joinpath(theLink)
        else:
            linkName = Path(PiPiLnDir).joinpath(theLink)
        #print (linkName)
        fileName = linkName.readlink()
    except:
        fileName = None
    return fileName


def piFromLn(theLink: str, PiPiLnDir: str | Path) -> tuple[dict | None, Path | None]:
    fileName = piPathLn(theLink, PiPiLnDir)
    if fileName:
        theJsonDict = touchPiFile(fileName)
    else:
        theJsonDict = None
    return theJsonDict, fileName

def getNewestPiLink(PiPiLnDir) -> tuple:
    latestPiLinkTime = 0.0
    latestPiLinkName = ''
    baseDir = Path(PiPiLnDir)
    for item in baseDir.iterdir():
        if item.is_symlink():
            if item.stat(follow_symlinks=False).st_ctime > latestPiLinkTime:
                latestPiLinkTime = item.stat(follow_symlinks=False).st_ctime
                latestPiLinkName = item.name
    return latestPiLinkName, latestPiLinkTime

def getNewestPiTypePiLink(PiPiLnDir, piTypeFiles: dict) -> tuple[str, Path | None, float]:
    latestPiLinkTime = 0.0
    latestPiLinkPath: Path | None = None
    latestPiLinkTitle = ''
    baseDir = Path(PiPiLnDir)
    print('z0', list(piTypeFiles.keys()))
    for piTitle, piPath in piTypeFiles.items():
        aPi = touchPiFile(fileName=piPath)
        symLink = baseDir.joinpath(aPi['piID'])
        if symLink.is_symlink():
            if symLink.stat(follow_symlinks=False).st_ctime > latestPiLinkTime:
                latestPiLinkTitle = piTitle
                latestPiLinkPath = symLink.readlink()
                latestPiLinkTime = symLink.stat(follow_symlinks=False).st_ctime
    return latestPiLinkTitle, latestPiLinkPath, latestPiLinkTime

def getPiLinkPaths(PiPiLnDir) -> tuple:
    piLinkPaths = []
    latestPiLinkTime = 0.0
    baseDir = Path(PiPiLnDir)
    for item in baseDir.iterdir():
        if item.is_symlink():
            piLinkPaths.append(item)
            if item.stat(follow_symlinks=False).st_ctime > latestPiLinkTime:
                latestPiLinkTime = item.stat(follow_symlinks=False).st_ctime
    latestPiLinkTime = datetime.fromtimestamp(latestPiLinkTime)
    return piLinkPaths, latestPiLinkTime