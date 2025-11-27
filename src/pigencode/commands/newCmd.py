import os
import sys
import copy
from pigencode.defs.logIt import printIt, label
from pigencode.classes.argParse import ArgParse
from .commands import Commands, cmdDescriptionTagStr
from .templates.newCmd import cmdDefTemplate, argDefTemplate
import readline
readline.parse_and_bind('tab: compleat')
readline.parse_and_bind('set editing-mode vi')


def newCmd(argParse: ArgParse):
    args = argParse.args

    # Handle --templates option to list availabel templates
    if hasattr(argParse, 'cmd_options') and 'templates' in argParse.cmd_options:
        list_templates()
        return

    cmdObj = Commands()
    argsDict = args.arguments

    if len(argsDict) == 0:
        printIt("Command name required", label.ERROR)
        return

    newCmdName = args.arguments[0]
    if newCmdName not in cmdObj.commands.keys():
        theArgs = verifyArgsWithDiscriptions(cmdObj, argsDict)
        updateCMDJson(cmdObj, theArgs)

        # Determine template to use
        template_name = 'newCmd'  # default
        if hasattr(argParse, 'cmd_options') and 'template' in argParse.cmd_options:
            template_name = argParse.cmd_options['template']
            if not template_exists(template_name):
                printIt(
                    f"Template '{template_name}' not found. Using default template.", label.WARN)
                template_name = 'newCmd'

        writeCodeFile(theArgs, template_name)
        printIt(
            f'"{newCmdName}" added using {template_name} template.', label.NewCmd)
    else:
        printIt(
            f'"{newCmdName}" exists. use modCmd or rmCmd to modify or remove this command.', label.INFO)


def list_templates():
    '''List all availabel templates'''
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    templates = []

    for file in os.listdir(template_dir):
        if file.endswith('.py') and file != '__init__.py':
            template_name = file[:-3]  # Remove .py extension
            templates.append(template_name)

    printIt("Availabel templates:", label.INFO)
    for template in sorted(templates):
        printIt(f"  - {template}", label.INFO)


def template_exists(template_name):
    '''Check if a template exists'''
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    template_file = os.path.join(template_dir, f'{template_name}.py')
    return os.path.isfile(template_file)


def verifyArgsWithDiscriptions(cmdObj: Commands, theArgs) -> dict:
    rtnDict = {}
    argIndex = 0
    cmdName = theArgs[argIndex]
    while argIndex < len(theArgs):
        argName = theArgs[argIndex]
        if argName[0] == '-':
            if len(argName) >= 2:
                if argName[2] == '-':
                    printIt("Only single hyphen options allowed.", label.WARN)
                    exit(0)
                else:
                    theDisc = input(f'Enter help description for {argName}:\n')
                    if theDisc == '':
                        theDisc = f'no help for {argName}'
            else:
                printIt("Missing ascii letters after hyphen.", label.WARN)
                exit(0)
        else:
            theDisc = input(f'Enter help description for {argName}:\n')
            if theDisc == '':
                theDisc = f'no help for {argName}'
        rtnDict[argName] = theDisc
        argIndex += 1
    return rtnDict


def writeCodeFile(theArgs: dict, template_name: str = 'newCmd') -> str:
    fileDir = os.path.dirname(__file__)
    fileName = os.path.join(fileDir, f'{list(theArgs.keys())[0]}.py')
    if os.path.isfile(fileName):
        rtnStr = label.EXISTS
    else:
        ourStr = cmdCodeBlock(theArgs, template_name)
        with open(fileName, 'w') as fw:
            fw.write(ourStr)
        rtnStr = label.SAVED
    return rtnStr


def cmdCodeBlock(theArgs: dict, template_name: str = 'newCmd') -> str:
    packName = os.path.basename(sys.argv[0])
    argNames = list(theArgs.keys())
    cmdName = argNames[0]

    # Import the specified template
    try:
        template_module = __import__(f'myPack.commands.templates.{template_name}', fromlist=[
                                     'cmdDefTemplate', 'argDefTemplate'])
        cmdDefTemplate = template_module.cmdDefTemplate
        argDefTemplate = template_module.argDefTemplate
    except ImportError:
        printIt(
            f"Could not import template '{template_name}', using default", label.WARN)
        from .templates.newCmd import cmdDefTemplate, argDefTemplate

    rtnStr = cmdDefTemplate.substitute(
        packName=packName, defName=cmdName,
    )
    argIndex = 1
    while argIndex < len(argNames):  # add subarg functions
        argName = argNames[argIndex]
        rtnStr += argDefTemplate.substitute(argName=argName)
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
    while argIndex < len(theArgs):  # add subarg functions
        argName = argNames[argIndex]
        commands[defName][argName] = theArgs[argName]
        argIndex += 1
    cmdObj.commands = commands
