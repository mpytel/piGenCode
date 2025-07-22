from pathlib import Path
from pigencode.defs.fileIO import getKeyItem, setKeyItem, piGCDirs

# def getSeedPath() -> Path:
#     seedPath = Path(getKeyItem(piGCDirs[0]))
#     if not seedPath.exists():
#         seedPath.mkdir(parents=True, exist_ok=True)
#         writeBasePiSeeds(seedPath)
#     return seedPath


def getSeedPath() -> Path:
    """Get the piSeeds directory path"""
    # seedDirName = "piSeeds"
    seedPath = Path(getKeyItem(piGCDirs[0]))
    if seedPath.is_dir():
        writeBasePiSeeds(seedPath)
    else:
        seedPath.mkdir(parents=True, exist_ok=True)
        writeBasePiSeeds(seedPath)
    return seedPath

    # # Check current directory
    # cwd = Path.cwd()
    # if cwd.name == seedDirName:
    #     seedPath = cwd
    # else:
    #     cwdDirs = [str(p.name) for p in cwd.iterdir() if p.is_dir()]
    #     if seedDirName in cwdDirs:
    #         seedPath = cwd.joinpath(seedDirName)

    # if seedPath and seedPath.is_dir():
    #     print(f'debug {str(seedPath)}')
    #     print(f'debug {seedPath.relative_to(Path.cwd())}')
    #     setKeyItem("piSeedsDir", str(seedPath.relative_to(Path.cwd())))
    #     return seedPath
    # else:
    #     seedPath.mkdir(parents=True, exist_ok=True)
    #     writeBasePiSeeds(seedPath)

    return seedPath


