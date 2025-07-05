import os, traceback
from ..classes.argParse import ArgParse
from ..defs.logIt import printIt, lable
from ..classes.piGenCode import genPiPiClass
from ..classes.piGenDefCode import genPiDefCode

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
    savedCodeFiles: dict = {}
    try:
        if fileName:
            if os.path.isfile(fileName):
                # Determine file type based on filename pattern
                if "piClassGC" in fileName:
                    savedCodeFiles = genPiPiClass(fileName, verbose)
                elif "piDefGC" in fileName:
                    savedCodeFiles = genPiDefCode(fileName, verbose)
                else:
                    printIt(f'Unknown file type: {fileName}', lable.WARN)
            else:
                printIt(fileName, lable.FileNotFound)
        else:
            # Process all files - both piClassGC and piDefGC
            classFiles = genPiPiClass("", verbose)
            defFiles = genPiDefCode("", verbose)
            savedCodeFiles.update(classFiles)
            savedCodeFiles.update(defFiles)
    except IndexError as e:
        tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
        printIt(f'genCode:\n{tb_str}', lable.ERROR)
        printIt('File name required', lable.IndexError)
    return savedCodeFiles