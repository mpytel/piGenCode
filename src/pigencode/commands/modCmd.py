import os, copy
from pigencode.defs.logIt import printIt, label
from pigencode.classes.argParse import ArgParse
from .commands import Commands, cmdDescriptionTagStr
from .templates.newCmd import cmdDefTemplate, argDefTemplate
import readline
readline.parse_and_bind('tab: compleat')
readline.parse_and_bind('set editing-mode vi')

cmdObj = Commands()
commands = cmdObj.commands

def modCmd(argParse: ArgParse):
    args = argParse.args
    #cmd = args.commands
    cmdObj = Commands()
    modCmdName = args.arguments[0]
    if modCmdName in cmdObj.commands.keys():
        theArgs = verifyArgsWithDiscriptions(cmdObj, args.arguments)
        if len(theArgs.keys()) > 0:
            updateCMDJson(cmdObj, modCmdName, theArgs)
            printIt(f'"{modCmdName}" modified.',label.ModCmd)
        else:
            printIt(f'"{modCmdName}" unchanged.',label.INFO)
    else:
        printIt(f'"{modCmdName}" does not exists. use newCmd or add it.',label.INFO)

def verifyArgsWithDiscriptions(cmdObj: Commands, theArgs) -> dict:
    rtnDict = {}
    argIndex = 0
    cmdName = theArgs[argIndex]
    while argIndex < len(theArgs):
        argName = theArgs[argIndex]
        if argName[0] == '-':
            if len(argName) >= 2:
                if argName[2] == '-':
                    printIt("Only single hyphen options allowed.",label.WARN)
                    exit(0)
                else:
                    theDisc = input(f'Enter help description for {argName}:\n')
                    if theDisc == '': theDisc = f'no help for {argName}'
            else:
                printIt("Missing ascii letters after hyphen.",label.WARN)
                exit(0)
        else:
            theDisc = ''
            saveDisc = False
            if argIndex == 0 and len(theArgs) == 1:
                chgDisc = input(f'Replace description for {argName} (y/N): ')
                if chgDisc.lower() == 'y':
                    saveDisc = True
            elif argIndex > 0:
                if argName in cmdObj.commands[cmdName].keys():
                    chgDisc = input(f'Replace description for {argName} (y/N): ')
                    if chgDisc.lower() == 'y':
                        saveDisc = True
                else: # add new arg
                    saveDisc = True
                    newArg = True
            if saveDisc:
                theDisc = input(f'Enter help description for {argName}:\n')
                if theDisc == '': theDisc = f'no help for {argName}'
        if saveDisc:
            # only poulate rtnDict with modified discriptions
            rtnDict[argName] = theDisc
        argIndex += 1
    return rtnDict

def writeCodeFile(theArgs: dict) -> str:
    fileDir = os.path.dirname(__file__)
    fileName = os.path.join(fileDir, f'{list(theArgs.keys())[0]}.py')
    if os.path.isfile(fileName):
        rtnStr = label.EXISTS
    else:
        ourStr = cmdCodeBlock(theArgs)
        with open(fileName, 'w') as fw:
            fw.write(ourStr)
        rtnStr = label.SAVED
    return rtnStr

def cmdCodeBlock(theArgs: dict) -> str:
    argNames = list(theArgs.keys())
    defName = argNames[0]
    defTemp = cmdDefTemplate
    argTemp = argDefTemplate
    rtnStr = defTemp.substitute(
        defName=defName
    )
    argIndex = 1
    while argIndex < len(argNames): # add subarg functions
        argName = argNames[argIndex]
        rtnStr += argTemp.substitute(argName=theArgs[argName])
        argIndex += 1
    return rtnStr

def updateCMDJson(cmdObj: Commands, modCmdName: str, theArgs:  dict) -> None:
    commands = copy.deepcopy(cmdObj.commands)
    argNames = list(theArgs.keys())
    if modCmdName in argNames:
        commands[modCmdName][f'{modCmdName}{cmdDescriptionTagStr}'] = theArgs[modCmdName]
        argIndex = 1
    else: argIndex = 0
    while argIndex < len(theArgs): # add subarg functions
        argName = argNames[argIndex]
        commands[modCmdName][argName] = theArgs[argName]
        argIndex += 1
    cmdObj.commands = commands
