import sys
from pathlib import Path
# import traceback
from json import dumps
from re import findall, compile as reCompile
from datetime import datetime
from time import time
from pi.defs.piFileIO import getKeyItem, delKey, setKeyItem, getPisPath
from pi.defs.logIt import printIt, lable, logIt, cStr, color
from pi.defs.piLogger import piLogger, piPiLogStr
from pi.defs.piTouch import isPiID
#from pi.defs.plural2Single import plural2Single
from pi.piClasses.piPi import PiPi
from pi.piClasses.piBase import PiBase
from pi.piClasses.piIndexer import PiIndexer
from pi.piClasses.piUser import PiUser, PiUserBody, buildUser, baseRealms
from pi.piClasses.piUserProfile import PiUserProfile, getPiUserProfile, getInput
from pi.piClasses.piPiClasses import PiPiClasses
from pi.piClasses.piRealm import PiRealm, PiRealmBody
from pi.piClasses.piDomain import PiDomain, PiDomainBody
from pi.piClasses.piSubject import PiSubject, PiTopicBody
from pi.piClasses.piIDIndex import PiIDIndex
from pi.piClasses.piTopic import PiTopic, PiTopicBody
from pi.piClasses.piToken import PiToken
from pi.piClasses.piTrie import PiTrie, PiTrieBody, PiTrieNode
from pi.piClasses.piWord import PiWord
from pi.piClasses.piIDIndexUpdates import PiIDIndexUpdates
# from pi.piWords.piWords import Words
import readline, os
#from time import time
readline.parse_and_bind('tab: compleat')
readline.parse_and_bind('set editing-mode vi')

# self.piIndexerTypes = ["user", "realm", "domain", "subject"]
baseRealmsList = list(baseRealms.keys())
curserUpLineCode = "\033[1A"
untitled = 'untitled'
globalStoragePiTypes = ['PiWord']
globalStorageContainers = ['word']

debugOff = lable.ABORTPRT # ^(.*)(printIt)(.*debugSet\)), $1# printIt$2
debugOn = lable.DEBUG
debugSet = debugOff
# debugSet = debugOn

class piUserNotFound(Exception):
    def __init__(self) -> None:
        super(Exception, self).__init__()
        message = ""
        for i in range(len(self.args)):
            message += self.args[i] +'\n'
        if not message: message = 'User Not Found'
        else: self.message =  message[:-1]
    @property
    def message(self) -> str:
        return self.__message
    @message.setter
    def message(self, message: str):
        self.__message = message

class PiCurrentIndexer(PiIndexer):
    def __init__(self) -> None:
        super(PiCurrentIndexer, self).__init__()
        self.pisPath: Path = getPisPath()
        self.piPiClasses = PiPiClasses()
        # self.words = Words()
        self.piIndexerTypes = self.piPiClasses.piIndexerTypes
        self.rootUser: PiUser = None
        self.User: PiUser = None
        self._establishedRootUser()
        self._establishedCurrentIndexerPis()
        self.piIDIndexUpdates = PiIDIndexUpdates(self)
        if not self.rootUser:
            print('no root user')
            exit()
        if not self.User:
            print('no curr user')
            exit()
