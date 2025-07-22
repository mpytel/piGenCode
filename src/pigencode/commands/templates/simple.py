from string import Template
from textwrap import dedent

cmdDefTemplate = Template(dedent("""from pigencode.defs.logIt import printIt, lable

def ${defName}(argParse):
    '''Simple ${defName} command implementation'''
    args = argParse.args
    arguments = args.arguments

    printIt(f"Running ${defName} command", lable.INFO)

    if len(arguments) == 0:
        printIt("No arguments provided", lable.WARN)
        return

    for i, arg in enumerate(arguments):
        printIt(f"Argument {i+1}: {arg}", lable.INFO)



"""))

argDefTemplate = Template(dedent("""def ${argName}(argParse):
    args = argParse.args
    printIt(args, lable.INFO)


"""))