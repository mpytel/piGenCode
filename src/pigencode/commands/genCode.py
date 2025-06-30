import os, traceback
from ..classes.argParse import ArgParse
from ..defs.logIt import printIt, lable
from ..classes.piGenCode import genPiPiClass

def genCode(argParse: ArgParse):
    args = argParse.parser.parse_args()
    theArgs = args.arguments
    fileName = ""
    if theArgs:
        fileName = theArgs[0]
    savedCodeFiles = genCodeFile(fileName)
    for savedCodeFile in savedCodeFiles:
        printIt(f'{savedCodeFile} generated',lable.INFO)

def genCodeFile(fileName="", verbose=False) -> dict:
    savedCodeFiles: dict
    try:
        if fileName:
            if os.path.isfile(fileName):
                savedCodeFiles = genPiPiClass(fileName, verbose)
            else:
                printIt(fileName, lable.FileNotFound)
        else:
            savedCodeFiles = genPiPiClass()
    except IndexError as e:
        tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
        printIt(f'germSeed:\n{tb_str}', lable.ERROR)
        printIt('File name required', lable.IndexError)
    return savedCodeFiles