# /Users/primwind/pis/be2160ca-4a88-4df6-977f-1e898a03c948/f22cb647-8fa0-4683-b18e-74fbb25e46c9/eb2a2f9a-cee7-446e-a4c7-41f199444c3b/4f730707-a5e1-402f-9dd4-374756f5d5d0/05b98d40-10ce-4f61-abbb-b6b8d6b65800/05b98d40-10ce-4f61-abbb-b6b8d6b65800.json
    @property
    def currIndexer(self) -> PiIndexer:
        rtnPiIndexer = PiIndexer()
        rtnPiIndexer.piUser = self.User.piID
        rtnPiIndexer.piRealm = self.Realm.piID
        rtnPiIndexer.piDomain = self.Domain.piID
        rtnPiIndexer.piSubject = self.Subject.piID
        rtnPiIndexer.setPiMD5()
        return rtnPiIndexer
    @property
    def getUserToken(self) -> str:
        userToken = self.User.piBody.piUserProfile.userToken
        return userToken
    def _establishedRootUser(self) -> bool:
        goodRoot = False
        piRootUserPathStr = getKeyItem('rootUser')
        if piRootUserPathStr:
            piRootUserPath = Path(piRootUserPathStr)
            if not piRootUserPath.is_file():
                delKey('rootUser')
                piRootUserPathStr = ""
        if piRootUserPathStr: # see it a root user exists in pis dir
            aRootUser: PiUser = PiUser(fileName=piRootUserPathStr)
            if aRootUser: # this is checked in piUser object
                self.rootUser = aRootUser
                # check to see if current list of user is viable
                self._checkUsersInRoot()
            else:
                self.rootUser = None
        else:
            rootPiUser = None
            self.pisPath = Path(getKeyItem('pisDir'))
            if self.pisPath.is_dir():
                self.rootUser = None
                for aPath in self.pisPath.iterdir():
                    if aPath.is_dir() and isPiID(aPath.name):
                        file_list = [f for f in aPath.glob('**/*') if f.is_file()]
                        # printIt('possible error here becase userfile used befor defined',lable.ERROR)
                        userfile = [f for f in file_list if f.name == f'{aPath.name}.json']
                        if userfile: userfile = userfile[0]
                        if userfile: chkPiUser = PiUser(fileName=userfile)
                        else: chkPiUser = None
                        if chkPiUser:
                            haveRoot = 'rootuser' in chkPiUser.piBody.piUserProfile.grants
                            if haveRoot:
                                rootPiUser = chkPiUser
                                break
                if rootPiUser:
                    self.rootUser = rootPiUser
                    setKeyItem('rootUser', str(userfile))
                    printIt(f'Root user set to 0: {self.rootUser.piBase.piTitle}',lable.INFO)
                    logIt(f'Root user set to: {self.rootUser.piBase.piTitle}',lable.INFO)
            if not self.rootUser: # no pis dir exist becuse piRootUser was not set
                # therfor creat new user
                print(cStr(cStr('Create root user',cVal=color.UNDERLINE),cVal=color.YELLOW))
                defultName = 'root'
                picklistStr = f'Root user name ({defultName}): '
                #' oot user  Root user short discription (root user):'
                newUserPiTitle = input(picklistStr)
                if not newUserPiTitle: newUserPiTitle = defultName
                picklistStr = "Root user short discription (root user): "
                print(f'{" "*80}{curserUpLineCode}', end='\x1b[1K\r')
                newUserPiSD = input(picklistStr)
                if not newUserPiSD: newUserPiSD = "root user"
                print('\n')
                print()
                if debugSet == debugOn: curserUpLines = 0
                else: curserUpLines = 1
                piUserProfile: PiUserProfile = getPiUserProfile(newUserPiTitle,curserUpLines=curserUpLines)
                piUserProfile.grants = ['rootuser']
                self.rootUser = buildUser(newUserPiTitle, newUserPiSD, piUserProfile, True)
        if self.rootUser:
            # print('goodRoot = True  ')
            goodRoot = True
        else:
            printIt('piRootUser not set.',lable.ERROR)
        return goodRoot
    def _checkUsersInRoot(self):
        currUserName = self.rootUser.piBody.user
        brokenLinkes = []
        chk4BrokenLinkes = False
        saveRoot = False
        for aUserName, aUserFileName in self.rootUser.piBody.users.items():
            if not Path(aUserFileName).is_file():
                brokenLinkes.append(aUserName)
                chk4BrokenLinkes = True
                saveRoot = True
        while brokenLinkes:
            del self.rootUser.piBody.users[brokenLinkes.pop()]
        if not currUserName in self.rootUser.piBody.users.keys():
            self.rootUser.piBody.user = self.rootUser.piBase.piTitle
            saveRoot = True
        if saveRoot: self.rootUser.piSave()
    def _establishedCurrentIndexerPis(self):
        '''Re-Establishes the current user-realm-domain-subject hierarcy as establish in these pi files. '''
        piCurrUserPathStr = self.rootUser.users[self.rootUser.user]
        piCurrUserPath = Path(piCurrUserPathStr)
        if piCurrUserPath.is_file():
            aUser: PiUser = PiUser(fileName=piCurrUserPath)
            if aUser: # this is checked in piUser object
                self.User = aUser
                self.Realm = PiRealm(fileName=self.User.realms[self.User.realm])
                self.Domain = PiDomain(fileName=self.Realm.domains[self.Realm.domain])
                self.Subject = PiSubject(fileName=self.Domain.subjects[self.Domain.subject])
            else:
                self.bldInitStdCurrUser()
        else:
            self.bldInitStdCurrUser()
    def bldInitStdCurrUser(self):
        '''Select or build a new standard user from CLI during bootstraping.
           A call to buildUser from pi.piClasses.piUser creates the user files.
           ****** Reconcile two similer functions (createNewUser) ******'''
        userPiPaths: dict = self.rootUser.users
        # input_data = sys.stdin.read()
        # print("------")
        # print(input_data)
        # print("------")
        # exit(0)
        if userPiPaths:
            userNameList = list(userPiPaths.keys())
            userNames = {}
            picklistID = 1
            picklistStr = "1. Create new user\n"
            # Make list of users
            for userName in userPiPaths.keys():
                picklistID += 1
                userNames[str(picklistID)] = userName # was userPis
                picklistStr += f'{str(picklistID)}. {userName}\n'
            picklistStr += 'Choose user from list (cancel with any other entry): '
            # Ask user to choose a user
            newUserIDStr = input(picklistStr)
            if newUserIDStr.isnumeric():
                newUserID = int(newUserIDStr)
                if picklistID < newUserID < 1:
                    picklistID = 0
                else:
                    picklistID = newUserID
            else: picklistID = 0
            if picklistID == 1:
                #creat new user
                prompt = "New user name: "
                newUserPiTitle = ""
                while not newUserPiTitle:
                    newUserPiTitle = getInput(prompt)
                    if newUserPiTitle in userNameList:
                        print(f'{" "*80}{curserUpLineCode}', end='\x1b[1K\r')
                        print(f'{newUserPiTitle} exists.')
                        newUserPiTitle = ""
                prompt = "New user short discription: "
                newUserPiSD = ""
                print(f'{" "*80}{curserUpLineCode}', end='\x1b[1K\r')
                while not newUserPiSD:
                    newUserPiSD = getInput(prompt)
                    print(f'{" "*80}{curserUpLineCode}', end='\x1b[1K\r')
                print('\n')
                print()
                if debugSet == debugOn: curserUpLines = 0
                else: curserUpLines = 1
                piUserProfile: PiUserProfile = getPiUserProfile(newUserPiTitle,curserUpLines=curserUpLines)
                newUser: PiUser = buildUser(newUserPiTitle, newUserPiSD, piUserProfile, True)
                if newUser:
                    # add to rootUser
                    self.rootUser.piBody.users[newUser.piBase.piTitle] = str(newUser.piJsonFilePath)
                    self.rootUser.piSave()
                    # set User objects
                    self.User = newUser
                    self.Realm = PiRealm(fileName=self.User.realms[self.User.realm])
                    self.Domain = PiDomain(fileName=self.Realm.domains[self.Realm.domain])
                    self.Subject = PiSubject(fileName=self.Domain.subjects[self.Domain.subject])
                else:
                    self.setCurrentIndexer(self.piIndexerTypes[0], self.rootUser.piBase.piTitle)
                    if not self.rootUser: printIt(f'rootUser not set.',lable.ERROR)
            elif picklistID > 1:
                print(userNames[str(picklistID)])
                self.setCurrentIndexer(self.piIndexerTypes[0],userNames[str(picklistID)])
            else: pass # 0 picked to cancel
        else: printIt('type file not set properly',lable.ERROR)
    def createNewUser(self, newUserPiTitle='', newUserPiSD='', piUserProfile: PiUserProfile=None) -> PiUser:
        '''Create a new standard user from CLI. A call to buildUser
           from pi.piClasses.piUser creates the user files.
           ****** Reconcile two similer functions (bldInitStdCurrUser) ******'''
        #creat new user
        userFiles: dict = self.rootUser.piBody.users
        if userFiles:
            picklistStr = "New user name: "
            while not newUserPiTitle:
                print(f'{" "*80}{curserUpLineCode}', end='\x1b[1K\r')
                newUserPiTitle = input(picklistStr)
                if newUserPiTitle in userFiles.keys():
                    print(f'{" "*80}{curserUpLineCode}', end='\x1b[1K\r')
                    print(f'{newUserPiTitle} exists.')
                    newUserPiTitle = ""
            picklistStr = "New user short discription: "
            while not newUserPiSD:
                print(f'{" "*80}{curserUpLineCode}', end='\x1b[1K\r')
                newUserPiSD = input(picklistStr)
            if not piUserProfile:
                print('\n')
                print()
                if debugSet == debugOn: curserUpLines = 0
                else: curserUpLines = 1
                piUserProfile: PiUserProfile = getPiUserProfile(newUserPiTitle,curserUpLines=curserUpLines)
            printIt(f'piUserProfile: {piUserProfile}',debugOff)
            newUser = buildUser(newUserPiTitle, newUserPiSD, piUserProfile)
            if newUser: # this is checked in piUser object
                self.rootUser.user = newUserPiTitle
                self.rootUser.users[newUserPiTitle] = str(newUser.piJsonFilePath)
                self.rootUser.piSave()
                self.User = newUser
                self.Realm = PiRealm(fileName=self.User.realms[self.User.realm])
                self.Domain = PiDomain(fileName=self.Realm.domains[self.Realm.domain])
                self.Subject = PiSubject(fileName=self.Domain.subjects[self.Domain.subject])
                self.setCurrentIndexer(self.piIndexerTypes[1], 'public')
            else:
                self.setCurrentIndexer(self.piIndexerTypes[0], self.rootUser.piBase.piTitle)
                if not self.rootUser: printIt(f'rootUser not set.',lable.ERROR)
        else:
            newUser = None
        return newUser
    def getUserTypeFileList(self, thePiType: str, source = 'curr') -> tuple[str, dict]:
        '''If type exits, return the name of the specilzed piType containing the dictionary of file names
           for the requested type.'''
        #print('in getUserTypeFileList')
        parrent = ''
        piTypePiFiles = None
        subjectType = 'topic'
        if source == 'curr':
            if thePiType == self.piIndexerTypes[0]: piTypePiFiles = self.User.piBody.users; parrent = self.piIndexerTypes[0]
            elif thePiType == self.piIndexerTypes[1]: piTypePiFiles = self.User.piBody.realms; parrent = self.piIndexerTypes[0]
            elif thePiType == self.piIndexerTypes[2]: piTypePiFiles = self.Realm.piBody.domains; parrent = self.piIndexerTypes[1]
            elif thePiType == self.piIndexerTypes[3]: piTypePiFiles = self.Domain.piBody.subjects; parrent = self.piIndexerTypes[2]
            #else: parrent, piTypePiFiles = self.getUserPublicTypeFileList(thePiType)
            if not piTypePiFiles:
                if thePiType in self.piPiClasses.piSpcTypeNames.keys(): subjectType = thePiType
                else: subjectType = 'topic'
                subjectTypes = self.Subject.piBody.topics
                if subjectType in subjectTypes.keys():
                    piPiTypeClass = self.piPiClasses.piSpcTypeNames[subjectType]
                    piContainerName = piPiTypeClass['piContainerNames'][0]  # [0] this is the 's' form.
                    exec(f'from pi.piClasses.{piPiTypeClass["piFileStem"]} import {piPiTypeClass["piClassName"]}')
                    piPiType = eval(f'{piPiTypeClass["piClassName"]}(fileName=subjectTypes[subjectType])')
                    piTypePiFiles: dict = eval(f'piPiType.piBody.{piContainerName}')
                    if not subjectType == thePiType: # Need go a leverl deeper to generic topics
                        if thePiType in piTypePiFiles.keys():
                            piTopicPi = eval(f'{piPiTypeClass["piClassName"]}(fileName=piTypePiFiles[thePiType])')
                            piTypePiFiles: dict = eval(f'piTopicPi.piBody.{piContainerName}')
                            parrent = thePiType
        else: # use root as the source
            if thePiType == self.piIndexerTypes[0]: piTypePiFiles = self.rootUser.piBody.users; parrent = self.piIndexerTypes[0]
            elif thePiType == self.piIndexerTypes[1]: piTypePiFiles = self.rootUser.piBody.realms; parrent = self.piIndexerTypes[0]
            elif thePiType == self.piIndexerTypes[2]:
                parrent = self.piIndexerTypes[1]
                rootRealm = PiRealm(self.rootUser.piBody.realms[self.rootUser.piBody.realm])
                piTypePiFiles = rootRealm.piBody.domains
            elif thePiType == self.piIndexerTypes[3]:
                parrent = self.piIndexerTypes[2]
                rootRealm = PiRealm(fileName=self.rootUser.piBody.realms[self.rootUser.piBody.realm])
                rootDomain = PiDomain(fileName=rootRealm.piBody.domains[rootRealm.piBody.domain])
                piTypePiFiles = rootDomain.piBody.subjects

            parrent, piTypePiFiles = self.getUserPublicTypeFileList(thePiType)
            if not piTypePiFiles:
                if thePiType in self.piPiClasses.piSpcTypeNames.keys(): subjectType = thePiType
                else: subjectType = 'topic'
                rootRealm = PiRealm(fileName=self.rootUser.piBody.realms[self.rootUser.piBody.realm])
                rootDomain = PiDomain(fileName=rootRealm.piBody.domains[rootRealm.piBody.domain])
                rootSubject = PiSubject(fileName=rootDomain.piBody.subjects[rootDomain.piBody.subject])
                subjectTypes = rootSubject.piBody.topics
                if subjectType in subjectTypes.keys():
                    piPiTypeClass = self.piPiClasses.piSpcTypeNames[subjectType]
                    piContainerName = piPiTypeClass['piContainerNames'][0]  # [0] this is the 's' form.
                    exec(f'from pi.piClasses.{piPiTypeClass["piFileStem"]} import {piPiTypeClass["piClassName"]}')
                    piPiType = eval(f'{piPiTypeClass["piClassName"]}(fileName=subjectTypes[subjectType])')
                    piTypePiFiles: dict = eval(f'piPiType.piBody.{piContainerName}') # [0] relms for user, the 's' form.
                    if not subjectType == thePiType: # Need go a leverl deeper to generic topics
                        if thePiType in piTypePiFiles.keys():
                            piTopicPi = eval(f'{piPiTypeClass["piClassName"]}(fileName=piTypePiFiles[thePiType])')
                            piTypePiFiles: dict = eval(f'piTopicPi.piBody.{piContainerName}')
                            parrent = thePiType
        if not piTypePiFiles:
            pass
            printIt(f'xx{thePiType} is not a topic.',lable.ERROR)
        return parrent, piTypePiFiles

    def getUserPublicTypeFileList(self,thePiType: str) -> tuple[str, dict]:
        # print(f'in getUserPublicTypeFileList, thePiType = {thePiType}')
        parrent = ''
        piTypePiFiles = None
        globalType = self.getGlblWordType(thePiType)
        # print('globalType',globalType)
        if not globalType: return parrent, piTypePiFiles

        print(self.piPiClasses.json().keys())
        piClassName = self.piPiClasses.piTypeNameClasses[globalType]['piClassName']
        parentTypeName = self.piPiClasses.piSpcClassNames[piClassName]['piIndexName']
        globalSubject: PiSubject = self.getRootPublicSubject()
        # print(f'{parentTypeName} in', globalSubject.topics.keys())
        print(f'{parentTypeName} in', self.piPiClasses.piSpcTypeNames.keys())
        if parentTypeName in globalSubject.topics.keys():
            print(f'piSpcTypeNames {dumps(self.piPiClasses.piSpcTypeNames[parentTypeName],indent=2)}')
            parentTopicFileName = globalSubject.topics[parentTypeName]
            parentClassName = self.piPiClasses.piSpcTypeNames[parentTypeName]['piClassName']
            parentFileStem = self.piPiClasses.piSpcTypeNames[parentTypeName]['piFileStem']
            parentContainerName = self.piPiClasses.piSpcTypeNames[parentTypeName]['piContainerNames'][0]
            #exec(f'from pi.piClasses.{parentFileStem} import {parentClassName}')
            #eval(f'{parentClassName}(fileName="{parentTopicFileName}")')
            print(dumps(piTypePi.piBody.json(),indent=2))
            if parentContainerName == 'tries':
                piTypePiTypeTopics = eval(f'piTypePi.piBody.{parentContainerName}')
            else:
                piTypePi = self.create_pi_object(parentTopicFileName)
                piTypePiTypeTopics = eval(f'piTypePi.piBody.{parentContainerName}')
                # print(f'{thePiType} in ',piTypePiTypeTopics.keys())
            if thePiType == parentTypeName:
                piTypePiFiles = piTypePiTypeTopics
                parrent = globalType
            elif thePiType in piTypePiTypeTopics.keys():
                thePiFileName = piTypePiTypeTopics[thePiType]
                thePiTypePi = eval(f'{parentClassName}(fileName="{thePiFileName}")')
                piTypePiFiles = eval(f'thePiTypePi.piBody.{parentContainerName}')
                parrent = parentTypeName
                return parrent, piTypePiFiles
        else:
            print('else getUserPublicTypeFileList')
        return parrent, piTypePiFiles
    def glbWordTrie(self) -> PiTrie:
        ''' the root.public.untitled.untitled.trie.word'''
        chkTuple = self.getUserPublicTypeFileList('word')
        if chkTuple[0] == 'trie':
            if chkTuple[1]:
                self.glbWordTrieFileName = chkTuple[1]
                printIt(f'glbWordTrieFileName: {self.glbWordTrieFileName}',lable.DEBUG)
                self.glbWordTrie = PiTrie(fileName=self.glbWordTrieFileName)
        else:
            if not self.__populateGlbWordTrie(): return None
    def populateGlbWordTrie(self, start=0, end=0) -> bool:
        seedGlbWordFileName = Path(__file__).parents[1].joinpath('piWords/allPiWords.json')
        if Path(seedGlbWordFileName).is_file():
            seedGlbWordToken = PiToken(fileName=seedGlbWordFileName)
            if end == 0: end = len(seedGlbWordToken.piBody.tokens.keys())
            processCount = end - start
            if processCount > 1:
                startRun = input(f'Process {processCount} words (N/y):')
                if len(startRun) == 0: return False
                if len(startRun) > 1: return False
                if not startRun[0].lower() == 'y': return False
            start_time00 = time()
            print('start, end',start, end)
            i = 0
            piType = 'word'
            dateTimeNow = str(datetime.now())
            logIt(f'recover from: {dateTimeNow}',logFileName='recover.sh')

            for aToken, aRef in seedGlbWordToken.piBody.tokens.items():
                # print(f'aToken00 {i}:',aToken)
                srcFileName = aRef.replace('pis/','pis/piWordRoot-')
                if i >= start:
                    # print(f'aToken00 {i}:',aToken)
                    ## start_time01 = time()
                    newPiPi = self.reqNewPi(piType, aToken, 'TBD')
                    if newPiPi:
                        # this log file gets very large off for now 07/12/2025
                        #logIt(f'aToken01 {i}: {aToken}',logFileName='trie.log')
                        print('trie.log gets very large off for now 07/12/2025')
                        print(f'aToken01 {i}:',aToken,f'    populateGlbWordTrie()')
                        print('-'*10)
                    else:
                        print(f'Found ({i}): {aToken}')
                    #print("--- %s reqNewPi ---" % (time() - start_time01))
                    if i >= end: break
                i +=1
            print("--- %s total ---" % (time() - start_time00))
        else:
            printIt(f'{seedGlbWordFileName}',lable.FileNotFound)
    def getWordPiTrie(self,thePiType: str) -> PiTrie:
        ''' currentaly used to return root.public.untitled.untitled topic list '''
        # print(f'in getUserPublicTypeFileList, thePiType = {thePiType}')
        parrent = ''
        piTypePiFiles = None
        globalType = self.getGlblWordType(thePiType)
        # print('globalType',globalType)
        if not globalType: return parrent, piTypePiFiles
        print('globalType,thePiType:',globalType,thePiType)
        currIndexStr = self.indexerAsTitels(self.currIndexer)
        if globalType == thePiType:
        #piClassName = self.piPiClasses.piTypeNameClasses[globalType]['piClassName']
        #parentTypeName = self.piPiClasses.piSpcClassNames[piClassName]['piIndexName']
            print('h1cccc')
            wordTrie: PiTrie = self.getWordTrie(self.rootUser.piBase.piTitle,'public',thePiType)
        else:
            # print('currIndexStr.piRealm:',currIndexStr.piRealm)
            print('h2cccv')
            wordTrie: PiTrie = self.getWordTrie(self.User.piBase.piTitle,currIndexStr.piRealm,thePiType)
        # print(f'{parentTypeName} in', globalSubject.topics.keys())
        # print(f'{parentTypeName} in', self.piPiClasses.piSpcTypeNames.keys())
        if wordTrie: return wordTrie
        else: return None
    def getRootUntiledRealmSubject(self, realmTitle: str) -> PiSubject:
        # print('in getRootUntiledRealmSubject')
        if not self.Domain: print('Domain not set')
        #print(f'subject piTitle = {piTitle}')
        #print(f'self.Domain.body = {self.Domain.piBody}')
        rootPublicRealmFileName = self.rootUser.piBody.realms[realmTitle]
        rootPublicRealm = PiRealm(fileName=rootPublicRealmFileName)
        rootPublicDomainFileName = rootPublicRealm.piBody.domains['untitled']
        rootPublicDomain = PiDomain(fileName=rootPublicDomainFileName)
        rootPublicSubjectFileName = rootPublicDomain.piBody.subjects['untitled']
        rootPublicSubject = PiSubject(fileName=rootPublicSubjectFileName)
        return rootPublicSubject
    def getCurrUntiledRealmSubject(self, realmTitle: str) -> PiSubject:
        # print('in getCurrUntiledRealmSubject')
        if not self.Domain: print('Domain not set')
        #print(f'subject piTitle = {piTitle}')
        #print(f'self.Domain.body = {self.Domain.piBody}')
        currPublicRealmFileName = self.User.piBody.realms[realmTitle]
        currPublicRealm = PiRealm(fileName=currPublicRealmFileName)
        currPublicDomainFileName = currPublicRealm.piBody.domains['untitled']
        currPublicDomain = PiDomain(fileName=currPublicDomainFileName)
        currPublicSubjectFileName = currPublicDomain.piBody.subjects['untitled']
        # print(currPublicSubjectFileName)
        return PiSubject(fileName=currPublicSubjectFileName)
    def getTrieTrieFile(self, user:str, realm:str) -> tuple[PiSubject, PiTrie]:
        ''' Returns the word try sepecifed by trieTitle'''
        wordSubject = None
        trieTrie = None
        realmFileName = ''
        if user == 'root':
            realmFileName = self.rootUser.piBody.realms[realm]
            #piIndexer = self.rootUser.piIndexer.copy()
        else:
            user = self.User.piBase.piTitle
            realmFileName = self.User.piBody.realms[realm]
            #piIndexer = self.User.piIndexer.copy()
        if realmFileName:
            theRealm = PiRealm(fileName=realmFileName)
            theDomainFileName = theRealm.piBody.domains['untitled']
            theDomain = PiDomain(fileName=theDomainFileName)
            theSubjectFileName = theDomain.piBody.subjects['untitled']
            wordSubject = PiSubject(fileName=theSubjectFileName)
            piIndexer = wordSubject.piIndexer.copy()
        if wordSubject:
            # print(f'wordSubject {wordSubject.piBase.piSD.split()[0]}') # first word is username.
            trieTrieFileName = wordSubject.getTopicFileName('trie')
        if not trieTrieFileName:
            # create trie trie file for user.realm.domain.subject useing piBase and currPiIndexer as impadance
            piBase = PiBase('trie','trie', f'{user} {realm} {self.Subject.piBase.piTitle} trie trie file.')
            trieTrie: PiTrie  = wordSubject.setTopic(piBase, piIndexer, self.piIDIndexUpdates)
            self.piIDIndexUpdates.push(trieTrie.piIndexer.piUser, trieTrie.piID, str(trieTrie.piJsonFilePath))
            self._establishedCurrentIndexerPis()
            trieTrieFileName = wordSubject.getTopicFileName('trie')
        else:
            trieTrie = PiTrie(fileName=trieTrieFileName)
        return wordSubject, trieTrie
    def getWordTrie(self, user:str, realm:str, trieTitle:str = 'word') -> PiTrie:
        ''' Returns the word try sepecifed by trieTitle'''
        # print('getWordTrie', user, realm, trieTitle)
        wordSubject:PiSubject = None
        trieTrie:PiTrie = None
        wordTrie:PiTrie = None
        wordSubject, trieTrie = self.getTrieTrieFile(user, realm)
        piIndexer = wordSubject.piIndexer.copy()
        #print(f'user: {user}, realm: {realm}, trieTitle: {trieTitle}')
        if trieTitle in trieTrie.piBody.root.children.keys():
            wordTrieFileName = trieTrie.piBody.root.children[trieTitle].filename
        else:
            # create trie file for title
            print('# PI create trie file for title in subject:',user,wordSubject.piBase.piTitle, wordSubject.piID)
            piBase = PiBase('trie',trieTitle, f'{user} {realm} trie {trieTitle} file.')
            triePi: PiTrie = wordSubject.setTopic(piBase, piIndexer, self.piIDIndexUpdates)
            #triePi.piSave(suppress=False)
            self._establishedCurrentIndexerPis()
            self.piIDIndexUpdates.push(triePi.piIndexer.piUser, triePi.piID, str(triePi.piJsonFilePath))
            wordTrieFileName = triePi.piJsonFilePath

        # print('wordTrieFileName',wordTrieFileName)
        wordTrie = PiTrie(fileName=wordTrieFileName)
        return wordTrie
    def getGlblConatinerPi(self, piType: str) -> tuple[str, PiPi]:
        parentContainerName = ''
        rtnPiPi = None
        globalType = self.getGlblWordType(piType)
        piGlobalStoreTypeNames = self.piPiClasses.piGlobalStoreTypeNames
        if globalType in piGlobalStoreTypeNames.keys():
            globalTypeClass = piGlobalStoreTypeNames[globalType]
            piIndexName = self.piPiClasses.piSpcClassNames[globalTypeClass]['piIndexName']
            globalSubject: PiSubject = self.getRootUntiledRealmSubject('public')
            parentTopicFileName = globalSubject.topics[piIndexName]
            parentClassName = self.piPiClasses.piSpcTypeNames[piIndexName]['piClassName']
            parentFileStem = self.piPiClasses.piSpcTypeNames[piIndexName]['piFileStem']
            parentContainerName = self.piPiClasses.piSpcTypeNames[piIndexName]['piContainerNames'][0]
            exec(f'from pi.piClasses.{parentFileStem} import {parentClassName}')
            piTypePi = eval(f'{parentClassName}(fileName="{parentTopicFileName}")')
            #piTypePiTypeTopics = eval(f'piTypePi.piBody.{parentContainerName}')
            rtnPiPi = piTypePi
        return parentContainerName, rtnPiPi
    def getPiIndexerPi(self, piType: str) -> PiPi:
        pi_type_map = {
            "user": self.User,
            "realm": self.Realm,
            "domain": self.Domain,
            "subject": self.Subject,
        }
        return pi_type_map.get(piType)

    def getCurrPiType(self, thePiType: str) -> PiPi:
        '''Returns current specilized of standard piType PiPi based on thePiType.'''
        piPi = None
        chkSpecPiType = False
        print('l2',thePiType,chkSpecPiType)
        # id piIndexer the the current pi is returned
        if thePiType == self.piIndexerTypes[0]: piPi = self.User
        elif thePiType == self.piIndexerTypes[1]: piPi = self.Realm
        elif thePiType == self.piIndexerTypes[2]: piPi = self.Domain
        elif thePiType == self.piIndexerTypes[3]:  piPi = self.Subject
        elif thePiType == 'topic':  # provide specilized or standard pi Type
            piPi = PiPi(fileName=self.Subject.piBody.types[self.Subject.piBody.type])
            if piPi.piBase.piType == self.piIndexerTypes[4]:
                piPi = PiTopic(fileName=self.Subject.piBody.types[self.Subject.piBody.type])
            else: chkSpecPiType = True
        else: chkSpecPiType = True
        print('l2',thePiType,chkSpecPiType)
        if chkSpecPiType:
            piTypeClasses = self.piPiClasses.piSpcTypeNames
            if thePiType in piTypeClasses.keys(): # PiClassTypeName
                exec(f'from pi.piClasses.{piTypeClasses[thePiType]["piFileStem"]} import {thePiType}')
                piPi = eval(f'{thePiType}(fileName=self.Subject.piBody.types[{thePiType}])')
                printIt(f'getCurrPiType piPi {type(piPi)}',debugSet)
            else:
                #printIt(f'{thePiType} type not valid.',lable.ERROR)
                pass
        return piPi
    def sortPiModDateList(self,arr):
        n = len(arr)
        swapped = False
        # Traverse through all array elements
        for i in range(n-1):
            for j in range(0, n-i-1):
                if arr[j]['piModDate'] < arr[j + 1]['piModDate']:
                    swapped = True
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
            if not swapped:
                return
    def isCurrIndexerPi(self, piPath: Path, piType: str = ''):
        piTypeIndex = 3
        # if piType:
        #     if piType in self.piIndexerTypes:
        #         piTypeIndex = self.piIndexerTypes.index(piType)
        currUserPath: Path = self.pisPath.joinpath(self.User.piID)
        chkPath = currUserPath
        if piTypeIndex >= 1:
            currUserPath = currUserPath.joinpath(self.Realm.piID)
            chkPath = piPath.parents[4-piTypeIndex]
        if piTypeIndex >= 2:
            currUserPath = currUserPath.joinpath(self.Domain.piID)
            chkPath = piPath.parents[4-piTypeIndex]
        if piTypeIndex >= 3:
            currUserPath = currUserPath.joinpath(self.Subject.piID)
            chkPath = piPath.parents[4-piTypeIndex]
        return currUserPath == chkPath
    def getLatestPiList4CurrSubject(self, piType: str = '', numOfPis=3) -> list:
        piIDIndexFileName = self.User.piBody.piIDIndex
        piIDIndex = PiIDIndex(fileName=piIDIndexFileName)
        piIndexer = self.currIndexer
        rtnPis = []
        currPis = self.Subject.getDecendents()
        #print('currPis\n',currPis)
        for piID in currPis:
            piIDNode, piIDIndexFileName = piIDIndex.search(piID)
            if piIDNode != None:
                currPiFileName = piIDNode.children[piID].filename
                piPi = PiPi(fileName=currPiFileName)
                addPi = piIndexer.piUser == piPi.piIndexer.piUser and \
                        piIndexer.piRealm == piPi.piIndexer.piRealm and \
                        piIndexer.piDomain == piPi.piIndexer.piDomain and \
                        piIndexer.piSubject == piPi.piIndexer.piSubject and \
                        piPi.piBase.piType not in self.piIndexerTypes + ['topic']
                if addPi:
                    rtnPis.append(piPi)
            else:
                printIt(f'{piID}',lable.FileNotFound)
        return rtnPis

    def getCurrUserBodyRealms(self) -> list:
        thePi = self.getPiIndexerPi(self.piIndexerTypes[0])
        return list(thePi.piBody.realms.keys())
    def getCurrRealmBodyDomains(self) -> list:
        thePi = self.getPiIndexerPi(self.piIndexerTypes[1])
        return list(thePi.piBody.domains.keys())
    def getCurrDomainBodySubjects(self) -> list:
        thePi = self.getPiIndexerPi(self.piIndexerTypes[2])
        return list(thePi.piBody.subjects.keys())
    def getCurrSubjectBodyTopics(self) -> list:
        thePi = self.getPiIndexerPi(self.piIndexerTypes[3])
        if 'topic' in thePi.piBody.topics.keys():
            theTopicPi = PiTopic(fileName=thePi.piBody.topics['topic'])
            return list(theTopicPi.piBody.topics.keys())
        return []
    def getCurrPiTypeList(self, piType: str = '', numOfPis=3) -> list:
        pi_type_map = {
            "user": self.getCurrUserBodyRealms(),
            "realm": self.getCurrRealmBodyDomains(),
            "domain": self.getCurrDomainBodySubjects(),
            "subject": self.getCurrSubjectBodyTopics()
        }
        if piType in self.piPiClasses.piIndexerTypes:
            rtnList = pi_type_map.get(piType)
        return rtnList
        # printIt(f'CLI output number of pis and the numOfPis to list.',lable.TODO)
        # printIt(f'Store numOfPis in .pirc. Consider creating a piRC ',lable.TODO)
        # printIt(f'piType to store this information per user. Just',lable.TODO)
        # printIt(f'like piIDIndex are stored. Also we need piIndex files',lable.TODO)
        # printIt(f'to store pis indexed  by piType.',lable.TODO)
        # piIDIndexFileName = self.User.piBody.piIDIndex
        # piIDIndex = PiIDIndex(fileName=piIDIndexFileName)
        # print(piIDIndex.piBase)
        # print(piIDIndex.piBody)
        # currPi = piIDIndex.piBody.currPi
        # piIndexer = self.currIndexer
        # rtnPis = []
        # for piID in currPi:
        #     piIDNode, piIDIndexFileName = piIDIndex.search(piID)
        #     currPiFileName = piIDNode.children[piID].filename
        #     piPi = PiPi(fileName=currPiFileName)
        #     addPi = piIndexer.piUser == piPi.piIndexer.piUser and \
        #             piIndexer.piRealm == piPi.piIndexer.piRealm and \
        #             piIndexer.piDomain == piPi.piIndexer.piDomain and \
        #             piIndexer.piSubject == piPi.piIndexer.piSubject and \
        #             piPi.piBase.piType not in self.piIndexerTypes + ['topic']
        #     #print('currPiIndexer',piIndexer)
        #     if addPi:
        #         #print('pi:',piPi.piBase.piType, piPi.piBase.piTitle)
        #         #print('parts:\n',Path(currPiFileName).parts)
        #         #print('piIndexer:\n',piIndexer)
        #         rtnPis.append(piPi)
        # return rtnPis
    def create_pi_object(self, pi_file_name: str):
        '''
        Creates a Pi object based on the piType found in the file.
        Args:
            pi_file_name: The name of the PI file.
        Returns:
            A Pi object of the appropriate type.
            Returns None if the piType is not supported.
        '''
        if Path(pi_file_name).is_file():
            the_pi = PiPi(fileName=str(pi_file_name))
            pi_type = the_pi.piBase.piType
            pi_type_map = {
                "user": PiUser,
                "realm": PiRealm,
                "domain": PiDomain,
                "subject": PiSubject,
                "topic": PiTopic,
                "piIDIndex": PiIDIndex,
                "trie": PiTrie,
            }
            pi_class = pi_type_map.get(pi_type)  # Safely get the class from the map
            if pi_class:
                the_pi = pi_class(fileName=str(pi_file_name))
            return the_pi
        else:
            return None
    def getFileNameFromPiID(self, piID: str, userSource: PiUser = None):
        if userSource:
            userIDIndex=PiIDIndex(fileName=userSource.piBody.piIDIndex)
            try:
                piIDNode, piIDIndexFileName = userIDIndex.search(piID)
            except:
                pass
            source = userSource.piID
        else:
            userIDIndex=PiIDIndex(fileName=self.User.piBody.piIDIndex)
            try:
                piIDNode, piIDIndexFileName = userIDIndex.search(piID)
                #print(piID,dumps(piIDNode.json(),indent=2))
                #print(userIDIndex.piBase,'piIDIndexFileName')
                piFileName = Path(piIDNode.children[piID].filename)
                #print(piFileName)
                source = self.User.piID
            except:
                userIDIndex=PiIDIndex(fileName=self.rootUser.piBody.piIDIndex)
                try:
                    piIDNode, piIDIndexFileName = userIDIndex.search(piID)
                    piFileName = Path(piIDNode.children[piID].filename)
                    source = self.rootUser.piID
                except:
                    return None
        if not piFileName:
            printIt(f'piID: {piID}',lable.FileNotFound)
            return None
        return piFileName
    def piFromLink(self, piID: str|Path, userSource: PiUser = None, suppress = False):
        # This is used for CLI listing.
        ''' piID as str assumes a piMD5 soft-link in the root or current user\n
            piID as Path will open a pi json file as a PiPi\n
            return: PiPi, and the source as 'root' or 'curr'.'''
        rtnPi: object = None
        source: str = ''
        piFileName: Path = None
        if type(piID) == str:
            if isPiID(piID):
                piFileName = self.getFileNameFromPiID(piID)
            else:
                piFileName = Path(piID)
        elif str(type(piID)) in ["<class 'pathlib.PosixPath'>", "<class 'pathlib.Path'>"]:
            piFileName = piID
        if piFileName:
            thePi = self.create_pi_object(piFileName)
            rtnPi = thePi
            if not source: source = self.rootUser.piID
            else: source = self.User.piID
        else:
            if not suppress:
                printIt(f'{piID} ({self.User.piBase.piTitle})',lable.FileNotFound)
        return rtnPi, source
    def piTitleFromLink(self, piID):
        rtnPiTitle = f'piID not found'
        pi: PiPi = None
        if isPiID(piID):
            pi, source = self.piFromLink(piID)
            if pi: rtnPiTitle = pi.piBase.piTitle
            else: source = ''
        else: # assume pi is title
            rtnPiTitle = piID
            source = ''
        return rtnPiTitle, source
    def indexerAsTitels(self, piIndexer: PiIndexer|dict) -> PiIndexer:
        rtnIndexer = PiIndexer()
        if type(piIndexer) == dict: piIndexer = PiIndexer(**piIndexer)
        printIt(f'indexerTitels: {piIndexer}', debugSet, debugOff)
        rtnIndexer.piUser = self.piTitleFromLink(piIndexer.piUser)[0]
        rtnIndexer.piRealm = self.piTitleFromLink(piIndexer.piRealm)[0]
        rtnIndexer.piDomain = self.piTitleFromLink(piIndexer.piDomain)[0]
        rtnIndexer.piSubject = self.piTitleFromLink(piIndexer.piSubject)[0]
        return rtnIndexer
    def currIndexerAsTitels(self) -> PiIndexer:
        piIndexer = PiIndexer()
        piIndexer.piUser = self.User.piBase.piTitle
        piIndexer.piRealm = self.Realm.piBase.piTitle
        piIndexer.piDomain = self.Domain.piBase.piTitle
        piIndexer.piSubject = self.Subject.piBase.piTitle
        return piIndexer
    def setUser(self, piTitle: str, createUser = True) -> bool:
        printIt('in setUser',debugSet)
        chgUser = False
        if not piTitle == self.User.piBase.piTitle:
            if piTitle in self.rootUser.piBody.users.keys():
                if Path(self.rootUser.piBody.users[piTitle]).is_file():
                    print(f'user being set to {piTitle}')
                    self.User = PiUser(fileName=self.rootUser.piBody.users[piTitle])
                    chgUser = True
                else:
                    self._checkUsersInRoot()
            else:
                if createUser:
                    newUser = self.createNewUser(piTitle)
                    if newUser:
                        self.User = newUser
                        self.rootUser.piBody.users[piTitle] = newUser
                        chgUser = True
            if chgUser:
                self.rootUser.piBody.user = piTitle
                self.rootUser.piSave()
                self.Realm = PiRealm(fileName=self.User.realms[self.User.realm])
                self.Domain = PiDomain(fileName=self.Realm.domains[self.Realm.domain])
                self.Subject = PiSubject(fileName=self.Domain.subjects[self.Domain.subject])
        else:
            printIt(self.User.piBody.piUserProfile.username,debugSet)
            #if 'rootuser' in self.User.piBody.piUserProfile.grants:
            chgUser = True
        return chgUser
    def setRealm(self, piTitle: str) -> bool:
        chgRealm = False
        if not piTitle == self.User.realm:
            if piTitle in self.User.realms.keys():
                self.Realm = PiRealm(fileName=self.User.realms[piTitle])
                chgRealm = True
                self.User.realm = piTitle
                self.User.piSave()
                self.Domain = PiDomain(fileName=self.Realm.domains[self.Realm.domain])
                self.Subject = PiSubject(fileName=self.Domain.subjects[self.Domain.subject])
        return chgRealm
    def setDomain(self, piTitle: str) -> bool:
        chgDomain = False
        #print(f'self.Realm.body = {self.Realm.piBody}')
        if not piTitle == self.Realm.domain:
            if piTitle in self.Realm.domains.keys():
                self.Domain = PiDomain(fileName=self.Realm.domains[piTitle])
                chgDomain = True
                self.Realm.domain = piTitle
                #print(f'self.Realm.body = {self.Realm.piBody}')
                self.Realm.piSave()
                self.Subject = PiSubject(fileName=self.Domain.subjects[self.Domain.subject])
        return chgDomain
    def setSubject(self, piTitle: str) -> bool:
        chgSubject= False
        if not self.Domain: print('Domain not set')
        #print(f'subject piTitle = {piTitle}')
        #print(f'self.Domain.body = {self.Domain.piBody}')
        if not piTitle == self.Domain.subject:
            if piTitle in self.Domain.subjects.keys():
                self.Subject = PiSubject(fileName=self.Domain.subjects[piTitle])
                chgSubject = True
                self.Domain.subject = piTitle
                self.Domain.piSave()
            else:
                printIt(f'{piTitle} not in self.Domain.subjects.keys',lable.WARN)
        return chgSubject
    def setCurrentIndexer(self, piType: str, piTitle: str) -> bool:
        printIt('in setCurrentIndexer',debugOff)
        indexerChanged = False
        if piType in self.piIndexerTypes: # pyType in ['user', 'realm', 'domain', 'subject'
            if piType == self.piIndexerTypes[0]: # user
                if piTitle != self.User.piBase.piTitle:
                    printIt(f'setCurrentIndexer: {piType}',debugSet)
                    indexerChanged = self.setUser(piTitle)
                else:
                    printIt(f'user set to: {piTitle}',lable.INFO)
            elif piType == self.piIndexerTypes[1]: # realm
                indexerChanged = self.setRealm(piTitle)
            elif piType == self.piIndexerTypes[2]: # domain
                indexerChanged = self.setDomain(piTitle)
            else: # piType == self.piIndexerTypes[0]  subject
                indexerChanged = self.setSubject(piTitle)
            if indexerChanged:
                # sd not need in log becuase it a current indexer change.
                piLogger.logChgPi(piPiLogStr(PiBase(piType,piTitle,'')))
        return indexerChanged
    # def piExists(self, newPiBase: PiBase) -> str:
    #     parentName = ''
    #     parentName, piFiles = self.getUserTypeFileList(newPiBase.piType)
    #     if piFiles:
    #         printIt(f'{newPiBase.piTitle}, {list(piFiles.keys())}',debugSet)
    #         if not newPiBase.piTitle in piFiles.keys(): parentName = ''
    #     else: parentName = ''
    #     return parentName
    def reqNewPi(self, piType:str, piTitle:str, piSD:str) -> PiPi:
        # This function is called by piAPI post and should not bypass unless by requesion in.
        '''Reqest that a new pi of any type be created and properly indexed unless one alrady exits.
           if pi exits then None is returned.
           Every pi is uniquly identifed by a signiture consiting of piType, piTitle, and
           piIndexer (piUser, piRealm, piDomain, piSubject).'''
        global debugSet
        debugHold = debugSet
        newPi = None
        # print(cStr('newPi:',color.CYAN),newPi is None)
        if piType in self.piIndexerTypes[0:2]: # [user, realm]
            return newPi # user and realms are not requested here.
        elif piType == self.piIndexerTypes[2]: # new domain needs new Untiteld subject
            newPi = self.Realm.setDomain(piTitle, piSD, self.piIDIndexUpdates)
            self.setDomain(newPi.piBase.piTitle)
            self.Domain = newPi
        elif piType == self.piIndexerTypes[3]: # new subject
            newPi = self.Domain.setSubject(piTitle, piSD, self.piIDIndexUpdates)
            self.setSubject(newPi.piBase.piTitle)
            self.Subject = newPi
        if newPi:
            piBase = newPi.piBase
        else:
            ''' Create new non-piIndex pi '''
            piExists = False
            piBase = PiBase(piType, piTitle, piSD)
            globalType = self.getGlblWordType(piType)
            if globalType:
                currIndexerAsTitels = self.currIndexerAsTitels()
                currentRealm = currIndexerAsTitels.piRealm
                targetRealm = 'public'
                if piType == globalType: # word == word or root.private.untitled.untitled word storage
                    print('reqNewPi',piType, piTitle, targetRealm, globalType)
                    globalSubject: PiSubject = self.getRootUntiledRealmSubject(targetRealm)
                    # printIt('globalSubject.piID:',globalSubject.piID,lable.DEBUG)
                    # start_time01 = time()
                    piIndexer01 = globalSubject.piIndexer.copy()
                    printIt('root.public.piSubject:',piIndexer01.piSubject,lable.DEBUG)
                    newPi = globalSubject.setTopic(piBase, piIndexer01, self.piIDIndexUpdates)
                    if newPi == None: return newPi
                    # print(f'{time() - start_time01} - root.{targetRealm}.{piType}: {piTitle}')
                else:
                    if currentRealm == 'public':
                        targetRealm = currentRealm
                        # Add public words to root and curr user
                        print('reqNewPi',piType, piTitle, targetRealm, globalType)
                        globalSubject: PiSubject = self.getRootUntiledRealmSubject(targetRealm)
                        # start_time01 = time()
                        piIndexer02 = globalSubject.piIndexer.copy()
                        printIt('root.public.piSubject:',piIndexer02.piSubject,lable.DEBUG)
                        newPi = globalSubject.setTopic(piBase, piIndexer02, self.piIDIndexUpdates)
                        # print(f'{time() - start_time01} - root.{targetRealm}.{piType}: {piTitle}')
                    currSubject: PiSubject = self.getCurrUntiledRealmSubject(targetRealm)
                    piIndexer03 = currSubject.piIndexer.copy()
                    printIt(f'user.{targetRealm}.piIndexer03.piSubject:',piIndexer03.piSubject,lable.DEBUG)
                    printIt(f'user.{targetRealm}.currSubject.piID:',currSubject.piID,lable.DEBUG)
                    # start_time01 = time()
                    newPi = currSubject.setTopic(piBase, piIndexer03, self.piIDIndexUpdates)
                    # print(f'{time() - start_time01} - {currIndexerAsTitels.piUser}.{targetRealm}.{piType}: {piTitle}')
                    piExists = True
            # else:
            #     printIt(f'should be {piType}', lable.ERROR)
            if not piExists:
                if piType == globalType:
                    print(piBase.piType,piBase.piTitle,piBase.piSD)
                    testWord = self.chkIfWord(piBase.piTitle)
                    if not testWord:
                        newPi = self.Subject.setTopic(piBase, piIndexer01, self.piIDIndexUpdates)
                    #printIt(f'why are we here, piType == globalType',lable.DEBUG)
                    #printIt(f'why are we here, {piType} == {globalType}',lable.DEBUG)
                else:
                    printIt('why are we here, piType != globalType',lable.DEBUG)
                    printIt(f'why are we here, {piType} != {globalType}',lable.DEBUG)
                    piIndexer = self.Subject.piIndexer.copy()
                    newPi = self.Subject.setTopic(piBase, piIndexer, self.piIDIndexUpdates)
        if self.piIDIndexUpdates.updates:
             self.piIDIndexUpdates.addFlush(self)
        return newPi
    def chkIfWord(self, testWord) -> str:
        rtnStr = ''
        globalSubject: PiSubject = self.getRootUntiledRealmSubject('public')
        trieTrieFileName = globalSubject.getTopicFileName('trie')
        if trieTrieFileName:
            # print(f'chkIfWord-trieTrieFileName: {trieTrieFileName}')
            trietrie = PiTrie(fileName=trieTrieFileName)
            # print(f'trieTrieFile: {trietrie.piBody.root.type_}, {trietrie.piBody.root.word} ({trietrie.piID})')
            aTrieFileName = trietrie.getTrieFileName('word')
            if aTrieFileName:
                trietrie = PiTrie(fileName=aTrieFileName)
                piTrieBody: PiTrieBody = trietrie.piBody
                aNode = piTrieBody.search(testWord)
                if not aNode == None:
                    if aNode.type_ == 'word':
                        piWord = PiWord(fileName=aNode.filename)
                        print(f'{piWord.piBase.piTitle} touches: {piWord.piTouch.piTouches}' )
                        #piWord.piTouch.piTouches += 1 Incrimentd when saved.
                        piWord.piSave()
                        rtnStr = aNode.word
        return rtnStr
    def getPiUserPiIDIndex(self, pi_user_id: PiPi):
        if self.rootUser and self.rootUser.piID == pi_user_id:
            return self.rootUser.piBody.piIDIndex
        if self.User and self.User.piID == pi_user_id:
            return self.User.piBody.piIDIndex
        return self.piFromLink(pi_user_id).piBody.piIDIndex
    def rmPiUserUpdates(self, thePi:PiUser):
        pass
    def rmPiRealmUpdates(self, thePi:PiRealm):
        pass
    def rmPiDomainUpdates(self, thePi:PiDomain):
        pass
    def rmPiSubjectUpdates(self, thePi:PiSubject):
        pass
    def rmPiTopicUpdates(self, thePi:PiTopic):
        print(f'rmPiTopicUpdates: {thePi.piBase}')
        if thePi.piBase.piTitle == 'topic':
            # remove all subTopics.
            assert thePi.piID == thePi.piTypeID
            for topic, fileName in thePi.piBody.topics.items():
                piTopic = PiTopic(fileName=fileName)
                self.rmPiTopicUpdates(piTopic)
        else:
            for topic, fileName in thePi.piBody.topics.items():
                topicPath = Path(fileName)
                self.piIDIndexUpdates.push(thePi.piIndexer.piUser, topicPath.stem, fileName)
        self.piIDIndexUpdates.push(thePi.piIndexer.piUser, thePi.piID, thePi.fileName)
    def rmPiIDIndexUpdates(self, thePi:PiIDIndex):
        pass
    def rmPiTrieUpdates(self, thePi:PiTrie):
        self.piIDIndexUpdates.push(thePi.piIndexer.piUser, thePi.piID, thePi.fileName)
    def rmPiPiUpdates(self, thePi:PiPi):
        self.piIDIndexUpdates.push(thePi.piIndexer.piUser, thePi.piID, thePi.fileName)
        piSubject, _ = self.piFromLink(thePi.piIndexer.piSubject)
        if thePi.piID in piSubject.piInfluence.piDescendent:
            print(f'piSubject.rmpiDescendent: {thePi.piID}')
            piSubject.piInfluence.piDescendent.remove(thePi.piID)
            piSubject.piSave()
        piTopics, _ = self.piFromLink(piSubject.topics['topic'])
        if thePi.piID in piTopics.piInfluence.piDescendent:
            print(f'piTopics.rmpiDescendent: {thePi.piID}')
            piTopics.piInfluence.piDescendent.remove(thePi.piID)
            piTopics.piSave()
        piTopic, _ = self.piFromLink(piTopics.topics[thePi.piBase.piType])
        if thePi.piID in piTopic.piInfluence.piDescendent:
            print(f'piTopic.rmpiDescendent: {thePi.piID}')
            piTopic.piInfluence.piDescendent.remove(thePi.piID)
        theTopicTitles = list(piTopic.topics.keys())
        if len(theTopicTitles) == 1:       # with only one topic of this piType remove topic file.
            assert thePi.piBase.piTitle in theTopicTitles
            self.rmPiTopicUpdates(piTopic)
        else:
            if thePi.piBase.piTitle in theTopicTitles:
                del piTopic.topics[thePi.piBase.piTitle]
                theTopicTitles.remove(thePi.piBase.piTitle)
                piTopic.piBody.topic = theTopicTitles[-1]
                piTopic.piSave()

    def get_rmFlush_Updates(self, piID):
        self.piIDIndexUpdates.updates = {}
        thePi, _ = self.piFromLink(piID)
        piType = thePi.piBase.piType
        piType_map = {
            "user": self.rmPiUserUpdates,
            "realm": self.rmPiRealmUpdates,
            "domain": self.rmPiDomainUpdates,
            "subject": self.rmPiSubjectUpdates,
            "topic": self.rmPiTopicUpdates,
            "piIDIndex": self.rmPiIDIndexUpdates,
            "trie": self.rmPiTrieUpdates,
        }
        if piType in piType_map:
            piDef = piType_map.get(piType)  # Safely get the class from the map
            piDef(thePi)
        else:
            self.rmPiPiUpdates(thePi)

    def rmPi(self,piID:str) -> list:
        outPis = []
        self.get_rmFlush_Updates(piID)
        for updates in self.piIDIndexUpdates.updates.values():
            print(dumps(updates,indent=2))
            for filename in updates.values():
                outPi, _ = self.piFromLink(filename)
                if not outPi: printIt(filename,lable.FileNotFound)
                outPis.append(outPi.json())
        self.piIDIndexUpdates.rmFlush(self)
        return outPis

    # def rm(self, piID):
    #     current_node, piIDIndexFileName = self.search(piID)
    #     piIDIndex = PiIDIndex(fileName=piIDIndexFileName)
    #     current_node, piIDIndexFileName = piIDIndex.search(piID)
    #     print(dumps(current_node,indent=2))

    # def getUserWordTypes(self, piType: str) -> str:
    #     ''' returns global word title if word is in special piType string.'''
    #     globalTokenType = ''
    #     piGlobalStoreTypeNames = self.piPiClasses.piGlobalStoreTypeNames
    #     piTypeLower = piType.lower()
    #     if piTypeLower in piGlobalStoreTypeNames.keys():
    #         globalTokenType = piTypeLower
    #     else:
    #         for piGlobalStoreTypeName in piGlobalStoreTypeNames.keys():
    #             match = findall(r"(?<!^" + piGlobalStoreTypeName + r").*" + piGlobalStoreTypeName + r"\b",piTypeLower)
    #             if match:
    #                 match = match[0]
    #                 if match == piType:
    #                     globalTokenType = piGlobalStoreTypeName
    #                     return globalTokenType
    #                 elif not self.words.isWord(match):
    #                     globalTokenType = piGlobalStoreTypeName
    #                     return globalTokenType
    #     return globalTokenType
    def getGlblWordType(self, piType: str) -> str:
        ''' returns global word title if word is in special piType string.'''
        globalTokenType = ''
        piGlobalStoreTypeNames = self.piPiClasses.piGlobalStoreTypeNames
        piTypeLower = piType.lower()
        if piTypeLower in piGlobalStoreTypeNames.keys():
            globalTokenType = piTypeLower
        else:
            for piGlobalStoreTypeName in piGlobalStoreTypeNames.keys():
                match = findall(r"(?<!^" + piGlobalStoreTypeName + r").*" + piGlobalStoreTypeName + r"\b",piTypeLower)
                if match:
                    match = match[0]
                    if match == piType:
                        globalTokenType = piGlobalStoreTypeName
                        return globalTokenType
                    elif not self.chkIfWord(match):
                        globalTokenType = piGlobalStoreTypeName
                        return globalTokenType
        return globalTokenType
    def getPathFromIndexer(self, thePIIndexer: PiIndexer) -> Path:
        chkPath = self.pisPath.joinpath(thePIIndexer.piUser)
        chkPath = chkPath.joinpath(thePIIndexer.piRealm)
        chkPath = chkPath.joinpath(thePIIndexer.piDomain)
        chkPath = chkPath.joinpath(thePIIndexer.piSubject)
        return chkPath
    def touchPi(self,thePi: PiPi):
        print('here in touchPi')
        rootLinksFileName = self.rootUser.piBody.piIDIndex
        piIDIndex = PiIDIndex(fileName=rootLinksFileName)
        print('In touchPi of piCurrentIdexer: ',len(piIDIndex.piBody.children.keys()))
        piIDNode, aPiIDIndex = piIDIndex.search(thePi)
        if piIDNode:
            thePi = PiPi(fileName=piIDNode.filename)
            thePi.piTouch.piModificationDate = str(datetime.now())
            thePi.piTouch.piTouches += 1
            thePi.piSave()
    def addPiDescendants(self, decendentPi: PiPi):
        # decendentPi will be add to the rootuser and curruser.
        # Then all the indexers down to the current pi
        if decendentPi.rootStorage:
            self.setRootPublicUntitled(decendentPi)
        else:
            print(f'type: {decendentPi.piBase.piType}')
            print(decendentPi.piInfluence.piDescendent)
            piPiTypePi = self.getCurrPiType(decendentPi.piBase.piType)
            piPiTypePi.addpiDescendent(decendentPi.piID)
            print('decendentPi.piInfluence.piDescendent')
    def getUserSubject(self, user: PiUser, relam='public') -> PiSubject:
        userSubjectRealmFile = user.realms[relam]
        userSubjectRealm = PiRealm(fileName=userSubjectRealmFile)
        userSubjectDomainFile = userSubjectRealm.domains['untitled']
        userSubjectDomain = PiDomain(fileName=userSubjectDomainFile)
        userSubjectFile = userSubjectDomain.subjects['untitled']
        userSubject = PiSubject(fileName=userSubjectFile)
        return userSubject
    def setRootPublicUntitled(self, decendentPi: PiPi):
        self.rootUser.addpiDescendent(decendentPi.piID)
        publicRealmPathStr = self.rootUser.realms['public']
        publicRealm = PiRealm(fileName=publicRealmPathStr)
        publicRealm.addpiDescendent(decendentPi.piID)
        untitledDomainPathStr = publicRealm.domains['untitled']
        untitledDomain = PiDomain(fileName=untitledDomainPathStr)
        untitledDomain.addpiDescendent(decendentPi.piID)
        untitledSubjectPathStr = untitledDomain.subjects['untitled']
        untitledSubject = PiSubject(fileName=untitledSubjectPathStr)
        untitledSubject.addpiDescendent(decendentPi.piID)
        piPiTypeClasses = self.piPiClasses.piSpcPiTypeClasses
        print('dd',piPiTypeClasses)
        if type(decendentPi.piBody) == dict:
            pass
        elif decendentPi.piBase.piType in piPiTypeClasses.keys():
            specTypePathStr = untitledSubject.types[decendentPi.piBase.piType]
            specType = PiPi(fileName=specTypePathStr)
            specType.addpiDescendent(decendentPi.piID)