def writeBasePiSeeds(piSeedPath: Path):

    piSeeds = {
        "piStruct_piProlog": """# piStruct_piProlog
piStruct piProlog 'Defines a data structure for piProlog.\\nA dictionary defining the structure of the piProlog added to the top of all piPi. piStructS00(title, version, author, copyright).'
piStructS00 title 'A string value for storing the name of any system used to process pis.'
piStructS00 version 'A string value for storing th e version of the system used to process pis.'
piStructS00 author 'A string value for storing the author of the system used to process pis.'
piStructS00 copyright 'A string value for storing the copyright holder and year of the system used to process pis.'
piValuesSetD piProlog 'defines default prolog values from a piProlog structure'
piValue piProlog.title pi
piValue piProlog.version '0.0.1'
piValue piProlog.author 'martin@pidev.com'
piValue piProlog.copyright '2023 Pi Development'
""",
        "piStruct_piBase": """# piStruct_piBase
piStruct piBase 'Defines a data structure for pi.\\nA dictionary for holding pi topic information.'
piStructS00 piType 'piStruct child of pi storing a string type name of the pi.'
piStructS00 piTitle 'piStruct child of pi storing a string title of the pi.'
piStructS00 piSD pi
piValuesSetD piBase 'defines default piBase values from a piBase structure'
piValue piBase.piType pi
piValue piBase.piTitle pi
piValue piBase.piSD 'Smallest particle of Pertinent Information, uesed tdefine base pis.'
""",
        "piStruct_piTouch": """# piStruct_piTouch
piStruct piTouch 'Defines a data structure for piTouch.\\nA dictionary of pi datetime stamp.'
piStructS00 piCreationDate 'piStruct child of piTouch storing datetime stamp when a pi is created.'
piStructS00 piModificationDate 'piStruct child of piTouch storing datetime stamp when a pi is modified.'
piStructS00 piTouchDate 'piStruct child of piTouch storing datetime stamp when a pi is read.'
piStructI00 piTouches 'Incrimenting integer counting the number of times the pi is tuched'
""",
        "piStruct_piIndexer": """# piStruct_piIndexer
piStruct piIndexer 'Defines a data structure for piIndexer.\\nA dictionary for indexing pis, 1) user, 2) realm, 3) domain, 4) subject and 5) type used to catalog all pis.'
piStructS00 piMD5 'piStruct child of piIndexer storing a unique piIndexer signiture = md5(piUser+piRealm+piDomain+piSubject),'
piStructS00 piUser 'piStruct child of piIndexer storing a designated user of the pi.'
piStructS00 piRealm 'piStruct child of piIndexer storing a designated realm (public, private, secret) of the pi.'
piStructS00 piDomain 'piStruct child of piIndexer storing a designated domain of the pi.'
piStructS00 piSubject 'piStruct child of piIndexer storing a designated subject of the pi.'
piValuesSetD piIndexer 'defines default piBase values from a piBase structure'
piValue piIndexer.piUser 'TBD'
piValue piIndexer.piRealm 'TBD'
piValue piIndexer.piDomain 'TBD'
piValue piIndexer.piSubject 'TBD'
""",
        "piStruct_piInfluence": """# piStruct_piInfluence
piStruct piInfluence 'Defines a data structure for piInfluence.\\nA dictionary of lists that map object used fot organizing pis,'
piStructL00 piPrecedent 'piStruct child of piInfluence storing a list of piID strings corresponding to the symbolic links pointing to pis that preceded the current pi.'
piStructL00 piDescendent 'piStruct child of piInfluence storing a list of piID strings corresponding to the symbolic links pointing to pis that sucdeed the current pi.'
""",
        "piStruct_pi": """# piStruct_pi
piStruct pi 'Define a pi data structure.\\nA dictionary for holding pi topic information.'
piStructC00 piProlog piProlog
piStructC00 piBase piBase
piStructS00 piID 'An unique string pi signiture = md5(piType+piTitle+piSD+piMD5).'
piStructC00 piTouch piTouch
piStructC00 piIndexer piIndexer
piStructC00 piInfluence piInfluence
piStructD00 piBody 'A dictionary for storing any additional information.'
piValuesSetD pi 'defines default pi from a pi structure'
piValue pi.piProlog piProlog.
piValue pi.piBase piBase.
piValue pi.piIndexer piIndexer.
""",
        "piStruct_argument": """# piStruct_argument
piStruct argument 'Argument definition dict.'
piStructS00 type 'Defines the arument data type (str|int|dict|list)'
piStructS00 value 'Defines the arument defalut value. Starts as an str, will be programicly cast to the specified data type.'
""",
        "piStruct_fromImports": """# piStruct_fromImports
piStruct fromImports 'Defines a data structure for fromImports.'
piStructS00 from 'Defines the from package name defalut as a python form path string.'
piStructS00 import 'Defines the import object names as a comma dilinated string of object names.'
""",
        "piStruct_piClassGC": """# piStruct_piClassGC
piStruct piClassGC 'Data structure for generating code from a piSeed text file.'
piStructC00 pi piClassGC.
piStructA00 piClassGC.piBody 'Add elements to saved structure dict. At specifes the depth of this dict.'
piStructD01 piClassGC 'Defines a data structure for code generation.\\nA dictionary defining the structure needed to gemnerate a python class file.'
piStructS02 fileDirectory 'Directory path for the output Python file (relative or absolute). Uses piClassGCDir from RC if not specified.'
piStructS02 fileName 'Name of the output Python file (without .py extension).'
piStructL02 headers 'List of header strings.'
piStructL02 imports 'List of objects to import.'
piStructD02 fromImports 'List of objects to import.'
piStructL02 fromPiClasses 'List of objects to import.'
piStructL02 rawFromImports 'List of objects to import.'
piStructD02 globals 'Defines class file global veriables. Zero or more are specifed by changing <globalName> to desired variable name.'
piStructS02 piClassName 'Name of the class using caplitalized piType name (PiTypeName).\\nThe class will be cammel case piType name (class piTypeName():).'
piStructL02 inheritance 'List of classes to inherent.'
piStructD02 initArguments 'Defines dict of class parameters.'
piStructL02 classComment 'list of class comment lines.'
piStructL02 preSuperInitCode 'Replace the standard __init__ code with lines of code for supper listed as seperate list items.'
piStructL02 postSuperInitCode 'Add  __init__ code lines after the supper coed of code listed as seperate list items.'
piStructL02 initAppendCode 'Append the standard __init__ code with lines of code listed as seperate list items.'
piStructS02 genProps 'Flag to generate class properies for each class argument.'
piStructL02 strCode 'Replace the standard __str__ code with lines of code listed as seperate list items.'
piStructL02 jsonCode 'Replace the piGen json code with lines of code listed as seperate list items.'
piStructD02 classDefCode 'Zero or more def function are defned in this dict.'
piStructL02 globalCode 'lines of code to append after the lines of code defining the piClass.\\nEach line of code is a seperate list items.'
""",
        "piStruct_piDefGC": """# piStruct_piDefGC
piStruct piDefGC 'Data structure for generating Python function definition files from piSeed text files.'
piStructC00 pi piDefGC.
piStructA00 piDefGC.piBody 'Add elements to saved structure dict. At specifies the depth of this dict.'
piStructD01 piDefGC 'Defines a data structure for function definition file generation.\\nA dictionary defining the structure needed to generate a python file containing function definitions.'
piStructL02 headers 'List of header strings for the file.'
piStructL02 imports 'List of objects to import.'
piStructD02 fromImports 'Dictionary of objects to import from specific modules.'
piStructL02 fromPiClasses 'List of objects to import from piClasses.'
piStructL02 rawFromImports 'List of raw import statements.'
piStructD02 globals 'Defines file global variables. Zero or more are specified by changing <globalName> to desired variable name.'
piStructS02 fileDirectory 'Directory path for the output Python file (relative or absolute). Uses piDefGCDir from RC if not specified.'
piStructS02 fileName 'Name of the output Python file (without .py extension).'
piStructL02 fileComment 'List of file-level comment lines.'
piStructD02 functionDefs 'Dictionary of function definitions. Each key is a function name containing list of code lines.'
piStructL02 constants 'List of module-level constants definitions.'
piStructD02 mlConstants 'List of module-level constants defined on multiple Lines.'
piStructL02 globalCode 'Lines of code to append at the end of the file.\\nEach line of code is a separate list item.'
piValuesSetD piDefGC 'defines default piDefGC values from a piDefGC structure'
piValue piDefGC.piProlog pi.piProlog
piValue piDefGC.piBase:piType piDefGC
piValue piDefGC.piBase:piTitle piDefGC
piValue piDefGC.piBase:piSD 'Structure for generating Python function definition files.'
piValue piDefGC.piBody:piDefGC:headers []
piValue piDefGC.piBody:piDefGC:imports []
piValue piDefGC.piBody:piDefGC:fromImports {}
piValue piDefGC.piBody:piDefGC:fromPiClasses []
piValue piDefGC.piBody:piDefGC:rawFromImports []
piValue piDefGC.piBody:piDefGC:globals {}
piValue piDefGC.piBody:piDefGC:fileName 'functions'
piValue piDefGC.piBody:piDefGC:fileComment []
piValue piDefGC.piBody:piDefGC:functionDefs {}
piValue piDefGC.piBody:piDefGC:constants []
piValue piDefGC.piBody:piDefGC:mlConstants {}
piValue piDefGC.piBody:piDefGC:globalCode []
""",
        "piStruct_piGenClass": """# piStruct_piGenClass
piStruct piGenClass 'Data structure for generating multiple classes from a single piSeed file, similar to piDefGC for functions.'
piStructC00 pi piGenClass.
piStructA00 piGenClass.piBody 'Add elements to saved structure dict for class generation.'
piStructD01 piGenClass 'Defines a data structure for multi-class code generation.\\nA dictionary defining the structure needed to generate a Python file with multiple classes.'
piStructS02 fileDirectory 'Directory path for the output Python file (relative or absolute). Uses piGenClassDir from RC if not specified.'
piStructS02 fileName 'Name of the output Python file (without .py extension).'
piStructL02 headers 'List of header comment strings.'
piStructL02 imports 'List of modules to import (import module).'
piStructD02 fromImports 'Dictionary of from imports (from module import items).'
piStructL02 constants 'List of module-level constants and variables.'
piStructD02 mlConstants 'List of module-level constants defined on multiple Lines.'
piStructD02 classDefs 'Dictionary of class definitions, each containing complete class code.'
piStructL02 globalCode 'List of global code lines at the end of the file.'
"""
}

    fileID = 0
    for key, value in piSeeds.items():
        fileName = f'piSeed{str(fileID).zfill(3)}_{key}.pi'
        filePath = piSeedPath.joinpath(fileName)
        if not filePath.exists():
            with open(filePath, 'w') as fw:
                fw.write(value)
        fileID += 1
