# don\'t import PiContoller or PiClasses because PiClasses my not be present

from re import compile as reCompile
from os import makedirs
from traceback import format_exception
from pathlib import Path
from pi.defs.logIt import printIt, label
from pi.defs.piFileIO import getKeyItem, baseDir, piDirs
from pi.commands.germSeed import germAllSeedFiles
from pi.commands.genCode import genCodeFile

class PiPiPackage():
    def __init__(self, packageName):
        self.packageName = packageName
        self.piSeedsDir: Path
        self.piScratchDir: Path
        self.piClassDir: Path
        self.pisDir: Path
        self.packageOK = True
        self.germAndGen = False
        self.piPackageSys: object
        self.piCurrentIndexer: object
        if self.packageOK: self.packageOK = self._chkBaseDirs()
        if self.packageOK: self.packageOK = self._chkPiClassFiles()
        if self.packageOK:
            if self.germAndGen:
                printIt(f'{packageName} initalized.',label.INFO)
            self.piPackageSys = PiPackageSys()
            self.piCurrentIndexer = self.piPackageSys.piCurrentIndexer
        else:
            printIt(f'{self.packageName} did not germinate correctly.', label.ERROR)
            exit(0)
    def _chkBaseDirs(self) -> bool:
        rtnBool = False
        for piDir in piDirs:
            checkDir = getKeyItem(piDir, str(baseDir.joinpath(piDirs[piDir])))
            self.__setattr__(piDir, baseDir.joinpath(checkDir))
        if self.piSeedsDir.is_dir():
            rtnBool = True
        else:
            printIt(self.piSeedsDir, label.DirNotFound)
        return rtnBool
    def _chkPiClassFiles(self) -> bool:
        rtnBool = False
        if not self.piClassDir.is_dir():
            germAllSeedFiles(False)
            genCodeFile()
            self.germAndGen = True
            rtnBool = havePiClasses()
        else:
            # look to see all classes are present
            rtnBool = havePiClasses()
        return rtnBool

def havePiClasses() -> bool:
    rtnBool = False
    piClassDir = getKeyItem("piClassDir")
    if piClassDir:
        piClassDirPath = Path(piClassDir)
        if piClassDirPath.is_dir():
            piClasses = ['piBase', 'piDomain', 'piDomainBody', 'piIDBody', 'piIDIndex', 'piIDIndexUpdates', 'piIDNode', 'piIndexer', 'piInfluence', 'piLoadPiType', 'piPi', 'piPiClasses', 'piProlog', 'piRealm', 'piRealmBody', 'piSubject', 'piSubjectBody', 'piToken', 'piTokenBody', 'piTopic', 'piTopicBody', 'piTouch', 'piTrie', 'piTrieBody', 'piTrieNode', 'piUser', 'piUserBody', 'piUserProfile', 'piWord', 'piWordBody', 'piWordSeek']
            piClassFiles = [p.name.split(".")[0] for p in piClassDirPath.iterdir() if p.is_file()]
            piClasses.sort()
            piClassFiles.sort()
            rtnBool = piClasses == piClassFiles
            if not rtnBool:
                printIt(f'check {piClasses}',label.FAIL)
                printIt(f'files {piClassFiles}',label.FAIL)
                printIt(f'**** Fix in piPackage.havePiClasses ****',label.ERROR)
    return rtnBool

def PiPackageSys() -> object:
    exec("from .piPiPackageSystem import PiPiPackageSystem")
    return eval("PiPiPackageSystem()")

def PiCurrentIndexer() -> object:
    exec("from .piCurrentIndexer import PiCurrentIndexer")
    return eval("PiCurrentIndexer()")