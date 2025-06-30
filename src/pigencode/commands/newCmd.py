import os, sys, copy
from ..defs.logIt import printIt, lable
from ..classes.argParse import ArgParse
from .commands import Commands, cmdDescriptionTagStr
from .templates.newCmd import cmdDefTemplate, argDefTemplate
import readline
readline.parse_and_bind('tab: compleat')
readline.parse_and_bind('set editing-mode vi')

def newCmd(argParse: ArgParse):
    args = argParse.args
    #cmd = args.commands
    cmdObj = Commands()
    argsDict = args.arguments
    newCmdName = args.arguments[0]
    if newCmdName not in cmdObj.commands.keys():
        theArgs = verifyArgsWithDiscriptions(cmdObj, argsDict)
        updateCMDJson(cmdObj, theArgs)
        writeCodeFile(theArgs)
        printIt(f'"{newCmdName}" added.',lable.NewCmd)
    else:
        printIt(f'"{newCmdName}" exists. use modCmd or rmCmd to modiify or remove this command.',lable.INFO)

def verifyArgsWithDiscriptions(cmdObj: Commands, theArgs) -> dict:
    rtnDict = {}
    argIndex = 0
    cmdName = theArgs[argIndex]
    while argIndex < len(theArgs):
        argName = theArgs[argIndex]
        if argName[0] == '-':
            if len(argName) >= 2:
                if argName[2] == '-':
                    printIt("Only single hyphen options allowed.",lable.WARN)
                    exit(0)
                else:
                    theDisc = input(f'Enter help description for {argName}:\n')
                    if theDisc == '': theDisc = f'no help for {argName}'
            else:
                printIt("Missing ascii letters after hyphen.",lable.WARN)
                exit(0)
        else:
            theDisc = input(f'Enter help description for {argName}:\n')
            if theDisc == '': theDisc = f'no help for {argName}'
        rtnDict[argName] = theDisc
        argIndex += 1
    return rtnDict

def writeCodeFile(theArgs: dict) -> str:
    fileDir = os.path.dirname(__file__)
    fileName = os.path.join(fileDir, f'{list(theArgs.keys())[0]}.py')
    if os.path.isfile(fileName):
        rtnStr = lable.EXISTS
    else:
        ourStr = cmdCodeBlock(theArgs)
        with open(fileName, 'w') as fw:
            fw.write(ourStr)
        rtnStr = lable.SAVED
    return rtnStr

def cmdCodeBlock(theArgs: dict) -> str:
    packName = os.path.basename(sys.argv[0])
    argNames = list(theArgs.keys())
    cmdName = argNames[0]
    defTemp = cmdDefTemplate
    argTemp = argDefTemplate
    rtnStr = defTemp.substitute(
        packName=packName, defName=cmdName,
    )
    argIndex = 1
    while argIndex < len(argNames): # add subarg functions
        argName = argNames[argIndex]
        rtnStr += argTemp.substitute(argName=argName)
        argIndex += 1
    return rtnStr

def updateCMDJson(cmdObj: Commands, theArgs:  dict) -> None:
    commands = copy.deepcopy(cmdObj.commands)
    argNames = list(theArgs.keys())
    defName = argNames[0]
    defDiscription = theArgs[argNames[0]]
    commands[defName] = {}
    commands[defName][f'{defName}{cmdDescriptionTagStr}'] = defDiscription
    argIndex = 1
    while argIndex < len(theArgs): # add subarg functions
        argName = argNames[argIndex]
        commands[defName][argName] = theArgs[argName]
        argIndex += 1
    cmdObj.commands = commands
