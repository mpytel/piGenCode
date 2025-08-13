# optSwitches classes - synced from existing code

import json
from pathlib import Path
from pi.defs.logIt import printIt, lable
from pi.defs.piFileIO import getKeyItem

rcFileDir = Path(__file__).resolve().parents[2]
rcFileName = rcFileDir.joinpath('.pirc')

class OptSwitches():
    def __init__(self, switchFlags: dict):
        self.switchFlags = switchFlags
        self.optSwitches = readOptSwitches()

    def toggleSwitchFlag(self, switchFlag: str):
        '''toggle the Switch Flag in rcFileName '''
        optSwitches = {}
        optSwitches["switcheFlags"] = {}
        currSwitchFlag = switchFlag[1:]
        if switchFlag[0] in '+':
            currSwitchValue = True # not (self.optSwitches["switcheFlags"][currSwitchFlag] == True)
        else:
            currSwitchValue  = False
        try:
            self.optSwitches["switcheFlags"][currSwitchFlag] = currSwitchValue
        except:
            print('here')
            self.optSwitches["switcheFlags"][currSwitchFlag] = True
        writeOptJson(self.optSwitches, self.switchFlags)

def readOptSwitches() -> dict:
    global rcFileName
    optSwitches = {}
    if rcFileName.is_file():
        with open(rcFileName, 'r') as rf:
            rawRcJson = json.load(rf)
        if "switcheFlags" in rawRcJson.keys():
            optSwitches["switcheFlags"] = rawRcJson["switcheFlags"]
        else:
            optSwitches["switcheFlags"] = {}
    else:
        optSwitches["switcheFlags"] = {}
    return optSwitches

def writeOptJson(optSwitches: dict, switchFlags: dict):
    global rcFileName
    rawRC = {}
    if rcFileName.is_file():
        with open(rcFileName, 'r') as rf:
            rawRC = json.load(rf)
    rawRC = rawRC | optSwitches
    for switchFlag in switchFlags.keys(): # fill in missing items'
        try: _ = rawRC["switcheFlags"][switchFlag]
        except: rawRC["switcheFlags"][switchFlag] = False
    printIt(formatOptStr(rawRC["switcheFlags"]), lable.INFO)
    with open(rcFileName, 'w') as wf:
        json.dump(rawRC, wf, indent=2)

def formatOptStr(optSwitches: dict) -> str:
    rtnStr = "Current option values: "
    for cmdOpt in optSwitches:
        rtnStr += f'-{cmdOpt}={optSwitches[cmdOpt]}, '
    rtnStr = rtnStr[:-2]
    return rtnStr