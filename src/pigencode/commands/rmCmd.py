import os, json
from pigencode.defs.logIt import printIt, label, cStr, color
from .commands import Commands

cmdObj = Commands()
commands = cmdObj.commands
theDir = os.path.dirname(os.path.realpath(__file__))
jsonFileName = os.path.join(theDir,'commands.json')

def rmCmd(argParse):
    global commands
    args = argParse.args
    theArgs = args.arguments
    argIndex = 0
    cmdName = theArgs[argIndex]
    while argIndex < len(theArgs):
        anArg = theArgs[argIndex]
        if anArg in commands and len(theArgs) == 1:
            if anArg == cmdName:
                if anArg in ["newCmd", "modCmd", "rmCmd"]:
                    printIt(f'Permission denied for "{anArg}".',label.WARN)
                    exit(0)
                chkRm: str = input(f"Perminantly delete {anArg} (y/N): ")
                if chkRm == '': chkRm = 'N'
                if chkRm.lower() == 'y':
                    removeCmd(anArg)
            else:
                printIt(f'Command "{anArg}" must be removed seperataly from "{cmdName}".',label.WARN)
        elif cmdName in commands:
            if anArg in commands[cmdName]:
                chkRm: str = input(f"Perminantly delete {anArg} (y/N): ")
                if chkRm == '': chkRm = 'N'
                if chkRm.lower() == 'y':
                    removeCmdArg(cmdName, anArg)
        else:
            printIt(f'"{cmdName}" is not currently a Command.',label.WARN)
            argIndex = len(theArgs)
        argIndex += 1

def removeCmdArg(cmdName, argName):
    global jsonFileName
    with open(jsonFileName, 'r') as rf:
        theJson = json.load(rf)
        del theJson[cmdName][argName]
    with open(jsonFileName, 'w') as wf:
        json.dump(theJson, wf, indent=2)
    printIt(argName,label.RmArg)

def removeCmd(cmdName):
    global jsonFileName
    with open(jsonFileName, 'r') as rf:
        theJson = json.load(rf)
        del theJson[cmdName]
    with open(jsonFileName, 'w') as wf:
        json.dump(theJson, wf, indent=2)
    pyFileName = f'{cmdName}.py'
    pyFileName = os.path.join(theDir, pyFileName)
    if os.path.isfile(pyFileName):
        os.remove(pyFileName)
    printIt(cmdName,label.RmCmd)
