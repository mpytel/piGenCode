import os, traceback, re
from pathlib import Path
from ..classes.argParse import ArgParse
from ..defs.logIt import printIt, lable
from ..defs.fileIO import getKeyItem
from ..classes.piGenCode import genPiPiClass
from ..classes.piGenDefCode import genPiDefCode
from ..classes.piGenClassCode import genPiGenClass

def checkPiGermsDirectory():
    """Check if piGerms directory exists and provide helpful error message if not"""
    piGermsDir = Path(getKeyItem("piScratchDir", "piGerms"))

    if not piGermsDir.exists():
        printIt("ERROR: piGerms directory not found", lable.ERROR)
        printIt(f"Expected location: {piGermsDir}", lable.ERROR)
        printIt("", lable.INFO)
        printIt("The piGerms directory contains the JSON configuration files needed for code generation.", lable.INFO)
        printIt("This directory is created when piSeed files are processed with 'germSeed'.", lable.INFO)
        printIt("", lable.INFO)
        printIt("To fix this issue:", lable.INFO)
        printIt("  1. Run 'pigencode germSeed' to process all piSeed files", lable.INFO)
        printIt("  2. Or run 'pigencode germSeed <number>' to process a specific piSeed file", lable.INFO)
        printIt("  3. Then run 'pigencode genCode' again", lable.INFO)
        printIt("", lable.INFO)
        printIt("Examples:", lable.INFO)
        printIt("  pigencode germSeed           # Process all piSeed files", lable.INFO)
        printIt("  pigencode germSeed 21        # Process piSeed021", lable.INFO)
        printIt("  pigencode genCode piClass 21 # Generate code after germSeed", lable.INFO)
        return False

    return True

def genCode(argParse: ArgParse):
    # Check if piGerms directory exists before proceeding
    if not checkPiGermsDirectory():
        return

    # Use the already parsed arguments from ArgParse.__init__
    args = argParse.args
    theArgs = args.arguments

    if not theArgs:
        # No arguments - process all files
        savedCodeFiles = genCodeFile("")
    elif len(theArgs) == 1:
        # Single argument - could be filename, number shortcut, or old syntax
        arg = theArgs[0]

        # Check if argument is a number (shortcut syntax)
        if isinstance(arg, int) or (isinstance(arg, str) and arg.isdigit()):
            number = int(arg)
            savedCodeFiles = processNumberShortcut(number)
        else:
            # Treat as filename
            savedCodeFiles = genCodeFile(arg)
    else:
        # Multiple arguments - new shortcut syntax
        savedCodeFiles = processShortcutSyntax(theArgs)

    for savedCodeFile in savedCodeFiles:
        printIt(f'{savedCodeFile} generated', lable.INFO)

def processNumberShortcut(number: int) -> dict:
    """
    Process number-only shortcut like 'genCode 31'
    Automatically detects file type by searching for germ files
    """
    savedCodeFiles: dict = {}

    # Search for germ files with this number in all subdirectories
    fileTypes = ['piclass', 'pidef', 'pigenclass']
    foundFiles = []

    for fileType in fileTypes:
        fileName = findGermFile(fileType, number)
        if fileName:
            foundFiles.append((fileType, fileName))

    if not foundFiles:
        printIt(f"No germ files found for number {number:03d}", lable.ERROR)
        printIt("Searched for:", lable.INFO)
        printIt(f"  • piGerms/piClassGC/piClassGC{number:03d}_*.json", lable.INFO)
        printIt(f"  • piGerms/piDefGC/piDefGC{number:03d}_*.json", lable.INFO)
        printIt(f"  • piGerms/piGenClass/piGenClass{number:03d}_*.json", lable.INFO)
        return savedCodeFiles

    if len(foundFiles) > 1:
        printIt(f"Multiple germ files found for number {number:03d}:", lable.WARN)
        for fileType, fileName in foundFiles:
            printIt(f"  • {fileType}: {fileName}", lable.WARN)
        printIt("Using the first one found. Use explicit syntax to specify type:", lable.WARN)
        printIt(f"  piGenCode genCode piClass {number}", lable.WARN)
        printIt(f"  piGenCode genCode piDef {number}", lable.WARN)
        printIt(f"  piGenCode genCode piGenClass {number}", lable.WARN)

    # Process the first (or only) found file
    fileType, fileName = foundFiles[0]
    printIt(f"Processing {fileType} file: {fileName}", lable.INFO)

    try:
        if fileType == 'piclass':
            files = genPiPiClass(fileName, False)
        elif fileType == 'pidef':
            files = genPiDefCode(fileName, False)
        else:  # pigenclass
            result = genPiGenClass(fileName)
            if result:
                files = {result: fileName}
            else:
                files = {}
        savedCodeFiles.update(files)
    except Exception as e:
        printIt(f"Error processing {fileName}: {e}", lable.ERROR)

    return savedCodeFiles

