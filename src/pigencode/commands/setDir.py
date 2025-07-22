from pigencode.defs.logIt import printIt, lable, cStr, color
from pigencode.defs.fileIO import rcFileName, setKeyItem, readJson
from json import dumps

def setDir(argParse):
    args = argParse.args
    theArgs = args.arguments
    lenArgs = len(theArgs)
    fileName = str(rcFileName)
    rcJson = readJson(fileName)
    rcKeys = list(rcJson.keys())
    if lenArgs == 0:
        printIt(f"Valid dirKey include:\n{dumps(rcJson,indent=2)}", lable.INFO)
    elif lenArgs == 1:
        dirKey = theArgs[0]
        if dirKey == 'list':
            printIt(f"Valid dirKey include:\n{dumps(rcJson,indent=2)}", lable.INFO)
        elif dirKey in rcKeys:
            printIt(f"{dirKey} = {rcJson[dirKey]}", lable.INFO)
        else:
            printIt(f"{dirKey} is not a key in {fileName}", lable.WARN)
    elif lenArgs % 2 == 0:
        rcItem = 0
        while rcItem < lenArgs:
            dirKey = theArgs[rcItem]
            rcItem += 1
            dirValue = theArgs[rcItem]
            rcItem += 1
            if dirKey in rcKeys:
                setKeyItem(dirKey, dirValue)
            else:
                printIt(f"{dirKey} is not a key in {fileName}", lable.WARN)
    else:
        printIt(f"A key value pair is missing.", lable.WARN)