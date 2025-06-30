import shlex
from traceback import format_exception
from ..defs.logIt import logIt, printIt, lable
from re import Pattern, compile as reCompile
from typing import Any

class PiSeed():
    def __init__(self, aPi: tuple | None, lineNumber):
        self.lineNumber: int = lineNumber
        if aPi:
            self.piType: str = aPi[0]
            self.piTitle: str = aPi[1]
            self.piSD: str = aPi[2]
        else:
            self.piType: str = ''
            self.piTitle: str = ''
            self.piSD: str = ''
        self.piSeedType: str = ""
        self.piSeedKeyType: str = ""
        self.piSeedKeyDepth: int = -1

    def __str__(self) -> str:
        rtnStr = f'piType: {self.piType}, piTitle: {self.piTitle}\n'
        rtnStr += f'piSD: {self.piSD}\n'
        rtnStr += f'Line: {self.lineNumber}, piSeedType: {self.piSeedType}, piSeedKeyType: {self.piSeedKeyType}, piSeedKeyDepth: {self.piSeedKeyDepth}'
        return rtnStr

    def json(self) -> dict:
        rtnDict = {
            "piType": self.piType,
            "piTitle": self.piTitle,
            "piSD": self.piSD
        }
        return rtnDict


class PiSeeds():

    def __init__(self, fileName: str = ''):
        self.seedFile = fileName
        self._piSeeds: list[PiSeed] = []
        if self.seedFile:
            seedPiList = readSeedPis(fileName)
            #printIt(f'seedList: {len(seedPiList)}')
            for anFilePi in seedPiList:
                lineNumber = anFilePi[0]
                aPi = (anFilePi[1], anFilePi[2], anFilePi[3])
                theSeed = PiSeed(aPi, lineNumber)
                try:
                    theMatchGroups = piSeedTokenMatch(theSeed.piType, PiSeedTypeREs)
                    theSeed.piSeedType = theMatchGroups[0]
                    theMatchLen = len(theMatchGroups)
                except Exception as e:
                    # tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
                    # printIt(f'piGerminator.py\n{tb_str}',lable.ERROR)
                    # exit()
                    theMatchLen = 0
                    theMatchGroups = {}

                if theMatchLen > 1:
                    theSeed.piSeedKeyType = theMatchGroups[1]
                    if theMatchLen > 2:
                        assert theMatchGroups[2].isnumeric()
                        theSeed.piSeedKeyDepth = int(theMatchGroups[2])

                self._piSeeds.append(theSeed)
        self._currIndex = 0
        self._seedCount = len(self._piSeeds)
        self.piPis = {}

    @property
    def piSeeds(self) -> list[PiSeed]:
        return self._piSeeds
    @property
    def prevPi(self) -> PiSeed:
        rtnPi = PiSeed(None, 0)
        if self._currIndex > 0:
            rtnPi = self.piSeeds[self._currIndex - 1]
        #print(f'rtnPi: {rtnPi}')
        return rtnPi
    @property
    def currPi(self) -> PiSeed:
        rtnPi = PiSeed(None,0)
        if self._currIndex >= 0 and self._currIndex < self._seedCount:
            rtnPi = self.piSeeds[self._currIndex]
        return rtnPi
    @property
    def nextPi(self) -> PiSeed:
        rtnPi = PiSeed(None,0)
        if self._currIndex + 1 < len(self.piSeeds):
            rtnPi = self.piSeeds[self._currIndex + 1]
        return rtnPi
    @property
    def currIndex(self) -> int:
        return self._currIndex
    @property
    def seedCount(self) -> int:
        return self._seedCount

    def next(self) -> PiSeed:
        rtnPi = PiSeed(None, 0)
        if self._currIndex + 1 < len(self.piSeeds):
            self._currIndex += 1
            rtnPi = self.piSeeds[self._currIndex]
        else:
            self._currIndex += 1
            #raise StopIteration
        return rtnPi

