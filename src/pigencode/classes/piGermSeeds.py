import os, datetime, copy, json, re, traceback
from ..defs.fileIO import readRC, writeRC
from ..defs.piJsonFile import readPiStruc, writePiStruc, readPiDefault, writePiDefault, writePi, PiClassGCFiles, PiDefGCFiles, PiGenClassFiles
from ..defs.piID import getPiMD5, getPiID
from ..defs.logIt import logIt, printIt, germDbug, lable, cStr, color
from .piSeeds import PiSeeds, PiSeedTypes, piSeedTitelSplit
from .piSeedRegistry import pi_seed_registry, register_pi_seed_handler

class piDictLevelError(Exception):
    pass
class piPiStrucNotFound(Exception):
    pass
class piIncorectPiValuePath(Exception):

    pass

class PiGermSeeds():
    def __init__(self, piSeeds: PiSeeds):
        dprint00 = False
        self.seeds = piSeeds
        self.piStructs = {}
        self.piDictSourceTypes = ["piStructs","piDefault", "piStruc"]
        self.piClassGCFiles = PiClassGCFiles()
        self.piDefGCFiles = PiDefGCFiles()
        self.piGenClassFiles = PiGenClassFiles()
        self.classDefCodeDescrtion = {}

        # find and write structures to files
        try:
            lastSeed = False
            while self.seeds.currPi.piType:
                if self.seeds.currPi.piSeedType in PiSeedTypes:
                    if dprint00: printIt(f'Processing piSeed type: {self.seeds.currPi.piSeedType}', lable.DEBUG)
                    self.germinateSeeds()
                    if lastSeed: break # last seed run.
                    if self.seeds.nextPi == None:
                        lastSeed = True # Run the last piSeed
                else:
                    #  need to check if type exists. if so creat this type\
                    piType = ["pi", "piType"]
                    if self.seeds.currPi.piSeedType in piType:
                        self.germinate_pi()
                    else:
                        self.germinate_any()
        except piPiStrucNotFound: raise piPiStrucNotFound(f'{self.seeds.currPi.piTitle} is not defined. Line: {self.seeds.currPi.lineNumber}')
        except piDictLevelError:
            printIt(f'piDictLevelError: {self.seeds.currPi.lineNumber} in {self.seeds.seedFile}',lable.ERROR)
            pass
        except StopIteration:
            printIt("__init__", "StopIteration", lable.DEBUG)
            pass
        except Exception as e:
            if self.seeds.currPi == None: lineNumber = self.seeds.seedCount
            else: lineNumber = self.seeds.currPi.lineNumber
            printIt(f'__init__\nlineNumber: {lineNumber} in {self.seeds.seedFile}',lable.ERROR)
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(tb_str,lable.ERROR)
            exit()
    def germinateSeeds(self):
        dprint00 = False
        try:
            while self.seeds.currPi != None:
                #print(self.seeds.currPi)
                if self.seeds.currPi.piSeedType in PiSeedTypes:
                    if dprint00: print(f'Processing piSeed type: {self.seeds.currPi.piSeedType}')
                    # Use registry pattern instead of exec()
                    if pi_seed_registry.has_handler(self.seeds.currPi.piSeedType):
                        pi_seed_registry.process_seed(self, self.seeds.currPi.piSeedType)
                    else:
                        # Fallback for piSeedTypes that don't have registered handlers
                        # This handles piType and piIndexer which use different logic
                        if self.seeds.currPi.piSeedType == "piType":
                            self.germinate_pi()
                        elif self.seeds.currPi.piSeedType == "piIndexer":
                            # piIndexer might need special handling - for now, skip
                            printIt(f"piIndexer seed type not yet implemented: {self.seeds.currPi.piTitle}", lable.WARN)
                            self.seeds.next()
                        else:
                            printIt(f"Unknown piSeed type: {self.seeds.currPi.piSeedType}", lable.ERROR)
                            self.seeds.next()
                    if self.seeds.nextPi == None: break
                else: break

        except piPiStrucNotFound: raise piPiStrucNotFound(f'{self.seeds.currPi.piTitle} is not defined. Line: {self.seeds.currPi.lineNumber}')
        except piDictLevelError:
            printIt(f'piDictLevelError: {self.seeds.currPi.lineNumber} in {self.seeds.seedFile}',lable.ERROR)
            pass
        except StopIteration:
            printIt("germinateSeeds", "StopIteration", lable.DEBUG)
            pass
        except Exception as e:
            if self.seeds.currPi == None: lineNumber = self.seeds.seedCount
            else: lineNumber = self.seeds.currPi.lineNumber
            printIt(f'germinateSeeds\nlineNumber: {lineNumber} in {self.seeds.seedFile}',lable.ERROR)
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(tb_str,lable.ERROR)
            exit()
    def germinate_pi(self):
        #print(self.seeds.currPi)
        if self.seeds.currPi.piType:
            targetPi = self.getTargetPi(self.seeds.currPi.piType)
            targetPi["piBase"]["piTitle"] = self.seeds.currPi.piTitle
            targetPi["piBase"]["piSD"] = self.seeds.currPi.piSD
            piMD5 = getPiMD5(targetPi["piIndexer"])
            targetPi["piIndexer"]["piMD5"] = piMD5
            targetPi["piID"] = getPiID()
            self.piStructs[self.seeds.currPi.piTitle] = targetPi
            writePi(targetPi, verbose = False)
            self.seeds.next()
    def germinate_any(self):
        if self.seeds.currPi.piType:
            targetPi = self.getTargetPi(self.seeds.currPi.piType)
            if not targetPi:
                printIt(f'pi used for {self.seeds.currPi.piType}: line {self.seeds.currPi.lineNumber}',lable.DEBUG)
                targetPi = self.getTargetPi("pi")
            targetPi["piBase"]["piType"] = self.seeds.currPi.piType
            targetPi["piBase"]["piTitle"] = self.seeds.currPi.piTitle
            targetPi["piBase"]["piSD"] = self.seeds.currPi.piSD
            piMD5 = getPiMD5(targetPi["piIndexer"])
            targetPi["piIndexer"]["piMD5"] = piMD5
            targetPi["piID"] = getPiID()
            self.piStructs[self.seeds.currPi.piTitle] = targetPi
            writePi(targetPi, verbose=False)
            self.seeds.next()
    def germinate_piClassGC(self):
        try:
            while self.seeds.currIndex < self.seeds.seedCount:
                if self.seeds.currPi.piSeedType == PiSeedTypes[3]:
                    lastSeed = False
                    baseType = self.seeds.currPi.piType
                    baseTitle = self.seeds.currPi.piTitle
                    baseLineNumber = int(self.seeds.currPi.lineNumber)
                    targetPi = self.getTargetPi(baseType,source=self.piDictSourceTypes[2])
                    if not targetPi: raise piPiStrucNotFound(f'Need to germinate {baseType} piStruct.')
                    targetPi["piBase"]["piTitle"] = baseTitle
                    targetPi["piBase"]["piSD"] = self.seeds.currPi.piSD
                    piMD5 = getPiMD5(targetPi["piIndexer"])
                    targetPi["piIndexer"]["piMD5"] = piMD5
                    targetPi["piID"] = "TBD"
                    self.piStructs[self.seeds.currPi.piTitle] = targetPi
                    if self.seeds.nextPi == None:
                        self.piClassGCFiles.writePiClassGC(baseType,baseTitle,baseLineNumber,targetPi,False)
                    self.seeds.next()
                else:
                    self.germinateSeeds()
                    self.piClassGCFiles.writePiClassGC(baseType,baseTitle,baseLineNumber, targetPi,False)
                    if lastSeed: break # last seed run.
                    if self.seeds.nextPi == None:
                        lastSeed = True # Run the last piSeed

        except piIncorectPiValuePath:
            printIt(f'{self.seeds.currPi.piTitle}',lable.IncorectPiValuePath)
            print('here00')
            exit()
        except piPiStrucNotFound as e1:
            printIt(f"germinate_piClassGC: '{cStr(str(e1),color.GREEN)}'", lable.DEBUG)
            raise piPiStrucNotFound
        except StopIteration:
            # print("germinate_piClassGC", "StopIteration")
            pass
        except Exception as e:
            printIt(f'germinate_piClassGC\nlineNumber: {self.seeds.currPi.lineNumber} in {self.seeds.seedFile}',lable.ERROR)
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(tb_str,lable.ERROR)
            exit()
    def germinate_piDefGC(self):
        # print('in germinate_piDefGC"',self.seeds.currPi)
        try:
            while self.seeds.currIndex < self.seeds.seedCount:
                if self.seeds.currPi.piSeedType == PiSeedTypes[7]:  # piDefGC is now index 8
                    lastSeed = False
                    baseType = "piDefGC"  # Use piDefGC as the structure type
                    baseTitle = self.seeds.currPi.piTitle
                    baseLineNumber = int(self.seeds.currPi.lineNumber)
                    targetPi = self.getTargetPi(baseType,source=self.piDictSourceTypes[2])
                    targetPi["piBase"]["piTitle"] = baseTitle
                    targetPi["piBase"]["piSD"] = self.seeds.currPi.piSD
                    piMD5 = getPiMD5(targetPi["piIndexer"])
                    targetPi["piIndexer"]["piMD5"] = piMD5
                    targetPi["piID"] = "TBD"
                    self.piStructs[self.seeds.currPi.piTitle] = targetPi
                    if self.seeds.nextPi == None:
                        self.piDefGCFiles.writePiDefGC(baseType,baseTitle,baseLineNumber,targetPi,False)
                    self.seeds.next()
                else:
                    self.germinateSeeds()
                    self.piDefGCFiles.writePiDefGC(baseType,baseTitle,baseLineNumber, targetPi,False)
                    if lastSeed: break # last seed run.
                    if self.seeds.nextPi == None:
                        lastSeed = True # Run the last piSeed

        except piIncorectPiValuePath:
            printIt(f'{self.seeds.currPi.piTitle}',lable.IncorectPiValuePath)
            print('here01')
            exit()
        except piPiStrucNotFound:
            printIt("germinate_piDefGC", lable.DEBUG)
            raise piPiStrucNotFound
        except StopIteration:
            # print("germinate_piDefGC", "StopIteration")
            pass
        except Exception as e:
            printIt(f'germinate_piDefGC\nlineNumber: {self.seeds.currPi.lineNumber} in {self.seeds.seedFile}',lable.ERROR)
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(tb_str,lable.ERROR)
            exit()

    def germinate_piGenClass(self):
        # print('in germinate_piGenClass"',self.seeds.currPi)
        try:
            while self.seeds.currIndex < self.seeds.seedCount:
                if self.seeds.currPi.piSeedType == PiSeedTypes[8]:  # piGenClass is now index 9
                    lastSeed = False
                    baseType = "piGenClass"  # Use piGenClass as the structure type
                    baseTitle = self.seeds.currPi.piTitle
                    baseLineNumber = int(self.seeds.currPi.lineNumber)
                    targetPi = self.getTargetPi(baseType, source=self.piDictSourceTypes[2])
                    targetPi["piBase"]["piTitle"] = baseTitle
                    targetPi["piBase"]["piSD"] = self.seeds.currPi.piSD
                    piMD5 = getPiMD5(targetPi["piIndexer"])
                    targetPi["piIndexer"]["piMD5"] = piMD5
                    targetPi["piID"] = "TBD"
                    self.piStructs[self.seeds.currPi.piTitle] = targetPi
                    if self.seeds.nextPi == None:
                        self.piGenClassFiles.writePiGenClass(baseType, baseTitle, baseLineNumber, targetPi, False)
                    self.seeds.next()
                else:
                    self.germinateSeeds()
                    self.piGenClassFiles.writePiGenClass(baseType, baseTitle, baseLineNumber, targetPi, False)
                    if lastSeed: break # last seed run.
                    if self.seeds.nextPi == None:
                        lastSeed = True # Run the last piSeed

        except piIncorectPiValuePath:
            printIt(f'{self.seeds.currPi.piTitle}', lable.IncorectPiValuePath)
            print('here02')
            exit()
        except piPiStrucNotFound:
            printIt("germinate_piGenClass", lable.DEBUG)
            raise piPiStrucNotFound
        except StopIteration:
            # print("germinate_piGenClass", "StopIteration")
            pass
        except Exception as e:
            printIt(f'germinate_piGenClass\\nlineNumber: {self.seeds.currPi.lineNumber} in {self.seeds.seedFile}',lable.ERROR)
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(tb_str,lable.ERROR)
            exit()

    def germinate_piValueA(self):
        try:
            #piValueA piDates.piBody:piClassGC:imports datetime
            final_key  = ''
            while self.seeds.currIndex < self.seeds.seedCount:
                lastSeed = False
                if self.seeds.currPi.piSeedType == PiSeedTypes[4]:
                    baseTitle = self.seeds.currPi.piTitle
                    baseValue = self.seeds.currPi.piSD
                    piPiTitleKey, piElemKeys = piSeedTitelSplit(baseTitle)
                    #print(piPiTitleKey, piElemKeys)
                    if piPiTitleKey and piElemKeys:
                        if not piPiTitleKey.isnumeric():
                            # print(f'piPiTitleKey: {piPiTitleKey}')
                            targetPi = self.getTargetPi(piPiTitleKey)
                            if targetPi:
                                if not piElemKeys.isnumeric():
                                    aDict = targetPi
                                    piExDefDictKeys = list(filter(None, piElemKeys.split(":")))

                                    # Navigate to the parent container
                                    for piExDefDictKey in piExDefDictKeys[:-1]:
                                        if piExDefDictKey not in aDict:
                                            aDict[piExDefDictKey] = {}
                                        aDict = aDict[piExDefDictKey]
                                        
                                    if len(aDict[piExDefDictKeys[-1]])==1:
                                        # append def description here.
                                        if piExDefDictKeys[-1] in self.classDefCodeDescrtion.keys():
                                            if self.seeds.prevPi.piSD != "@property":
                                                appendStr = ' '*4 + "'"*3 + self.classDefCodeDescrtion[piExDefDictKeys[-1]]+ "'"*3
                                                aDict[piExDefDictKeys[-1]].append(appendStr)
                                    aDict[piExDefDictKeys[-1]].append(baseValue)

                            else: raise Exception
                        else: raise Exception
                    else: raise Exception
                    self.seeds.next()
                    if self.seeds.currPi == None: break
                    if self.seeds.currPi.piSeedType != PiSeedTypes[4]: 
                        if final_key: print('t',final_key)
                        break
                if lastSeed: break # last seed run.
                if self.seeds.nextPi == None:
                    lastSeed = True # Run the last piSeed
        except piIncorectPiValuePath:
            printIt(f'{self.seeds.currPi.piTitle}',lable.IncorectPiValuePath)
            print('here03')
            exit()
        except piPiStrucNotFound:
            printIt("germinate_piValueA", lable.DEBUG)
            raise piPiStrucNotFound
        except StopIteration:
            # print("germinate_piValueA", "StopIteration")
            pass
        except Exception as e:
            printIt(f'germinate_piValueA\nlineNumber: {self.seeds.currPi.lineNumber} in {self.seeds.seedFile}',lable.ERROR)
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(tb_str,lable.ERROR)
            exit()
    def germinate_piValuesSetD(self):
        self.germinate_piValue()
    def germinate_piValue(self):
        dprint00 = False
        try:
            while True: # self.seeds.currIndex < self.seeds.seedCount:
                if self.seeds.currPi.piSeedType == PiSeedTypes[1]:
                    # load structure if not in self.piStructs, populate with defaults,
                    # and save to scratchPis/piDefult folder
                    piTitle = self.seeds.currPi.piTitle
                    if self.seeds.nextPi != None:
                        if self.seeds.nextPi.piType == PiSeedTypes[2]:
                            self.seeds.next()
                            if dprint00: print("debug01", piTitle)
                            self.germinatePiValues(piTitle)
                            if dprint00: print("debug02", piTitle)
                        else:
                            if dprint00: print("debug03", piTitle)
                            targetPi = self.getTargetPi(piTitle)
                            self.piStructs[piTitle] = targetPi
                            self.seeds.next()
                    else:
                        if dprint00: print("debug04", piTitle)
                        targetPi = self.getTargetPi(piTitle)
                        self.piStructs[piTitle] = targetPi
                        self.seeds.next()
                    writePiDefault(piTitle, self.piStructs[piTitle], False)
                else:
                    assert self.seeds.currPi.piType == PiSeedTypes[2]
                    # populate with provided defaults
                    if dprint00: printIt("debug05\n", str(self.seeds.currPi), lable.DEBUG)
                    self.germinatePiValues()
                    #print(self.seeds.currPi)
                    if self.seeds.nextPi == None:
                        break # because last line was processed.
                if self.seeds.nextPi != None:
                    if dprint00: print("debug06:\n",self.seeds.currPi.piType)
                    # print(f'{self.seeds.nextPi.piSeedType} in {PiSeedTypes[1:3]}')
                    if self.seeds.currPi.piSeedType == PiSeedTypes[2]: self.seeds.next()
                    if not self.seeds.currPi.piSeedType in PiSeedTypes[1:3]: break
                else:
                    if dprint00: print("debug07", piTitle)
                    if self.seeds.nextPi == None: break
                    if not self.seeds.currPi.piSeedType in PiSeedTypes[1:3]:
                        break

        except piPiStrucNotFound:
            printIt("germinate_piValue", lable.DEBUG)
            raise piPiStrucNotFound
        # except piPiStrucNotFound:
        #     printIt(f'{self.seeds.currPi.piTitle} is not defined.',lable.ERROR)
        #     exit()
        except piDictLevelError:
            printIt(f'piDictLevelError: {self.seeds.currPi.lineNumber} in {self.seeds.seedFile}',lable.ERROR)
            pass
        except StopIteration:
            # print("germinate_piValue", "StopIteration")
            pass
        except Exception as e:
            if self.seeds.currPi == None: lineNumber = self.seeds.seedCount
            else: lineNumber = self.seeds.currPi.lineNumber
            printIt(f'germinate_piValue\nlineNumber: {lineNumber} in {self.seeds.seedFile}',lable.ERROR)
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(tb_str,lable.ERROR)
            exit()
    def chk4ExDef(self, piValue: str) -> str | dict:
        '''
            Check if there is a external definition of the piValue.
            (PiDefault or PiStruc)

            Returns:
        '''
        rtnValue = piValue
        piExDefPITitle, piExDefValuePiTitle = piSeedTitelSplit(piValue)
        if piExDefPITitle:
            if not piExDefPITitle.isnumeric():
                piExDefTargetPi = self.getTargetPi(piExDefPITitle)
                if piExDefTargetPi:
                    if piExDefValuePiTitle == None or len(piExDefValuePiTitle) == 0:
                        rtnValue = piExDefTargetPi
                    elif not piExDefValuePiTitle.isnumeric():
                        aDict = piExDefTargetPi
                        piExDefDictKeys = list(filter(None, piExDefValuePiTitle.split(":")))
                        for piExDefDictKey in piExDefDictKeys:
                            aDict = aDict[piExDefDictKey]
                        rtnValue = aDict
            else:
                printIt(
                    f'piSeedKey titles can not be numaric: {piExDefPITitle}\npiValue',lable.ERROR)
        return rtnValue
    def getTargetPi(self, piTitle, source = "") -> dict:
        '''
            Check it piTitle has a PiDefault or PiStruc file.
            The cashed self.piStructs dict is checked first.

            Returns:
                Dictionary of targetStruc pi.
        '''
        debug00 = False
        debugTxt = f"{piTitle} from piStructs"
        targetStruc = {}
        if not source:
            try: targetStruc = self.piStructs[piTitle]
            except: pass
            if not targetStruc:  # check if PiDefault
                targetStruc = readPiDefault(piTitle, verbose=False)
                debugTxt = f"{piTitle} from readPiDefault"
            if not targetStruc:  # check if PiStruc
                targetStruc = readPiStruc(piTitle, verbose=False)
                debugTxt = f"{piTitle} from readPiStruc01: {targetStruc}"
        else:
            if source == self.piDictSourceTypes[0]:
                try: targetStruc = self.piStructs[piTitle]
                except: pass
            elif source == self.piDictSourceTypes[1]:
                targetStruc = readPiDefault(piTitle, verbose=False)
                debugTxt = f"{piTitle} from readPiDefault"
            elif source == self.piDictSourceTypes[2]:
                targetStruc = readPiStruc(piTitle, verbose=False)
                debugTxt = f"{piTitle} from readPiStruc02: {targetStruc}"
            else: pass
        if debug00:
            print('DEBUG', debugTxt)
        return targetStruc
    def germinatePiValues(self, piTitle=""):
        try:
            piPiTitleKey, piElemKeys = piSeedTitelSplit(self.seeds.currPi.piTitle)
            if piTitle == "":
                targetPi = self.getTargetPi(piPiTitleKey)
                piTitle = piPiTitleKey
            else:
                if piTitle != piPiTitleKey: raise piIncorectPiValuePath
                targetPi = self.getTargetPi(piTitle)
                #print(f'piTitle: {piTitle}')
            if piElemKeys == None:
                raise piIncorectPiValuePath
            if targetPi:
                while True: # self.seeds.currIndex < self.seeds.seedCount:
                    if self.seeds.currPi.piType != PiSeedTypes[2]: break
                    piPiTitleKey, piElemKeys = piSeedTitelSplit(self.seeds.currPi.piTitle)
                    if piTitle != piPiTitleKey:
                        raise piIncorectPiValuePath
                    structDictKeys = piElemKeys.split(":")
                    #print( piPiTitleKey, piElemKeys)
                    #print(structDictKeys, piTitle)
                    aDict = targetPi
                    lastIndex = -1
                    piValue = self.seeds.currPi.piSD
                    # check to populate with an existing default (ExDef)
                    # print('here01', piValue)
                    piValue = self.chk4ExDef(piValue)
                    if structDictKeys[lastIndex] == "piCode":
                        piValue = eval(self.seeds.currPi.piSD)
                        #piValue = piCodeValue(self.seeds.currPi.piSD)
                        #return eval(self.seeds.currPi.piSD)
                        lastIndex = -2
                    # piDictPrint(targetPi)
                    # print(lastIndex, structDictKeys[:lastIndex], structDictKeys[lastIndex])
                    for piStructDicKey in structDictKeys[:lastIndex]:
                        aDict = aDict[piStructDicKey]
                    #print(structDictKeys)
                    #piDictPrint(targetPi)
                    aDict[structDictKeys[lastIndex]] = piValue
                    # except Exception as e:
                    #     printIt(f'germinatePiValues\nlineNumber: {self.seeds.currPi.lineNumber} in {self.seeds.seedFile}',lable.ERROR)
                    #     tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
                    #     printIt(tb_str,lable.ERROR)
                    #     exit()
                    ##### ****** Best end, same next loop control. !!!!!
                    if self.seeds.nextPi != None:
                        self.seeds.next()
                        if self.seeds.currPi.piSeedType != PiSeedTypes[2]: break
                    else: break # because last line was processed.
                self.piStructs[piTitle] = targetPi

        except piIncorectPiValuePath:
            printIt(f'germinatePiValues: {self.seeds.currPi.piTitle}, line {self.seeds.currPi.lineNumber}',lable.IncorectPiValuePath)
            print('here04')
            exit()
        except piPiStrucNotFound:
            printIt("germinate_piValues:", self.seeds.currPi.piTitle, lable.DEBUG)
            raise piPiStrucNotFound
        except StopIteration:
            # print("germinatePiValues", "StopIteration")
            pass
        except Exception as e:
            printIt(f'germinatePiValues\nlineNumber: {self.seeds.currPi.lineNumber} in {self.seeds.seedFile}',lable.ERROR)
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(tb_str,lable.ERROR)
            exit()

    def germinate_piStruct(self):
        dprint00 = False
        dprint01 = False
        #print(self.seeds.currPi.piTitle)
        try:
            while self.seeds.currIndex < self.seeds.seedCount:
                processStruct = True
                if dprint01: print(self.seeds.currPi)
                if self.seeds.currPi.piType != PiSeedTypes[0]:
                    if dprint00: printIt("test01",lable.DEBUG)
                    processStruct = False
                elif self.seeds.nextPi == None:
                    if dprint00: printIt("test02",lable.DEBUG)
                    processStruct = False
                elif self.seeds.nextPi.piType == PiSeedTypes[0]:
                    if dprint00: printIt("test03",lable.DEBUG)
                    processStruct = False
                elif self.seeds.nextPi.piSeedType != PiSeedTypes[0]: processStruct = False
                if processStruct: # Start of structure found
                    baseName = self.seeds.currPi.piTitle
                    baseType = self.seeds.currPi.piType
                    self.currPiStruct = self.piStructs[baseName] = {}
                    self.seeds.next()
                    self.germinateSeedStructure()
                    # piStructsList = list(self.piStructs[baseName].keys())
                    # if len(piStructsList) > 0:
                    # if baseName == list(self.piStructs[baseName].keys())[0]:
                    #     self.piStructs[baseName] = self.piStructs[baseName][baseName]
                    # print("B",baseName)
                    # print("K",list(self.piStructs[baseName].keys())[0])

                    #print(baseType)
                    #fix clone copy to base name dict element.
                    _ = writePiStruc(baseName, self.piStructs[baseName], False)
                else:
                    # print(self.seeds.currPi.piSeedType, self.seeds.currPi.piSeedKeyType)
                    if self.seeds.currPi.piSeedType == PiSeedTypes[0] and \
                        self.seeds.currPi.piSeedKeyType == "A":
                        piPiTitleKey, _ = piSeedTitelSplit(self.seeds.currPi.piTitle)
                        baseName = piPiTitleKey
                        self.currPiStruct = self.piStructs[baseName]
                        self.germinateSeedStructure()
                    else:
                        break
            if self.seeds.nextPi != None:
                #print("here in germinate_piStruct")
                #print(f'{self.seeds.currPi.piType} == {PiSeedTypes[0]}')
                if self.seeds.currPi.piSeedType == PiSeedTypes[0]: self.seeds.next()

        except piDictLevelError:
            printIt(f'piDictLevelError: {self.seeds.currPi.lineNumber} in {self.seeds.seedFile}',lable.ERROR)
            pass
        except StopIteration:
            #printIt(f'StopIteration: {self.seeds.currPi.lineNumber} in {self.seeds.seedFile}',lable.ERROR)
            raise StopIteration
        except Exception as e:
            printIt(f'germinate_piStruct\nlineNumber: {self.seeds.currPi.lineNumber} in {self.seeds.seedFile}',lable.ERROR)
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(tb_str,lable.ERROR)
            exit()
    def germinateSeedStructure(self):
        dprint00 = False
        dprint02 = False
        try:
            baseDepth = 0
            baseName = self.seeds.currPi.piSD
            currDepth = self.seeds.currPi.piSeedKeyDepth
            if currDepth != baseDepth: raise piDictLevelError
            while self.seeds.currIndex < self.seeds.seedCount:
                if self.seeds.currPi.piType == PiSeedTypes[0]: break
                if self.seeds.currPi.piSeedType != PiSeedTypes[0]: break
                # PiSeedTypeVarTypes = ["I", "S", "F", "D", "L", "C", "A"]
                if self.seeds.currPi.piSeedKeyType == "B":
                    if dprint00: print('addB', self.seeds.currPi.piTitle)
                    self.currPiStruct[self.seeds.currPi.piTitle] = False
                elif self.seeds.currPi.piSeedKeyType == "I":
                    self.currPiStruct[self.seeds.currPi.piTitle] = 0
                elif self.seeds.currPi.piSeedKeyType == "S":
                    if dprint00: print('addS', self.seeds.currPi.piTitle)
                    self.currPiStruct[self.seeds.currPi.piTitle] = ""
                elif self.seeds.currPi.piSeedKeyType == "F":
                    self.currPiStruct[self.seeds.currPi.piTitle] = 0.0
                elif self.seeds.currPi.piSeedKeyType == "D":
                    if dprint02: germDbug("S", self.seeds.currPi, self.seeds.nextPi)
                    aDict = self.currPiStruct[self.seeds.currPi.piTitle] = {}
                    if self.seeds.nextPi == None: break
                    if self.seeds.currPi.piSeedKeyDepth == self.seeds.nextPi.piSeedKeyDepth - 1:
                        self.germinateDict(aDict, currDepth)
                elif self.seeds.currPi.piSeedKeyType == "L":
                    if dprint02: germDbug("S", self.seeds.currPi, self.seeds.nextPi)
                    aList = self.currPiStruct[self.seeds.currPi.piTitle] = []
                    if self.seeds.nextPi == None: break
                    if self.seeds.currPi.piSeedKeyDepth == self.seeds.nextPi.piSeedKeyDepth - 1:
                        self.germinateList(aList, currDepth)
                elif self.seeds.currPi.piSeedKeyType == "C":
                    if dprint02: germDbug("S", self.seeds.currPi, self.seeds.nextPi)
                    self.cloneDict(self.currPiStruct)
                    # if list(self.currPiStruct.keys())[0] == baseName:
                    #     print("inT", baseName, list(self.currPiStruct.keys())[0])
                    #     self.currPiStruct = self.currPiStruct[self.seeds.currPi.piSD]
                elif self.seeds.currPi.piSeedKeyType == "A":
                    if dprint02: germDbug("S", self.seeds.currPi, self.seeds.nextPi)
                    piPiTitleKey, piElemKeys = piSeedTitelSplit(self.seeds.currPi.piTitle)
                    try:
                        targetPi = self.getTargetPi(piPiTitleKey)
                        aDict = targetPi
                        piElemKeys = piElemKeys.split(":")
                        #piDictPrint(aDict)
                        #print(piElemKeys)
                        for piStruct in piElemKeys:
                            aDict = aDict[piStruct]
                        self.appendDict(aDict, currDepth)
                        #piDictPrint(targetPi)
                    except Exception as e:
                        printIt(f'germinateSeedStructure\nlineNumber: {self.seeds.currPi.lineNumber} in {self.seeds.seedFile}',lable.ERROR)
                        tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
                        printIt(tb_str,lable.ERROR)
                        exit()
                else:
                    raise piPiStrucNotFound
                if self.seeds.nextPi != None:
                    if self.seeds.nextPi.piSeedType == PiSeedTypes[0]: self.seeds.next()
                    else: break
                else: break
        except piDictLevelError:
            pass
        except piPiStrucNotFound:
            printIt(f'germinateSeedStructure - {self.seeds.currPi.piTitle} is not a defined structure.')
            exit()
        except StopIteration:
            pass
        except Exception as e:
            printIt(f'germinateSeedStructure\nlineNumber: {self.seeds.currPi.lineNumber} in {self.seeds.seedFile}',lable.ERROR)
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(tb_str,lable.ERROR)
            exit()
    def germinateDict(self, theDict, baseDepth):
        dprint02 = False
        try:
            self.seeds.next()
            currDepth = baseDepth + 1
            if self.seeds.currPi.piSeedKeyDepth == currDepth:
                while self.seeds.currIndex < self.seeds.seedCount:
                    if self.seeds.currPi.piType == PiSeedTypes[0]: break
                    # PiSeedTypeVarTypes = ["I", "S", "F", "D", "L", "C", "A"]
                    if self.seeds.currPi.piSeedKeyType == "B":
                        theDict[self.seeds.currPi.piTitle] = False
                    elif self.seeds.currPi.piSeedKeyType == "I":
                        theDict[self.seeds.currPi.piTitle] = 0
                    elif self.seeds.currPi.piSeedKeyType == "S":
                        if self.seeds.currPi.piSeedKeyDepth < currDepth: break
                        theDict[self.seeds.currPi.piTitle] = ""
                    elif self.seeds.currPi.piSeedKeyType == "F":
                        theDict[self.seeds.currPi.piTitle] = 0.0
                    elif self.seeds.currPi.piSeedKeyType == "D":
                        if dprint02: germDbug("D", self.seeds.currPi, self.seeds.nextPi)
                        aDict = theDict[self.seeds.currPi.piTitle] = {}
                        if self.seeds.nextPi != None:
                            if self.seeds.currPi.piSeedKeyDepth == self.seeds.nextPi.piSeedKeyDepth - 1:
                                self.germinateDict(aDict, currDepth)
                    elif self.seeds.currPi.piSeedKeyType == "L":
                        if dprint02: germDbug("D", self.seeds.currPi, self.seeds.nextPi)
                        aList = theDict[self.seeds.currPi.piTitle] = []
                        if self.seeds.nextPi != None:
                            if self.seeds.currPi.piSeedKeyDepth == self.seeds.nextPi.piSeedKeyDepth - 1:
                                self.germinateList(aList, currDepth)
                    elif self.seeds.currPi.piSeedKeyType == "C":
                        if dprint02: germDbug("D", self.seeds.currPi, self.seeds.nextPi)
                        self.cloneDict(theDict)
                    elif self.seeds.currPi.piSeedKeyType == "A":
                        if dprint02: germDbug("D", self.seeds.currPi, self.seeds.nextPi)
                        aDict = {}
                        theDict[self.seeds.currPi.piTitle] = self.appendDict(aDict, currDepth)
                    else:
                        raise piPiStrucNotFound
                    # print("D", currDepth, baseDepth, self.seeds.currPi.piTitle)
                    # print("D", self.seeds.currPi.piSeedKeyDepth, self.seeds.currPi.piTitle)
                    if self.seeds.nextPi != None:
                        if self.seeds.nextPi.piSeedKeyDepth < currDepth: break
                        #print(self.seeds.currPi.piTitle)
                        if self.seeds.nextPi.piSeedType == PiSeedTypes[0]: self.seeds.next()
                        else: break
                    else: break
            else: raise piDictLevelError

        except piDictLevelError:
            pass
        except piPiStrucNotFound:
            printIt(f'germinateDict - {self.seeds.currPi.piTitle} is not a defined structure.')
            exit()
        except StopIteration:
            pass
        except Exception as e:
            printIt(f'germinateDict\nlineNumber: {self.seeds.currPi.lineNumber} in {self.seeds.seedFile}',lable.ERROR)
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(tb_str,lable.ERROR)
            exit()
    def germinateList(self, theList, baseDepth):
        dprint02 = False
        try:
            #print("germinateList","check first next")
            self.seeds.next()
            currDepth = baseDepth + 1
            if self.seeds.currPi.piSeedKeyDepth == currDepth:
                while self.seeds.currIndex < self.seeds.seedCount:
                    if self.seeds.currPi.piType == PiSeedTypes[0]: break
                    # PiSeedTypeVarTypes = ["I", "S", "F", "D", "L", "C", "A"]
                    if self.seeds.currPi.piSeedKeyType == "B":
                        theList.append(False)
                    elif self.seeds.currPi.piSeedKeyType == "I":
                        theList.append(0)
                    elif self.seeds.currPi.piSeedKeyType == "S":
                        theList.append("")
                    elif self.seeds.currPi.piSeedKeyType == "F":
                        theList.append(0.0)
                    elif self.seeds.currPi.piSeedKeyType == "D":
                        if dprint02: germDbug("L", self.seeds.currPi, self.seeds.nextPi)
                        aDict = {}
                        if self.seeds.nextPi != None:
                            if self.seeds.currPi.piSeedKeyDepth == self.seeds.nextPi.piSeedKeyDepth - 1:
                                self.germinateDict(aDict, currDepth)
                        theList.append(aDict)
                    elif self.seeds.currPi.piSeedKeyType == "L":
                        if dprint02: germDbug("L", self.seeds.currPi, self.seeds.nextPi)
                        aList = []
                        if self.seeds.nextPi != None:
                            if self.seeds.currPi.piSeedKeyDepth == self.seeds.nextPi.piSeedKeyDepth - 1:
                                self.germinateList(aList, currDepth)
                        theList.append(aList)
                    elif self.seeds.currPi.piSeedKeyType == "C":
                        if dprint02: germDbug("L", self.seeds.currPi, self.seeds.nextPi)
                        printIt(f'Case when list containes a cloned dictionary?',lable.DEBUG)
                        exit()
                        #theList.append(self.cloneDict(aList))
                    elif self.seeds.currPi.piSeedKeyType == "A":
                        if dprint02: germDbug("L", self.seeds.currPi, self.seeds.nextPi)
                        aDict = {}
                        theList.append(self.appendDict(aDict, currDepth))
                    else:
                        raise piPiStrucNotFound
                    if self.seeds.nextPi != None:
                        if self.seeds.nextPi.piSeedKeyDepth < currDepth: break
                        # print(self.seeds.currPi.piTitle)
                        if self.seeds.nextPi.piSeedType == PiSeedTypes[0]: self.seeds.next()
                        else: break
                    else: break
            else: raise piDictLevelError

        except piDictLevelError:
            pass
        except piPiStrucNotFound:
            printIt(f'{self.seeds.currPi.piTitle} is not a defined structure.')
            exit()
        except StopIteration:
            pass
        except Exception as e:
            printIt(f'germinateList\nlineNumber: {self.seeds.currPi.lineNumber} in {self.seeds.seedFile}',lable.ERROR)
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(tb_str,lable.ERROR)
            exit()
    def appendDict(self, theDict, baseDepth):
        dprint02 = False
        try:
            self.seeds.next()
            currDepth = baseDepth + 1
            if self.seeds.currPi.piSeedKeyDepth == currDepth:
                while self.seeds.currIndex < self.seeds.seedCount:
                    if self.seeds.currPi.piType == PiSeedTypes[0]: break
                    # PiSeedTypeVarTypes = ["I", "S", "F", "D", "L", "C", "A"]
                    if self.seeds.currPi.piSeedKeyType == "B":
                        theDict[self.seeds.currPi.piTitle] = False
                    elif self.seeds.currPi.piSeedKeyType == "I":
                        theDict[self.seeds.currPi.piTitle] = 0
                    elif self.seeds.currPi.piSeedKeyType == "S":
                        theDict[self.seeds.currPi.piTitle] = ""
                    elif self.seeds.currPi.piSeedKeyType == "F":
                        theDict[self.seeds.currPi.piTitle] = 0.0
                    elif self.seeds.currPi.piSeedKeyType == "D":
                        if dprint02: germDbug("A", self.seeds.currPi, self.seeds.nextPi)
                        aDict = theDict[self.seeds.currPi.piTitle] = {}
                        if self.seeds.nextPi != None:
                            if self.seeds.currPi.piSeedKeyDepth == self.seeds.nextPi.piSeedKeyDepth - 1:
                                self.germinateDict(aDict, currDepth)
                    elif self.seeds.currPi.piSeedKeyType == "L":
                        if dprint02: germDbug("A", self.seeds.currPi, self.seeds.nextPi)
                        aList = theDict[self.seeds.currPi.piTitle] = []
                        if not self.classDefCodeDescrtion:
                            piExDefDictKeys = list(filter(None, self.seeds.prevPi.piTitle.split(":")))
                            if piExDefDictKeys[-1] == 'classDefCode':
                                self.classDefCodeDescrtion[self.seeds.currPi.piTitle] = self.seeds.currPi.piSD
                        else:
                            if self.seeds.currPi.lineNumber == self.seeds.prevPi.lineNumber+1:
                                self.classDefCodeDescrtion[self.seeds.currPi.piTitle] = self.seeds.currPi.piSD
                        if self.seeds.nextPi != None:
                            if self.seeds.currPi.piSeedKeyDepth == self.seeds.nextPi.piSeedKeyDepth - 1:
                                self.germinateList(aList, currDepth)
                    elif self.seeds.currPi.piSeedKeyType == "C":
                        if dprint02: germDbug("A", self.seeds.currPi, self.seeds.nextPi)
                        if self.seeds.currPi.piSD[-1] == ".":
                            aDictName = self.seeds.currPi.piSD[:-1]
                        else:
                            aDictName = self.seeds.currPi.piSD
                        # print(aDictName, theDict)
                        aDict = theDict[aDictName] = {}
                        self.cloneDict(aDict)
                        # piDictPrint(theDict)
                    elif self.seeds.currPi.piSeedKeyType == "A":
                        if dprint02: germDbug("A", self.seeds.currPi, self.seeds.nextPi)
                        aDict = {}
                        theDict[self.seeds.currPi.piTitle] = self.appendDict(aDict, currDepth)
                    else:
                        raise piPiStrucNotFound
                    # print("A", currDepth, baseDepth, self.seeds.currPi.piTitle)
                    # print("A", self.seeds.currPi.piSeedKeyDepth, self.seeds.currPi.piTitle)
                    if self.seeds.nextPi == None: break
                    if self.seeds.nextPi.piSeedKeyDepth < currDepth: break
                    self.seeds.next()
            else: raise piDictLevelError

        except piDictLevelError:
            pass
        except piPiStrucNotFound:
            printIt(f'{self.seeds.currPi.piTitle} is not a defined structure.')
            exit()
        except StopIteration:
            pass
        except Exception as e:
            printIt(f'appendDict\nlineNumber: {self.seeds.currPi.lineNumber} in {self.seeds.seedFile}',lable.ERROR)
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(tb_str,lable.ERROR)
            exit()
    def cloneDict(self, theDict: dict):
        cloneFromDisk = readPiStruc(self.seeds.currPi.piTitle)
        if cloneFromDisk:
            dictClone = copy.deepcopy(cloneFromDisk)
            if self.seeds.currPi.piSD[-1] == ".":
                for aKey in cloneFromDisk.keys():
                    theDict[aKey] = copy.deepcopy(cloneFromDisk[aKey])
                # print(f'theDict: {theDict}')
            else:
                theDict[self.seeds.currPi.piSD] = dictClone
        else: raise piPiStrucNotFound
        # print(theDict)
