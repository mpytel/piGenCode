# don't import PiContoller because PiClasses my not be present
import os
from pi.defs.logIt import printIt, label, cStr, color
from pi.defs.piFileIO import piAPIURL
from pi.defs.piTouch import isPiID
from pi.defs.piUtil import logedIn, piDupPiTitleZfill, piJoinStr
from pi.classes.piPiPackage import PiPiPackage
from fastapi import status
import requests as req
from json import dumps
from pi.classes.optSwitches import readOptSwitches
from pi.defs.piPrintCLI import getPiListStr, getPiIndexerStr, currPiStr, dependentPiStr, currIndexerStr
from pi.defs.plural2Single import plural2Single
from pi.classes.piCurrentIndexer import PiCurrentIndexer
from pi.piClasses.piWordSeek import PiWordSeek

debugOff = label.ABORTPRT # ^(.*)(printIt)(.*debugOff\)), $1# printIt$2
debugOn = label.DEBUG
debugSet = debugOff
# debugSet = debugOn

class PiTerminalSwitchboard():
    def __init__(self, packName: str, theCmd: str, theArgs: list) -> None:
        self.piTypeProcessed = True
        self.theCmd = theCmd
        self.theArgs = theArgs
        self.piPiPackage = PiPiPackage(packName)
        if not self.piPiPackage.packageOK: exit()
        # whant to remove this managment of piCurrentIndexer
        self.piPiPackageSystem = self.piPiPackage.piPackageSys
        self.piCurrentIndexer: PiCurrentIndexer = self.piPiPackage.piCurrentIndexer
        self.piPiClasses = self.piCurrentIndexer.piPiClasses
        self.piIndexerTypes = self.piPiClasses.piIndexerTypes
        self.piIndexerSTypes = self.piPiClasses.piIndexerSTypes
        self.piTypeNameClasses = self.piPiClasses.piTypeNameClasses
        self.piWordSeek = PiWordSeek()
        self.piAuthHeader = logedIn(self.piCurrentIndexer)
        if not self.piAuthHeader: exit()
        # here is were the current user is set via cert.
        #print('PiTerminalSwitchboard.__init__()',self.theCmd)
        if self.theCmd == "list":
            self.listPiType(self.theCmd) # use piApi to list pis for the req piType
        elif self.theCmd == "chkLogin":
            if logedIn(self.piCurrentIndexer):
                printIt(f'loged in as {self.piCurrentIndexer.User.piBase.piTitle}')
            else:
                printIt(f'Not loged in.')
        elif self.theCmd in self.piIndexerSTypes: # >pi pyTypes in cmd-line
            self.listPiType(self.theCmd)
        elif self.theCmd in self.piIndexerTypes: # >pi pyType in cmd-line
            self.setCurrPiType(self.theCmd)
        elif self.theCmd == "show":
            self.piShow() # list specific pis json without going though piAPI
        else:
            self.piTopic()
    def piShow(self):
        ''' used to list raw pi from file '''
        outStr = ""
        showFields = []
        aFieldValue = None
        if self.theArgs:
            for arg in self.theArgs:
                if isPiID(arg):
                    aPi, _ = self.piCurrentIndexer.piFromLink(arg)
                    # print(aPi.piID)
                    if aPi:
                        piJson = aPi.json()
                        if showFields:
                            fieldIndex = 0
                            while fieldIndex < len(showFields):
                                field = showFields[fieldIndex]
                                aFieldValue = getFieldValueFromJson(piJson, field)
                                if aFieldValue:
                                    if type(aFieldValue) == dict:
                                        print(dumps(aFieldValue,indent=2))
                                    else:
                                        print(f'{field}: {aFieldValue}')
                                else:
                                    printIt(f'{field} is not a pi field',label.WARN)
                                fieldIndex += 1
                        else:
                            print(f'{arg}\n', aPi)
                elif arg in self.piIndexerTypes:
                    indexItem = 'pi' + arg[0].upper() + arg[1:]
                    indexUUID4 = eval(f'self.piCurrentIndexer.currIndexer.{indexItem}')
                    aPi, _ = self.piCurrentIndexer.piFromLink(indexUUID4)
                    print(f'Current {arg}:\n', aPi)
                elif arg in self.piTypeNameClasses:
                    showFields.append(arg)
                    if len(self.theArgs) == 1:
                        self.piShowTopic(showFields)
                else:
                    showFields.append(arg)
                    if len(showFields) == 2:
                        self.piShowTopic(showFields)
    def piShowTopic(self, showFields: list):
        if showFields[0] in self.piTypeNameClasses:
            theJson = self.listPiType(showFields[0],True)
            if len(self.theArgs) == 2:
                if showFields[1].isnumeric():
                    theIndex = int(showFields[1])
                    if len(theJson["pis"]) >= theIndex:
                        printIt(f'theJson:\n{dumps(theJson["pis"][theIndex-1],indent=2)}',label.DEBUG)
                        return
                    else:
                        currIndexerTitels = theJson['currIndexer']
                        prtStr = f'Only {len(theJson["pis"])} {showFields[0]} in:\n'
                        prtStr += '\n' + currIndexerStr(currIndexerTitels)
                        print(prtStr)
                        return
                else:
                    findStr = showFields[1]
                    noOutput= True
                    for aPi in theJson["pis"]:
                        chkStr:str = aPi["piBase"]["piType"] + " " + \
                                 aPi["piBase"]["piTitle"] + " " + \
                                 aPi["piBase"]["piSD"]
                        if chkStr.find(findStr)>0:
                            noOutput = False
                            printIt(f'{showFields[0]} containing {showFields[1]}:\n{dumps(aPi,indent=2)}',label.INFO)
                    if noOutput:
                            printIt(f'No {showFields[0]} containing {showFields[1]} found',label.WARN)

            else:
                print(f'Listing of {showFields[0]}')
                printIt(f'theJson:\n{dumps(theJson["pis"],indent=2)}',label.INFO)
    def list(self):
        #printIt('in piTerminalSwitchboard.list()',label.DEBUG)
        theURL = f'{piAPIURL}/pis/list'
        if self.theArgs:
            piIndex = 1
            for arg in self.theArgs:
                if isPiID(arg):
                    theURL = f'{piAPIURL}/pis/{arg}'
                    res = req.get(theURL,headers=self.piAuthHeader)
                    if res.status_code == status.HTTP_200_OK:
                        theJson =  res.json()
                        # outStr += "\n" + dumps(theJson[0]["pi"],indent=2)
                        prtStr = getPiListStr(theJson[0])
                        pIDPaddingStr = f'{" "*(4-len(str(piIndex)))}'
                        print(f'{pIDPaddingStr}{color.YELLOW}{piIndex}:{color.RESET} {prtStr}')
                    # if res.status_code == status.HTTP_403_FORBIDDEN:
                    #     self.login()
                    #     theURL  = f'{piAPIURL}/pis/login'
                    else:
                        printIt(res.status_code, label.ERROR)
                elif arg in self.piIndexerSTypes:
                    self.listPiType(arg)
                piIndex += 1
        else:
            res = req.get(theURL,headers=self.piAuthHeader)
            if res.status_code == status.HTTP_200_OK:
                theJson =  res.json()
                piIndex = 1
                for pi in theJson['pis']:
                    prtStr = getPiListStr(pi)
                    pIDPaddingStr = f'{" "*(4-len(str(piIndex)))}'
                    print(f'{pIDPaddingStr}{color.YELLOW}{piIndex}:{color.RESET} {prtStr}')
                    piIndex += 1
            else:
                printIt(res.status_code, label.ERROR)
    def listPiType(self, piType:str, boolRtnJson:bool=False):
    # list current user's types when called from cli in plurl form
    # piType in self.piIndexerSTypes.
        #debugSet = debugOn
        theURL = f'{piAPIURL}/pis/{piType}'
        printIt(f'in listPiType', debugSet)
        printIt(f'GET URL: {theURL}', debugSet)
        printIt(f'self.piCurrentIndexer: {self.piCurrentIndexer.currIndexerAsTitels()}', debugSet)
        #debugSet = debugOff
        printIt(f'self.piAuthHeader: {self.piAuthHeader}', debugSet)
        res = req.get(theURL,headers=self.piAuthHeader)
        theJson = None
        if res.status_code == 200:
            self.piTypeProcessed = True
            theJson =  res.json()
            emDash = '—'
            if len(theJson["pis"]) > 0:
                if not boolRtnJson:
                    if len(self.theArgs) > 0:
                        try:
                            argsStr: str = self.theArgs[0]
                            formatIndex = int(argsStr)
                            if formatIndex == 1:
                                self.prtPiBase1line(theJson["pis"])
                            elif formatIndex == 2:
                                self.prtPiBase2line(theJson["pis"])
                        except:
                            if argsStr.lower() == 'md':
                                self.prtPiBaseMD(theJson["pis"])
                            elif argsStr.lower() == 'piid':
                                self.prtPiBaseAndPiIDs(theJson["pis"])
                    else:
                        os.system('clear')
                        self.prtPis(theJson["pis"])
            else:
                indexerTitels = self.piCurrentIndexer.currIndexerAsTitels().json()
                piIndexerStr = getPiIndexerStr(indexerTitels, 0, False)
                printIt(piIndexerStr,label.INFO)
        elif res.status_code == status.HTTP_403_FORBIDDEN:
            printIt(f'piAPI not availabel error {res.status_code}',label.WARN)
        elif res.status_code == status.HTTP_203_NON_AUTHORITATIVE_INFORMATION:
            printIt(f'piAPI error {res.status_code}',label.WARN)
        else:
            printIt(f'piAPI error {res.status_code}',label.FAIL)
        return theJson
    def prtPiBaseAndPiIDs(self, thePis):
        piIndex = 1
        prtStr = ''
        for pi in thePis:
            piBase = pi['piBase']
            if piIndex == 1:
                prtStr = f'### {piBase["piType"].capitalize()}s ({pi["piTypeID"]})\n'
            prtStr += f'{piIndex}) {cStr(piBase["piTitle"],color.GREEN)}: {pi["piID"]}\n'
            piIndex += 1
        print(prtStr)
    def prtPiBase1line(self, thePis):
        piIndex = 0
        prtStr = ''
        for pi in thePis:
            # if piIndex == 0:
            #     prtStr += '\n' + currIndexerStr(currIndexerTitels)
            #     print(prtStr)
            piBase = pi['piBase']
            prtStr = cStr(piBase['piType'],color.YELLOW)
            prtStr += ': '+cStr(piBase['piTitle'],color.GREEN)
            prtStr += ', '+cStr(piBase['piSD'],color.CYAN)
            pIDPaddingStr = f'{" "*(4-len(str(piIndex)))}'
            print(f'{pIDPaddingStr}{color.YELLOW}{piIndex} - {color.RESET} {prtStr}')
            piIndex += 1
            if piIndex > 10: break
    def prtPiBase2line(self, thePis):
        prtStr = ''
        piIndex = 0
        lineStr = ''
        piCount = len(thePis)
        for pi in thePis:
            piBase = pi['piBase']
            if not prtStr:
                prtStr = printIt(f"prtPiBase2line {piCount} - {piBase['piType']}\n",label.INFO,asStr=True)
            lineStr = piBase['piTitle']
            lineStr += ', '+piBase['piSD']
            # prtStr += f'{piIndex}) {lineStr}\n'
            prtStr += f'{lineStr}\n'
            piIndex += 1
            # if piIndex > 10: break
        if prtStr: print(prtStr[:-1])
    def prtPiBaseMD(self, thePis):
        piIndex = 1
        prtStr = ''
        for pi in thePis:
            piBase = pi['piBase']
            if piIndex == 1:
                prtStr = f'### {piBase["piType"].capitalize()}s\n'
            prtStr += f'{piIndex}) **{piBase["piTitle"]}**: {piBase["piSD"]}\n'
            piIndex += 1
        print(prtStr)
            # if piIndex > 10: break
    def prtPis(self, thePis):
        currIndexerTitels = self.piCurrentIndexer.currIndexerAsTitels().json()
        piIndex = 0
        prtStr = ''
        indexerTitels = ''
        for pi in thePis:
            # if piIndex == -1:
            #     prtStr += '\n' + currIndexerStr(currIndexerTitels)
            #     print(prtStr)
            prtStr = dependentPiStr(pi)
            if not indexerTitels: indexerTitels = self.piCurrentIndexer.indexerAsTitels(pi['piIndexer']).json()
            #prtStr += '\n' # + getPiIndexerStr(indexerTitels)
            pIDPaddingStr = f'{" "*(4-len(str(piIndex)))}'
            print(f'{pIDPaddingStr}{color.YELLOW}{piIndex}:{color.RESET} {prtStr}')
            piIndex += 1
            #if piIndex > 10: break
        print(getPiIndexerStr(indexerTitels))

    def getPiDictForTitle(self, theJson, theTitle:str) -> dict:
        rtnJson: dict = None
        for aJson in theJson:
            if aJson["pi"]["piBase"]["piTitle"] == theTitle:
                rtnJson = aJson["pi"]
                break
        return rtnJson
    def setCurrPiType(self, piType:str):
    # for cli:
    # change current type requested or specifed though this function
        print('In piTerminalSwitchboard.setCurrPiType')
        if self.theArgs:
            #print(self.theArgs)
            if len(self.theArgs) == 2:
                # standard entry with type, titel and sd provided
                piTitle = self.theArgs[0]
                piSD = self.theArgs[1]
                # fix string when it has escape charaters
                if '\\' in list(piTitle):
                    piTitle = piTitle.encode().decode('unicode-escape')
                if '\\' in list(piSD):
                    piSD = piSD.encode().decode('unicode-escape')
                # check spelling
                printIt('spellChk00',label.WARN)
                theTokens = [piType,piTitle,piSD]
                piType = self.piWordSeek.checkTokens(theTokens[0])
                piTitle = self.piWordSeek.checkTokens(theTokens[1])
                piSD = self.piWordSeek.checkTokens(theTokens[2])
                piBase = {"piType": str(piType),
                            "piTitle": str(piTitle),
                            "piSD": str(piSD)}
                printIt(f'setCurrPiType: {piType}',debugSet)
                if piType == 'user':
                    exec("from ..piClasses.piUserProfile import getPiUserProfile")
                    print('\n')
                    print()
                    piUserProfile = eval(f'getPiUserProfile("{piTitle}", 1)')
                    piBase["piUserProfile"] = piUserProfile.__dict__
                    res = req.post(f'{piAPIURL}/pi/user', json=piBase, headers=self.piAuthHeader)
                    if res.status_code == status.HTTP_403_FORBIDDEN:
                        printIt(f'piAPI not availabel error {res.status_code}',label.WARN)
                else:
                    res = req.post(f'{piAPIURL}/pi', json=piBase, headers=self.piAuthHeader)
                if res.status_code == status.HTTP_201_CREATED:
                    # the current pi was set in piAPIServer
                    theJson =  res.json()
                    printIt(f'Current {piType} set to {piTitle}.',label.INFO)
                elif res.status_code == status.HTTP_203_NON_AUTHORITATIVE_INFORMATION:
                    printIt(f'Not authorized to create {piType}',label.WARN)
                elif res.status_code == status.HTTP_302_FOUND:
                    printIt(f'This {piType} exists.',label.WARN)
                else:
                    printIt(f'piAPI error (setCurrPiType): {res.status_code}',label.FAIL)
            elif len(self.theArgs) == 3 and type(self.theArgs[0])==int:
                ''' EXPERIMENTAL use not working. Attempt to use switch flag to edit pi data'''
                printIt('Place holder for catching three argument entries',label.DEBUG)
                optSwitches = readOptSwitches()["switcheFlags"]
                if optSwitches["c"]:
                    print(self.theArgs[1])
                    if self.theArgs[1] in  ["realm", "domain", "subject"]:
                        thePiJson: dict = self.listPiType(piType+'s',True)
                        thePi = thePiJson["pis"][self.theArgs[0]-1]["pi"]
                        thePiIndexJson: dict = self.listPiType(self.theArgs[1]+'s',True)
                        thePiIndex = self.getPiDictForTitle(thePiIndexJson["pis"],self.theArgs[2])
                        self.piPiPackageSystem.setPiIdexerType(thePi["piID"], piType, thePiIndex["piID"])
                else:
                    print('Enter "pi +c" on the command line to make pis editable.')
            elif len(self.theArgs) == 1:
                '''List the pi associated with the single argument pi piType'''
                piTitle: str = self.theArgs[0]
                if piType == "user":
                    userDict:dict = self.piCurrentIndexer.rootUser.users
                    if userDict:
                        if piTitle in userDict.keys():
                            self.piCurrentIndexer.setCurrentIndexer(self.piIndexerTypes[0],piTitle)
                        else:
                            printIt(f'{piTitle} is not a {piType} piTerminalSwitchboard.setCurrPiType',label.WARN)
                    else:
                        printIt(f'users are not set up correctly',label.ERROR)
                elif piType in self.piIndexerTypes[1:4]:
                    if piTitle.isnumeric():
                        piTypeIndex = self.piIndexerTypes.index(piType) - 1
                        if piTypeIndex < 0: piTypeIndex = 0
                        currPiTitles = self.piCurrentIndexer.getCurrPiTypeList(self.piIndexerTypes[piTypeIndex])
                        # printIt(str(currPiTitles),label.DEBUG)
                        titleFromList = currPiTitles[int(piTitle)-1]
                        theTokens = [titleFromList]
                    else:
                        theTokens = [piTitle]
                    piTitle = theTokens[0]
                    piSD = ''
                    piBase = {"piType": str(piType),
                                "piTitle": str(piTitle),
                                "piSD": str(piSD)}
                    res = req.post(f'{piAPIURL}/pi', json=piBase, headers=self.piAuthHeader)
                    if res.status_code == status.HTTP_202_ACCEPTED:
                        typeIndex = self.piPiClasses.piIndexerTypes.index(piType) + 1
                        if piType == self.piPiClasses.piIndexerTypes[3]:
                            piSType = 'topics'
                        else:
                            piSType = self.piPiClasses.piIndexerSTypes[typeIndex]
                        #printIt(f'Type: {piType} set to {piTitle} with the following {piSType}.',label.INFO)
                        prtStr = 'List of ' + cStr(f'{piTitle} {piSType}',color.GREEN) + cStr(f':',color.RESET)
                        printIt(prtStr,label.INFO)
                        # list subtypes here
                        self.piCurrentIndexer = PiCurrentIndexer()
                        currPiTitles = self.piCurrentIndexer.getCurrPiTypeList(piType)
                        PiTitleIndex = 1
                        for aPiTitle in currPiTitles:
                            print(PiTitleIndex,aPiTitle)
                            PiTitleIndex += 1
                        thePiIndexerTitels = self.piCurrentIndexer.currIndexerAsTitels()
                        print(getPiIndexerStr(thePiIndexerTitels.json(),None,0))

                        #print(currPiStr(theJson))
                    # currentIndexer = self.piCurrentIndexer.currIndexer
                    # print(f'switch: {piType}, {piTitle}\n', currentIndexer)
                    elif res.status_code == status.HTTP_304_NOT_MODIFIED:
                        chkNotModifiedStr = self.getNotModifiedStr(piBase)
                        if chkNotModifiedStr: printIt(self.getNotModifiedStr(piBase),label.WARN)
                        else: printIt(f'{piType} is set to {piTitle}',label.INFO)
                    else:
                        print('json=',res)
        else:
            if piType == "user":
                if 'rootuser' in self.piPiPackageSystem.piCurrentIndexer.User.piBody.piUserProfile.grants:
                    self.piPiPackageSystem.piCurrentIndexer.bldInitStdCurrUser()
                else:
                    printIt('Login as root to create new users.',label.WARN)
            elif piType in self.piIndexerTypes:
                piBase = self.piPiPackageSystem.getCurrTypeItemPiBase(piType)
                if piBase:
                    self.theCmd = piBase.piType
                    self.theArgs = [piBase.piTitle, piBase.piSD]
                    self.piTopic()
    def getNotModifiedStr(self, piBase: dict) -> str:
        print('piBase',piBase)
        print(self.piCurrentIndexer.User.realm)
        piType = piBase['piType']
        piTitle = piBase['piTitle']
        piSD = piBase['piSD']
        rtnStr = ''
        if piType in self.piIndexerTypes: piIndexerTypeIndex = self.piIndexerTypes.index(piType)
        else: piIndexerTypeIndex = len(self.piIndexerTypes)
        if piIndexerTypeIndex >= 0:
            if piTitle != self.piCurrentIndexer.User.user: rtnStr = f'{piTitle} is not a {piType}'
            else: rtnStr = ''
        if piIndexerTypeIndex >= 1:
            if piTitle != self.piCurrentIndexer.User.realm: rtnStr += f' of {self.piCurrentIndexer.User.user}'
            else: rtnStr = ''
        if piIndexerTypeIndex >= 2:
            if piTitle != self.piCurrentIndexer.Realm.domain: rtnStr += f'/{self.piCurrentIndexer.User.realm}'
            else: rtnStr = ''
        if piIndexerTypeIndex >= 3:
            if piTitle != self.piCurrentIndexer.Domain.subject: rtnStr += f'/{self.piCurrentIndexer.Realm.domain}'
            else: rtnStr = ''
        if piIndexerTypeIndex >= 4:
            if piTitle != self.piCurrentIndexer.Subject.type: rtnStr += f'/{self.piCurrentIndexer.Domain.subject}'
            else: rtnStr = ''
        if piIndexerTypeIndex >= 5:
            rtnStr += f'/{self.piCurrentIndexer.subject.type}'
        if rtnStr: rtnStr += '.'
        return rtnStr
    def type(self): # creates or sets current type
        theURL = f'{piAPIURL}type'
        printIt(f'def type(self) not used yet.\ncommand: {self.theCmd}\narguments: {self.theArgs}',label.WARN)
    def pi(self): # creates or sets current pi
        theURL = f'{piAPIURL}pi'
        printIt(f'def pi(self) not used yet.\ncommand: {self.theCmd}\narguments: {self.theArgs}',label.WARN)
    def piTopic(self): # creates a new piTopic of specifed type
        '''Depending the number of arguments this function will
            O - treats the command as a type or types to list type.
                singuler: list the current pi of this type
                pluerl: list all of that type of the current user
            1 - look for an integer and use positiove values as the
                number to list and negative values to make current
            2 - Treat cmd self.theCmd as piType and\n
                self.theArgs[:2] as piTitle, piSD.
            '''
        # > pi topic 'cli pi creatation' 'quickest input for creating new pis with new type.
        argCount = len(self.theArgs)
        print('In piTerminalSwitchboard.piTopic argCount =',argCount)
        # print(cStr('self.theArgs:',color.CYAN),self.theArgs)
        if argCount == 0:
            chkCmdTypeName = self.theCmd
            chkTypeName = plural2Single(chkCmdTypeName,self.piPiClasses)
            print('chkTypeName', chkTypeName)
            if chkTypeName:
                self.listPiType(chkCmdTypeName)
            else:
                printIt(f'{cStr(chkCmdTypeName,color.UNDERLINE)} command not found.',label.WARN)
        elif argCount == 1:
            theJson = self.listPiType(self.theCmd, boolRtnJson=False)
            if len(theJson['pis']) == 0:
                self.piTypeProcessed = False
            # print(dumps(theJson,indent=2))
        elif argCount == 2:
            # check spelling because we are going to add a new pi
            theTokens = [self.theCmd,self.theArgs[0],self.theArgs[1]]
            piType = self.piWordSeek.checkTokens(theTokens[0])
            piTitle = self.piWordSeek.checkTokens(theTokens[1])
            if theTokens[2]: piSD = self.piWordSeek.checkTokens(theTokens[2])
            else: piSD = ''
            piBase = {"piType": piType,
                      "piTitle": piTitle,
                      "piSD": piSD}
            res = req.post(f'{piAPIURL}/pi', json=piBase, headers=self.piAuthHeader)
            if res.status_code == status.HTTP_201_CREATED:
                theJson =  res.json()
                if not theJson:
                    printIt(f'This {piType} exists.',label.WARN)
                else:
                    printIt(f'Current {piType} set to {piTitle}.',label.INFO)
            elif res.status_code == status.HTTP_202_ACCEPTED:
                typeIndex = self.piPiClasses.piIndexerTypes.index(piType) + 1
                if piType == self.piPiClasses.piIndexerTypes[3]:
                    piSType = 'topic'
                else:
                    piSType = self.piPiClasses.piIndexerSTypes[typeIndex]
                #printIt(f'Type: {piType} set to {piTitle} with the following {piSType}.',label.INFO)
                prtStr = cStr(f'{piSType}',color.GREEN) + cStr(f' for ',color.RESET) + cStr(f'{piTitle}',color.BLUE) + cStr(f':',color.RESET)
                printIt(prtStr,label.INFO)
                # list subtypes here
                self.piCurrentIndexer = PiCurrentIndexer()
                currPiTitles = self.piCurrentIndexer.getCurrPiTypeList(piType)
                PiTitleIndex = 1
                for aPiTitle in currPiTitles:
                    print(PiTitleIndex,aPiTitle)
                    PiTitleIndex += 1
                thePiIndexerTitels = self.piCurrentIndexer.currIndexerAsTitels()
                print(getPiIndexerStr(thePiIndexerTitels.json(),None,0))
            elif res.status_code == status.HTTP_302_FOUND:
                printIt(f'in piType HTTP_302_FOUND', debugSet)
                dupTitle = piDupPiTitleZfill(piType,piTitle,self.piCurrentIndexer)
                # print('dupTitle',dupTitle)
                if dupTitle:
                    piBase["piTitle"] = dupTitle
                    res = req.post(f'{piAPIURL}/pi', json=piBase, headers=self.piAuthHeader)
                    if res.status_code == status.HTTP_201_CREATED:
                        theJson =  res.json()
                        if not theJson:
                            printIt(f'This {piType} exists.',label.WARN)
                        else:
                            printIt(f'Current {piType} set to {dupTitle}.',label.INFO)
                else:
                    printIt(f'{piType} {cStr(piTitle,color.UNDERLINE)} exists.',label.WARN)
            elif res.status_code == status.HTTP_304_NOT_MODIFIED:
                    chkNotModifiedStr = self.getNotModifiedStr(piBase)
                    if chkNotModifiedStr: printIt(self.getNotModifiedStr(piBase),label.WARN)
                    else: printIt(f'{piType} is set to {piTitle}',label.INFO)
            elif res.status_code == status.HTTP_403_FORBIDDEN:
                printIt(f'piAPI not availabel {res.status_code}',label.WARN)
            elif res.status_code == status.HTTP_203_NON_AUTHORITATIVE_INFORMATION:
                printIt(f'Not authorized to create {piType}',label.WARN)
            else:
                printIt(f'piAPI error: {res.status_code}',label.FAIL)
        elif argCount == 3:
            # #*** THIS IS WHERE GENERIC TYPES ARE CREATED
            # check spelling
            # There seems to never be that case when argCount == 3
            printIt(f'There seems to never be that case when argCount == 3 in PiTerminalSwitchboard.piTopic()', label.ERROR)
            print('spellChk02')
            theTokens = [self.theCmd,self.theArgs[0],self.theArgs[1]]
            piType = self.piWordSeek.checkTokens(theTokens[0])
            piTitle = self.piWordSeek.checkTokens(theTokens[1])
            piSD = self.piWordSeek.checkTokens(theTokens[2])
            # printIt(f'This will create {piTitle} as a {piType}:\nSD: {piSD}')
            print('not calling via API')
            newPi = self.piCurrentIndexer.reqNewPi(piType, piTitle, piSD)
            if newPi:
                printIt(f'{newPi.piBase.piTitle} was created as {newPi.piID}',label.INFO)
            else:
                printIt(f'{piTitle} was not created.', label.WARN)
        else:
            printIt('How did I get here (piTerminalSwitchboard)?')
            printIt('missing item piType, piTitle, piSD?')
def getFieldValueFromJson(theJson: dict, theField: str) -> (dict|str):
    rtnValue = None
    if theField in theJson.keys():
        rtnValue = theJson[theField]
    else:
        for aFiled, aValue in theJson.items():
            if aFiled == theField:
                rtnValue = aValue
                break
            else:
                if type(aValue) == dict:
                    rtnValue = getFieldValueFromJson(aValue, theField)
                    if rtnValue: break
    return rtnValue

