import os, traceback
from re import compile as reCompile
from pathlib import Path
from pigencode.classes.argParse import ArgParse
from pigencode.defs.logIt import printIt, lable
from pigencode.defs.fileIO import getKeyItem, writeRC, piGCDirs
from pigencode.defs.getSeedPath import getSeedPath
from pigencode.classes.piGermSeeds import PiGermSeeds, germinateSeeds
from pigencode.classes.piSeeds import PiSeeds
from .genCode import genCodeFile

seedFilePattern = reCompile(
    r'(piSeed)([0-9]{3})(?:_.*)?(.pi)')  # piSeed000_name.pi

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
                # Generate code for piClassGC files
                for classGCFile in piGermSeeds.piClassGCFiles.classGCFilePaths:
                    savedCodeFiles = genCodeFile(str(classGCFile))
                    for savedCodeFile in savedCodeFiles:
                        printIt(f'{savedCodeFile} generated',lable.INFO)
                # Generate code for piDefGC files
                for defGCFile in piGermSeeds.piDefGCFiles.defGCFilePaths:
                    savedCodeFiles = genCodeFile(str(defGCFile))
                    for savedCodeFile in savedCodeFiles:
                        printIt(f'{savedCodeFile} generated',lable.INFO)
        else:
            while argIndex < len(theArgs):
                fileName = theArgs[argIndex]
                piGermSeeds = germSeedFile(fileName)
                if piGermSeeds:
                    # Generate code for piClassGC files
                    for classGCFile in piGermSeeds.piClassGCFiles.classGCFilePaths:
                        savedCodeFiles = genCodeFile(str(classGCFile))
                        for savedCodeFile in savedCodeFiles:
                            printIt(f'{savedCodeFile} generated',lable.INFO)
                    # Generate code for piDefGC files
                    for defGCFile in piGermSeeds.piDefGCFiles.defGCFilePaths:
                        savedCodeFiles = genCodeFile(str(defGCFile))
                        for savedCodeFile in savedCodeFiles:
                            printIt(f'{savedCodeFile} generated',lable.INFO)
                argIndex += 1
        if piGermSeeds:
            for piGermSeed in piGermSeeds.piClassGCFiles.classGCFilePaths:
                printIt(f'classGCFile created: {piGermSeed}',lable.INFO)
            for piGermSeed in piGermSeeds.piDefGCFiles.defGCFilePaths:
                printIt(f'defGCFile created: {piGermSeed}',lable.INFO)

def getSeedFileName(fileIntStr) -> str:
    fileName = ''
    seedDir = Path(getKeyItem(piGCDirs[0]))
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
            #print('theMatch', fileName, theMatch)
            if theMatch:
                seedFile = str(seedPath.joinpath(fileName))
                piGermSeeds = germSeedFile(seedFile, verbose)
    else:
        printIt(f'No piSeed Directory founc: {seedPath}',lable.FileNotFound)
    return piGermSeeds

def germSeedFile(fileName: str, verbose=True) -> PiGermSeeds:
    piGermSeeds: PiGermSeeds
    seedFilePath = Path(fileName)
    try:
        if seedFilePath.is_file():
            piGermSeeds = germinateSeeds(fileName)
            seedCount = piGermSeeds.seeds.seedCount
            if verbose:
                printIt(
                    f'{seedCount} seeds germinated from: {seedFilePath.name}', lable.INFO)
        else:
            printIt(fileName, lable.FileNotFound)
            exit()
    except IndexError as e:
        tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
        printIt(f'germSeedFile:\n{tb_str}', lable.ERROR)
        printIt('File name required', lable.IndexError)
    return piGermSeeds

'''
cp /Users/primwind/proj/python/piGenCode/piSeeds/holdSeeds/piSeed002_piTouch.pi ./piSeeds/
cp /Users/primwind/proj/python/piGenCode/piSeeds/holdSeeds/piSeed003_piIndexer.pi ./piSeeds/
cp /Users/primwind/proj/python/piGenCode/piSeeds/holdSeeds/piSeed004_piInfluence.pi ./piSeeds/
cp /Users/primwind/proj/python/piGenCode/piSeeds/holdSeeds/piSeed005_pi.pi ./piSeeds/
cp /Users/primwind/proj/python/piGenCode/piSeeds/holdSeeds/piSeed006_argument.pi ./piSeeds/
cp /Users/primwind/proj/python/piGenCode/piSeeds/holdSeeds/piSeed007_fromImports.pi ./piSeeds/
cp /Users/primwind/proj/python/piGenCode/piSeeds/holdSeeds/piSeed008_piClassGC.pi ./piSeeds/
'''


