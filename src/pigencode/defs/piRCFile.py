import json
from pathlib import Path

rcFileName = Path.cwd()
rcFileName = rcFileName.joinpath(f'.{rcFileName.name.lower()}rc')

def getKeyItem(key, defultValue=""):
    rtnValue = readRC(key)
    if not rtnValue:
        rtnValue = defultValue
        writeRC(key, rtnValue)
    return rtnValue

def readRC(rcName: str) -> str:
    global rcFileName
    rcValue = ''
    if rcFileName.is_file():
        with open(rcFileName, 'r') as rf:
            rawRcJson = json.load(rf)
    try:
        rcValue = rawRcJson[rcName]
    except:
       pass
    return rcValue

def writeRC(rcName: str, rcValue: (int|float|str|list|dict)):
    global rcFileName
    if rcFileName.is_file():
        with open(rcFileName, 'r') as rf:
            rawRC = json.load(rf)
    else:
        rawRC = {}
    rawRC[rcName] = rcValue
    with open(rcFileName, 'w') as wf:
        json.dump(rawRC, wf, indent=2)