PiSeedTypes = ["piScratchDir", "piStruct", "piValuesSetD", "piValue", "piClassGC", "piValueA", "piType", "piIndexer"]
PiSeedTypeVarTypes = ["B", "I", "S", "F", "D", "L", "C", "A"]
PiSeedTypeVarTypesStr = ''.join(PiSeedTypeVarTypes)
PiSeedTypeVarValues = {
    PiSeedTypeVarTypes[0]: False,
    PiSeedTypeVarTypes[1]: 0,
    PiSeedTypeVarTypes[2]: "",
    PiSeedTypeVarTypes[3]: 0.0,
    PiSeedTypeVarTypes[4]: {},
    PiSeedTypeVarTypes[5]: [],
    PiSeedTypeVarTypes[6]: {},
    PiSeedTypeVarTypes[7]: {}
}
PiSeedTypeREs = {
    PiSeedTypes[0]: reCompile('(piScratchDir)'),
    PiSeedTypes[1]: reCompile(f'(piStruct)([{PiSeedTypeVarTypesStr}]'+'{1})([0-9]{2})'),
    PiSeedTypes[2]: reCompile(r'(.+)\.(.*)[\:]*'),
    PiSeedTypes[3]: reCompile('piClassGC(\\d{3})_(.+).json'),
    PiSeedTypes[4]: reCompile('(piValueA)'),
    PiSeedTypes[5]: reCompile('(piType)'),
    PiSeedTypes[6]: reCompile('(piIndexer)'),
    PiSeedTypes[7]: reCompile('(.+)') # this last one returns the input string
} # example piStrucD00
PiFunctionsTokens = ["getPiIDMD5", "getPiMD5", "getMD5"]
PiFunctionsTokenREs = {
    PiFunctionsTokens[0]: reCompile('(getPiIDMD5)\\((.+)\\)'),
    PiFunctionsTokens[1]: reCompile('(getPiMD5)\\((.+)\\)'),
    PiFunctionsTokens[2]: reCompile('(getMD5)\\((.+)\\)')
}
#  piPiValuePiTitle(self.seeds.currPi.piTitle)
# piSeedTitelSplit
def piSeedTitelSplit(piValueTitle: str) -> tuple:
    try:
        #print(f'piSeedTitelSplit: {piTitle}')
        piPiTitleKey, piElemKeys = None, None
        rtnMatch = PiSeedTypeREs[PiSeedTypes[2]].match(piValueTitle)
        if rtnMatch != None:
            theMatchGroups = rtnMatch.groups()
            if len(theMatchGroups) == 2:
                piPiTitleKey, piElemKeys = theMatchGroups

    except Exception as e:
        tb_str = ''.join(format_exception(None, e, e.__traceback__))
        printIt(tb_str,lable.ERROR)
        exit()
    return piPiTitleKey, piElemKeys


def piSeedTokenMatch(seed: str, piSeedTokenREs: dict[str, Pattern[str]]) -> tuple[str | Any, ...]:
    theMatchGroups: tuple[str | Any, ...]
    for piSeedTokenMatcher in piSeedTokenREs:
        rtnMatch = piSeedTokenREs[piSeedTokenMatcher].match(seed)
        if rtnMatch:
            theMatchGroups = rtnMatch.groups()
            break
    return theMatchGroups

def readSeedPis(piFileName) -> list[tuple]:
    piBaseList: list[tuple] = []
    __chkReg = reCompile('\\s*#.*')
    with open(piFileName, 'r') as f:
        inLineNumber = 1
        while True:
            currLine = f.readline()
            if not currLine:
                break
            if not __chkReg.match(currLine) and len(currLine) > 1: # > 1 because blank lines contain \n char.
                try:
                    tokens = shlex.split(currLine)
                    if len(tokens) == 3:
                        piType, piTitle, piSD = tokens
                    elif len(tokens) == 2:
                        piType, piTitle = tokens
                        piSD = ""
                    else: raise Exception("2 or 3 piTokens only")
                    piBaseList.append((inLineNumber,piType, piTitle, piSD))

                except Exception as e:
                    tb_str = ''.join(format_exception(None, e, e.__traceback__))
                    printIt(f'{piFileName}, line:{inLineNumber}\n{tb_str}',lable.ERROR)
                    printIt(f'current line: {currLine}\n{tb_str}',lable.ERROR)
            inLineNumber += 1
    return piBaseList