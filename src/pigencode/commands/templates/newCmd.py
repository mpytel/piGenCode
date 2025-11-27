from string import Template
from textwrap import dedent

cmdDefTemplate = Template(dedent("""from pigencode.defs.logIt import printIt, label, cStr, color
from .commands import Commands

cmdObj = Commands()
commands = cmdObj.commands

def ${defName}(argParse):
    global commands
    args = argParse.args
    theCmd = args.commands[0]
    theArgNames = list(commands[theCmd].keys())
    theArgs = args.arguments
    argIndex = 0
    nonCmdArg = True
    printIt("Modify default behavour in src/${packName}/commands/${defName}.py", label.DEBUG)
    # delete place holder code bellow that loops though arguments provided
    # when this command is called when not needed.
    # Note: that function having a name that is entered as an argument part
    # of this code and is called using the built in exec function. while argIndex < len(theArgs):
    while argIndex < len(theArgs):
        anArg = theArgs[argIndex]
        if anArg in commands[theCmd]:
            nonCmdArg = False
            exec(f"{anArg}(argParse)")
        elif nonCmdArg:  # not a know aregument for this {packName} {defName} command
            if len(theArgNames) > 1:
                printIt(f"{theArgNames[argIndex+1]}: {anArg}",label.INFO)
            else:
                printIt(f"unknown argument: {anArg}", label.INFO)
        argIndex += 1
    if len(theArgs) == 0:
        printIt("no argument(s) entered", label.INFO)


"""))

argDefTemplate = Template(dedent("""def ${argName}(argParse):
    args = argParse.args
    printIt(args, label.INFO)


"""))