def processShortcutSyntax(args: list) -> dict:
    """
    Process shortcut syntax like:
    - piClass 21 (single file)
    - piDef 2 (single file)
    - piGenClass 1 2 (multiple files)
    - piClass 4-16 (range)
    - piGenClass 1-3 (range)
    - piClass 5 7 21 (multiple files)
    - piClass 2 8 14-21 (combination)
    """
    savedCodeFiles: dict = {}

    if len(args) < 2:
        printUsageHelp()
        return savedCodeFiles

    fileType = args[0].lower()
    numberArgs = args[1:]

    # Validate file type
    if fileType not in ['piclass', 'pidef', 'pigenclass']:
        printIt(f"Invalid file type '{args[0]}'. Use 'piClass', 'piDef', or 'piGenClass'", lable.ERROR)
        printUsageHelp()
        return savedCodeFiles

    # Parse number arguments and expand ranges
    numbers = parseNumberArguments(numberArgs)

    if not numbers:
        printIt("No valid numbers found in arguments", lable.ERROR)
        printUsageHelp()
        return savedCodeFiles

    printIt(f"Processing {fileType} files: {sorted(numbers)}", lable.INFO)

    # Generate files for each number
    successCount = 0
    for number in sorted(numbers):
        fileName = findGermFile(fileType, number)
        if fileName:
            try:
                if fileType == 'piclass':
                    files = genPiPiClass(fileName, False)
                elif fileType == 'pidef':
                    files = genPiDefCode(fileName, False)
                else:  # pigenclass
                    result = genPiGenClass(fileName)
                    if result:
                        files = {result: fileName}
                    else:
                        files = {}
                savedCodeFiles.update(files)
                successCount += 1
            except Exception as e:
                printIt(f"Error processing {fileName}: {e}", lable.ERROR)
        else:
            printIt(f"Germ file not found for {fileType} {number:03d}", lable.WARN)

    if successCount > 0:
        printIt(f"Successfully processed {successCount} germ files", lable.INFO)

    return savedCodeFiles

def printUsageHelp():
    """Print usage help for the shortcut syntax"""
    printIt("Usage examples:", lable.INFO)
    printIt("  piGenCode genCode piClass 21          # Generate from piClassGC021", lable.INFO)
    printIt("  piGenCode genCode piDef 2             # Generate from piDefGC002", lable.INFO)
    printIt("  piGenCode genCode piGenClass 1 2      # Generate from piGenClass001 and piGenClass002", lable.INFO)
    printIt("  piGenCode genCode piClass 4-16        # Generate from piClassGC004 to piClassGC016", lable.INFO)
    printIt("  piGenCode genCode piGenClass 1-3      # Generate from piGenClass001 to piGenClass003", lable.INFO)
    printIt("  piGenCode genCode piClass 5 7 21      # Generate from piClassGC005, 007, and 021", lable.INFO)
    printIt("  piGenCode genCode piClass 2 8 14-21   # Generate from piClassGC002, 008, and 014-021", lable.INFO)

def parseNumberArguments(args: list) -> set:
    """Parse number arguments supporting ranges (4-16) and individual numbers (5 7 21)"""
    numbers = set()

    for arg in args:
        # Convert to string if it's not already
        arg_str = str(arg)

        if '-' in arg_str and not arg_str.startswith('-'):
            # Range format: 4-16
            try:
                start, end = arg_str.split('-', 1)
                start_num = int(start)
                end_num = int(end)
                if start_num <= end_num:
                    numbers.update(range(start_num, end_num + 1))
                else:
                    printIt(f"Invalid range '{arg_str}': start must be <= end", lable.WARN)
            except ValueError:
                printIt(f"Invalid range format '{arg_str}': use format like '4-16'", lable.WARN)
        else:
            # Individual number
            try:
                numbers.add(int(arg_str))
            except ValueError:
                printIt(f"Invalid number '{arg_str}': must be an integer", lable.WARN)

    return numbers

