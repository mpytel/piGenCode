import os, time, traceback
from json import dumps
from inspect import currentframe, getframeinfo
from pathlib import Path

# Class of different termianl styles
class color():

    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    UNDERLINE = "\033[4m"
    RESET = "\033[0m"

    # message: color
    l2cDict: dict = {
        "BK": RESET,
        "ERROR: ": RED,
        "PASS: ": GREEN,
        "WARN: ": YELLOW,
        "SAVED: ": BLUE,
        "DEBUG: ": MAGENTA,
        "REPLACED: ": CYAN,
        "INFO: ": WHITE,
        "IMPORT: ": UNDERLINE,
        "RESET": RESET,
        "File Not Found: ": YELLOW,
        "Directory Not Found: ": YELLOW,
        "FAIL: ": RED,
        "Useage: ": WHITE,
        "DELETE: ": YELLOW,
        "EXISTS: ": GREEN,
        "READ: ": GREEN,
        "TOUCHED: ": GREEN,
        "MKDIR: ": GREEN,
        "NEW CMD ADDED: ": GREEN,
        "CMD MODIFIED: ": GREEN,
        "CMD REMOVED: ": GREEN,
        "ARG REMOVED: ": GREEN,
        "IndexError: ": RED,
        "Testing: ": CYAN,
        "Update: ": CYAN,
        "PIPI: ": CYAN,
        "TODO: ": CYAN,
        "ABORTPRT": YELLOW
        }


class label():
    SAVED = "SAVED: "
    REPLACED = "REPLACED: "
    BLANK = "BK"
    ERROR = "ERROR: "
    PASS = "PASS: "
    WARN = "WARN: "
    DEBUG = "DEBUG: "
    INFO = "INFO: "
    IMPORT = "IMPORT: "
    RESET = "RESET"
    FileNotFound = "File Not Found: "
    DirNotFound = "Directory Not Found: "
    FAIL = "FAIL: "
    Useage = "Useage: "
    MKDIR = "MKDIR: "
    DELETE = "DELETE: "
    EXISTS = "EXISTS: "
    READ = "READ: "
    TOUCHED = "TOUCHED: "
    NewCmd = "NEW CMD ADDED: "
    ModCmd = "CMD MODIFIED: "
    RmCmd = "CMD REMOVED: "
    RmArg = "ARG REMOVED: "
    IndexError = "IndexError: "
    TESTING = "Testing: "
    UPDATE = "Update: "
    NewPi = "PIPI: "
    TODO = "TODO: "
    ABORTPRT = "ABORTPRT"


# log function
def logIt(*message, logFileName="pi.log"):
    # write log
    now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    prtStr = ""
    needClip = False
    if len(message) > 0:
        for mess in message:
            if mess == label.BLANK:
                pass
            elif mess in color.l2cDict:
                prtStr = mess + prtStr
            else:
                needClip = True
                prtStr += str(mess) + " "
        if needClip:
            prtStr = prtStr[:-1]

    prtStr = "["+now+"] "+prtStr+"\n"

    with open(logFileName, "a") as f:
        f.write(prtStr)

def printIt(*message, asStr: bool=False) -> str:
    prtStr = ""
    rtnStr = ""
    needClip = False
    abortPrt = False
    for mess in message:
        if mess == label.ABORTPRT: abortPrt = True
    if not abortPrt:
        if len(message) > 0:
            for mess in message:
                if mess == label.BLANK:
                    prtStr = message[0]
                    rtnStr = message[0]
                    needClip = False
                elif mess in color.l2cDict:
                    prtStr = color.l2cDict[mess] + mess + color.RESET + prtStr
                    rtnStr = mess + rtnStr
                else:
                    needClip = True
                    prtStr += str(mess) + " "
                    rtnStr += str(mess) + " "
            if needClip:
                prtStr = prtStr[:-1]
                rtnStr = rtnStr[:-1]
        if not asStr: print(prtStr)
    return rtnStr

def cStr(inStr:str, cVal:str):
    return cVal + inStr + color.RESET

def deleteLog(logFileName="pi.log"):
    if os.path.isfile(logFileName): os.remove(logFileName)
    if os.path.isfile("pis.txt"): os.remove("pis.txt")

def printPiPath(thePiPath: str | Path):
    try:
        if type(thePiPath) == str: chkPiPath = Path(thePiPath)
        else: chkPiPath = thePiPath
        if chkPiPath.is_dir:
            piPathList = str(thePiPath)[1:].split('/')
        else:
            raise Exception(thePiPath)
        listLen = len(piPathList)
        # 0/1/2/U/R/D/S/T/F
        # 0/1/2/3/4/5/6/7/8 - 9
        # 8/7/6/5/4/3/2/1/0 - 9
        # 7/6/5/4/3/2/1/0 - 8
        pathItems = ['user','realm','domain','subject','type','file']
        prtStr = ''
        if listLen < 7:
            raise Exception(f'Path less then subject\nPath: {thePiPath}')
        elif listLen == 8:
            for i in range(5): # -(listLen-4-i)
                prtStr += f'{pathItems[i]}: {piPathList[-(listLen-4-i)]}\n'
        elif listLen == 9:
            for i in range(6): # -(listLen-4-i)
                prtStr += f'{pathItems[i]}: {piPathList[-(listLen-3-i)]}\n'
        else: Exception("Path is to long")
        print(prtStr[:-1])
    except Exception as e:
        printIt(e.args[0], label.DirNotFound)
        tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
        printIt(tb_str,label.ERROR)
        exit()

def piDictPrint(theDict, piDictTitle="no title"):
    ps = dumps(theDict,indent=2)
    printIt(f'{piDictTitle}:\n{ps}',label.INFO)

def getCodeFile():
    cf = currentframe()
    codeObj =cf.f_back.f_code
    codeObjStr = str(codeObj).split(",")[1].split('"')[1]
    codeObjStr = os.path.basename(codeObjStr)
    return codeObjStr

def getCodeLine():
    cf = currentframe()
    return cf.f_back.f_lineno


def printTraceback():
    traceback.print_stack()
    exit()
