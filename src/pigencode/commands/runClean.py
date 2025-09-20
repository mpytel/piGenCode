from pathlib import Path
from .rmGC import rmGC
from .syncCode import syncDirectory
from .germSeed import germAllSeedFiles
from .genCode import genCodeFile


def runClean(argParse):
    rmGC(argParse)
    options = {}
    targetPath = Path("testCode/pi")
    options["dest-dir"] = "holdCode/pi"
    syncDirectory(targetPath, options)
    germAllSeedFiles()
    savedCodeFiles = genCodeFile("")

