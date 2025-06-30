import os, traceback
from re import compile as reCompile
from pathlib import Path
from ..classes.argParse import ArgParse
from ..defs.logIt import printIt, lable
from ..defs.piRCFile import getKeyItem, writeRC
from ..classes.piGermSeeds import PiGermSeeds, germinateSeeds
from ..classes.piSeeds import PiSeeds
from .genCode import genCodeFile

seedFilePattern = reCompile(r'(piSeed)([0-9]{3})_.*(.pi)') # piSeed000_name.pi

def germSeed(argParse: ArgParse):
    args = argParse.parser.parse_args()
    theArgs = args.arguments
    argIndex = 0
    piGermSeeds: PiGermSeeds
    if len(theArgs) == 0:
        piGermSeeds = germAllSeedFiles()
    else:
        try: chkArg = int(theArgs[0])
        except: chkArg = theArgs[0]
        if type(chkArg) == int:
            fileIntStr = str(theArgs[0]).zfill(3)
            fileName = getSeedFileName(fileIntStr)
            piGermSeeds = germSeedFile(fileName)
            if piGermSeeds:
                for classGCFile in piGermSeeds.piClassGCFiles.classGCFilePaths:
                    savedCodeFiles = genCodeFile(str(classGCFile))
                    for savedCodeFile in savedCodeFiles:
                        printIt(f'{savedCodeFile} generated',lable.INFO)
        else:
            while argIndex < len(theArgs):
                fileName = theArgs[argIndex]
                piGermSeeds = germSeedFile(fileName)
                argIndex += 1
    if piGermSeeds:
        for piGermSeed in piGermSeeds.piClassGCFiles.classGCFilePaths:
            printIt(f'classGCFile created: {piGermSeed}',lable.INFO)

def getSeedFileName(fileIntStr) -> str:
    fileName = ''
    seedDir = Path(getKeyItem("piSeedsDir"))
    seedFiles = [str(p.name) for p in seedDir.iterdir() if p.is_file()]
    for fileName in seedFiles:
        theMatch = seedFilePattern.match(fileName)
        if theMatch:
            chkFileIntStr = theMatch.groups()[1]
            if fileIntStr == chkFileIntStr:
                fileName = seedDir.joinpath(fileName)
                break
            else:
                fileName = ''
    return str(fileName)

def germAllSeedFiles(verbose=True) -> PiGermSeeds:
    seedPath = getSeedPath()
    piSeeds = PiSeeds()
    piGermSeeds = PiGermSeeds(piSeeds)
    if seedPath:
        seedFiles = [str(p.name) for p in seedPath.iterdir() if p.is_file()]
        seedFiles.sort()
        for fileName in seedFiles:
            theMatch = seedFilePattern.match(fileName)
            print('theMatch', fileName, theMatch)
            if theMatch:
                seedFile = seedPath.joinpath(fileName)
                piGermSeeds = germSeedFile(seedFile, verbose)
    else:
        printIt(f'No piSeed Directory founc: {seedPath}',lable.FileNotFound)
    return piGermSeeds

def getSeedPath() -> Path | None:
    # get possible path from resource file and set it to the default
    # directory name if no resorce file or key is preset
    seedDirName = "piSeeds"
    seedPath = Path(getKeyItem("piSeedsDir", seedDirName))
    if seedPath.is_dir():
        return seedPath
    else:
        seedPath = None
    # check if current directory or subdirectry is a piSeeds directory
    cwd = Path.cwd()
    if cwd.name == seedDirName:
         seedPath = cwd
    else:
        cwdDirs = [str(p.name) for p in cwd.iterdir() if p.is_dir()]
        if seedDirName in cwdDirs:
            seedPath = cwd.joinpath(seedDirName)
    if not seedPath:
        return seedPath
    writeRC("piSeedsDir", str(seedPath))
    return seedPath





def germSeedFile(fileName, verbose=True) -> PiGermSeeds:
    piGermSeeds: PiGermSeeds
    try:
        if os.path.isfile(fileName):
            piGermSeeds = germinateSeeds(fileName)
            seedCount = piGermSeeds.seeds.seedCount
            if verbose: printIt(f'{seedCount} seeds germinated from: {fileName}',lable.INFO)
        else:
            printIt(fileName, lable.FileNotFound)
            exit()
    except IndexError as e:
        tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
        printIt(f'germSeedFile:\n{tb_str}', lable.ERROR)
        printIt('File name required', lable.IndexError)
    return piGermSeeds