def findGermFile(fileType: str, number: int) -> str:
    """Find the germ file for the given type and number"""
    try:
        # Determine the subdirectory and pattern
        if fileType == 'piclass':
            subdir = 'piClassGC'
            pattern = f'piClassGC{number:03d}_*.json'
        elif fileType == 'pidef':
            subdir = 'piDefGC'
            pattern = f'piDefGC{number:03d}_*.json'
        else:  # pigenclass
            subdir = 'piGenClass'
            pattern = f'piGenClass{number:03d}_*.json'

        # Look in piGerms subdirectory
        piGermsDir = Path(getKeyItem("piScratchDir", "piGerms"))
        germDir = piGermsDir / subdir

        if not piGermsDir.exists():
            printIt(f"piGerms directory not found: {piGermsDir}", lable.ERROR)
            printIt("Run 'pigencode germSeed' first to create germ files", lable.INFO)
            return ""

        if not germDir.exists():
            printIt(f"Germ subdirectory not found: {germDir}", lable.WARN)
            printIt(f"No {fileType} files have been processed yet", lable.INFO)
            printIt(f"Run 'pigencode germSeed' to process piSeed files", lable.INFO)
            return ""

        # Find matching files
        matchingFiles = list(germDir.glob(pattern))
        if matchingFiles:
            return str(matchingFiles[0])  # Return first match

        # File not found - provide helpful message
        printIt(f"Germ file not found: {germDir}/{pattern}", lable.WARN)
        printIt(f"Make sure piSeed{number:03d}_*.pi exists and has been processed with 'germSeed'", lable.INFO)
        return ""

    except Exception as e:
        printIt(f"Error finding germ file for {fileType} {number}: {e}", lable.ERROR)
        return ""

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
                elif "piGenClass" in fileName:
                    result = genPiGenClass(fileName)
                    if result:
                        savedCodeFiles[result] = fileName
                else:
                    printIt(f'Unknown file type: {fileName}', lable.WARN)
            else:
                printIt(fileName, lable.FileNotFound)
        else:
            # Process all files - piClassGC, piDefGC, and piGenClass
            classFiles = genPiPiClass("", verbose)
            defFiles = genPiDefCode("", verbose)
            genClassFiles = processAllPiGenClassFiles(verbose)
            savedCodeFiles.update(classFiles)
            savedCodeFiles.update(defFiles)
            savedCodeFiles.update(genClassFiles)
    except IndexError as e:
        tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
        printIt(f'genCode:\n{tb_str}', lable.ERROR)
        printIt('File name required', lable.IndexError)
    return savedCodeFiles

def processAllPiGenClassFiles(verbose=False) -> dict:
    """Process all piGenClass JSON files in the piGerms directory"""
    savedCodeFiles = {}
    try:
        # Get piGerms directory
        piGermsDir = Path(getKeyItem("piScratchDir", "piGerms"))
        piGenClassDir = piGermsDir / "piGenClass"

        if not piGermsDir.exists():
            printIt(f"piGerms directory not found: {piGermsDir}", lable.WARN)
            printIt("Run 'pigencode germSeed' first to create germ files", lable.INFO)
            return savedCodeFiles

        if not piGenClassDir.exists():
            if verbose:
                printIt(f"piGenClass directory not found: {piGenClassDir}", lable.DEBUG)
                printIt("No piGenClass files to process", lable.DEBUG)
            return savedCodeFiles

        # Find all piGenClass JSON files
        json_files = list(piGenClassDir.glob("piGenClass*.json"))
        if not json_files:
            if verbose:
                printIt("No piGenClass JSON files found", lable.DEBUG)
            return savedCodeFiles

        for json_file in json_files:
            if verbose:
                printIt(f"Processing piGenClass file: {json_file}", lable.DEBUG)

            result = genPiGenClass(str(json_file))
            if result:
                savedCodeFiles[result] = str(json_file)

    except Exception as e:
        printIt(f"Error processing piGenClass files: {e}", lable.ERROR)

    return savedCodeFiles