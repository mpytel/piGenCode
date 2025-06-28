# piGenCode
Generate python classes from germinated piSeed files. Each line of a piSeed file is a piSeed, a instance of a piBase dictionary.

piSeeds are tuples of information used to genrate python code. We are devloping an obsolete idea that uses three strings called a pi to represent a particle of Pertinent Information, composed of a type, titel and short discription (SD). This is the piBase dictionary containg three elememts, piType, piTitle, piSD as keys. When representing a piSeed these elements represnet a piSeedType, piSeedKey, and the piSeedValue.

Each piSeedType is an instruction for ***piGenCode*** to prefor different operations. Currently there are 8 piSeedTypes:
- piScratchDir
- piStruct
- piValuesSetD
- piValue
- piClassGC
- piValueA
- piType
- piIndexer

#### List of piSeeds to geneate the piBase json structure
```
piScratchDir /Users/primwind/proj/dev/pi/pi/scratchPis 'locattion for storing pis befor piIndexing and piID directory tree encritipn is present.'
# piStruct.piBase
piStruct piBase 'Defines a data structure for pi.\nA dictionary for holding pi topic information.'
piStructS00 piType 'piStruct child of pi storing a string type name of the pi.'
piStructS00 piTitle 'piStruct child of pi storing a string title of the pi.'
piStructS00 piSD pi
piValuesSetD piBase 'defines default piBase values from a piBase structure'
piValue piBase.piType pi
piValue piBase.piTitle pi
piValue piBase.piSD 'Smallest particle of Pertinent Information, uesed to define base pis.'
```

For exmple the following set the loca

piGen is used to genrate piValuesSetD, piStruct, and piClassGC objects from piSeed files. A piSeed file containes lines of piSeeds, each designated as one of 8 piSeedTypes:
- piScratchDir
- piStruct
- piValuesSetD
- piValue
- piClassGC
- piValueA
- piType
- piIndexer

piSeeds are tuplles of three strings called a pi. Each pi are small particle of Pertinent Information, composed of a type, titel and short discription (SD). The base form is a piBase dictionary using piType, piTitle, piSD as keys." Each piSeedType is an instruction for ***piGen*** to prefor different operations.
For exmple the following set the location of the piScratchDir where piStruct, piClassGC and piValuesSetD pi files.
`
pi piScratchDir /Users/primwind/proj/dev/pi/pi/scratchPis 'directory for storing piStruct, piClassGC and piValuesSetD pi files.'
`
***piGen*** reads piSeed000.pi text files in sequance to write the piStruct, piClassGC and piValuesSetD pi files requested in each piSeed text file.
```
pi germSeed /Users/primwind/proj/dev/pi/pi/piSeeds/piSeed_piWord.pi
pi genCode /Users/primwind/proj/dev/pi/pi/scratchPis/piClassGC/piClassGC018_piWord.json
```