##### Public Functions
def germinateSeeds(fileName) -> PiGermSeeds:
    piSeeds = PiSeeds(fileName)
    seedPis = PiGermSeeds(piSeeds)
    return seedPis


# Register all piSeed type handlers with the registry
# This replaces the exec() pattern with a cleaner registry approach

# @register_pi_seed_handler("piGermDir")
# def handle_piScratchDir(germ_seeds_instance):
#     """Handler for piGermDir seed type"""
#     germ_seeds_instance.germinate_piScratchDir()

@register_pi_seed_handler("piStruct")
def handle_piStruct(germ_seeds_instance):
    """Handler for piStruct seed type"""
    germ_seeds_instance.germinate_piStruct()

@register_pi_seed_handler("piValuesSetD")
def handle_piValuesSetD(germ_seeds_instance):
    """Handler for piValuesSetD seed type"""
    germ_seeds_instance.germinate_piValuesSetD()

@register_pi_seed_handler("piValue")
def handle_piValue(germ_seeds_instance):
    """Handler for piValue seed type"""
    germ_seeds_instance.germinate_piValue()

@register_pi_seed_handler("piClassGC")
def handle_piClassGC(germ_seeds_instance):
    """Handler for piClassGC seed type"""
    germ_seeds_instance.germinate_piClassGC()

@register_pi_seed_handler("piValueA")
def handle_piValueA(germ_seeds_instance):
    """Handler for piValueA seed type"""
    germ_seeds_instance.germinate_piValueA()

@register_pi_seed_handler("piDefGC")
def handle_piDefGC(germ_seeds_instance):
    """Handler for piDefGC seed type"""
    germ_seeds_instance.germinate_piDefGC()

@register_pi_seed_handler("piGenClass")
def handle_piGenClass(germ_seeds_instance):
    """Handler for piGenClass seed type"""
    germ_seeds_instance.germinate_piGenClass()

# Note: piType and piIndexer handlers are not registered here because
# their corresponding germinate methods don't exist in the class.
# They are handled by the fallback logic in the main processing loop.


# struc                   self.cloneDict(self.currPiStruct)
# dict                       self.cloneDict(theDict)
# list                       theList.append(self.cloneDict(aList))
# append                     self.cloneDict(theDict)
