import datetime
from sys import stdout
from re import compile as reCompile
from pathlib import Path
from copy import deepcopy
from pi.defs.logIt import printIt, lable, logIt, cStr, color
from pi.defs.piFileIO import getKeyItem, savePiLn, writeRC, setKeyItem, delKey
from pi.defs.piTouch import piPathLn
from pi.piClasses.piUser import PiBase, PiPi, PiUser
from pi.piClasses.piTopic import PiTopic
from pi.classes.piCurrentIndexer import PiCurrentIndexer
import readline
readline.parse_and_bind('tab: compleat')
readline.parse_and_bind('set editing-mode vi')


debugOff = lable.ABORTPRT # ^(.*)(printIt)(.*debugOff\)), $1# printIt$2
debugOn = lable.DEBUG
debugSet = debugOff
#debugSet = debugOn

#imported - self.piIndexerTypes = ["user", "realm", "domain", "subject"]
curserUpLineCode = "\033[1A"

class PiPiPackageSystem():
    '''This will be replaced'''
    def __init__(self) -> None:
        self.pis = {}
        self.piCurrentIndexer = PiCurrentIndexer()
        self.piIndexerTypes = self.piCurrentIndexer.piIndexerTypes
        self._sysCheck()
    def _sysCheck(self):
        try:
            self.piRootUser =  self.piCurrentIndexer.rootUser
            self.piCurrUser = self.piCurrentIndexer.User
            if self.piRootUser:
                pass
                #print('in _sysCheck')
                # self.chkRootUserTimeOut()
        except:
        # Is pis with piRootUser established
            if not self.piRootUser: self._establishedRootUser()
        #   2)  Check is a piUser other then piRootUser is presen
            if self.piRootUser:
                pass
                #self.chkRootUserTimeOut()
            else:
                print(self.piRootUser==None)
                print("Root user not set.")
    def chkRootUserTimeOut(self):
        rootUserPathStr = getKeyItem('rootUser')
        rootUserName = self.piCurrentIndexer.rootUser.piBase.piTitle
        currUserPathStr = self.piCurrentIndexer.rootUser.piBody.users[self.piCurrentIndexer.rootUser.piBody.user]
        if rootUserPathStr == currUserPathStr:
            # look for another user in session with piRootUser is expired. 5 min sesson time.
            lastRootSessonChk = getKeyItem('lastRootSessonChk', self.piRootUser.piTouch.piTouchDate)
            if lastRootSessonChk:
                #currRootSessonChk = self.piRootUser.piTouch.piTouchDate
                lastChk = datetime.datetime.strptime(lastRootSessonChk,"%Y-%m-%d %H:%M:%S.%f")
                currChk = datetime.datetime.now()
                diffMin = (currChk - lastChk).total_seconds() / 60.0
                if diffMin > 50:
                    printIt("Root user access has expired.\n",lable.WARN)
                    print(cStr('Choose a current user, or create a new user.',cVal=color.UNDERLINE))
                    self.piCurrentIndexer.setUser(rootUserName)
            else:
                print('here in PiPiPackageSystem.chkRootUserTimeOut()')
                self.piCurrentIndexer.setUser(rootUserName)
    def _getPiRootUserPath(self) -> Path:
        piRootUserPathStr = getKeyItem('rootUser')
        return Path(piRootUserPathStr)
    def getCurrTypeItemPiBase(self, setTypeName: str, setTypeTitle: str = '') -> PiBase:
        '''Returns the piBase for the piIndexer or type item selected or created to be current.'''
        thePiBase = None
        printIt(f'type only item: type: {setTypeName}, title: {setTypeTitle}',debugSet)
        currPiFiles: dict = self.piCurrentIndexer.getUserTypeFileList(setTypeName)[1]
        printIt(f'currPiFiles: {str(setTypeName)}',debugSet)
        if currPiFiles:
            currPiTitelLists = list(currPiFiles.keys())
            newTypeTitle = {}
            picklistID = thePiIndex = 0
            if not setTypeTitle:
                if setTypeName == self.piIndexerTypes[1]: # new realms are not allowed
                    picklistStr = ""
                    minPiIndex = 1
                else:
                    picklistStr = f'{str(thePiIndex)}. Create new {setTypeName}\n'
                    minPiIndex = 0
                # Make list of users
                for piTitle in currPiFiles.keys():
                    thePiIndex += 1
                    newTypeTitle[str(thePiIndex)] = piTitle
                    picklistStr += f'{str(thePiIndex)}. {piTitle}\n'
                picklistID = -1
                print(picklistStr[:-1])
                promptStr = f'Choose {setTypeName} from list (cancel with any other entry): '
                newIDStr = input(promptStr)
                if newIDStr.isnumeric():
                    newID = int(newIDStr)
                    if thePiIndex >= newID >= minPiIndex: # and newID <= thePiIndex:
                        picklistID = newID
            if picklistID == 0:
                # create new piBase and set the pi index
                picklistStr = f'New {setTypeName} title: '
                newPiTitle = ""
                while not newPiTitle:
                    print(f'{" "*80}{curserUpLineCode}', end='\x1b[1K\r')
                    newPiTitle = input(picklistStr)
                    if newPiTitle in currPiTitelLists:
                        print(f'{" "*80}{curserUpLineCode}', end='\x1b[1K\r')
                        print(f'{newPiTitle} exists.')
                        newPiTitle = ""
                picklistStr = f'New {setTypeName} short discription: '
                newPiSD = ""
                print(f'{" "*80}{curserUpLineCode}', end='\x1b[1K\r')
                while not newPiSD: newPiSD = input(picklistStr)
                thePiBase: PiBase = PiBase(setTypeName, newPiTitle, newPiSD)
            elif picklistID > 0:
                # Set to existing piInderer pi
                # this need to be changed tom go througjh piAPIServer
                thePiBase: PiBase = PiBase(setTypeName,newTypeTitle[str(picklistID)],'')
        else:
            printIt(f'{setTypeName} is not a {setTypeTitle}',lable.WARN)
        return thePiBase
    def setCurrDomain(self):
        pass
    def setCurrSubject(self):
        pass
    def _getPiPath(self, thePi: PiPi) -> Path:
        pisDir = Path(getKeyItem('pisDir'))
        piTypeID = self._getTypeID(thePi)
        piPath = pisDir.joinpath(thePi.piIndexer.piUser,
                                  thePi.piIndexer.piRealm,
                                  thePi.piIndexer.piDomain,
                                  thePi.piIndexer.piSubject,
                                  piTypeID)
        piPath.mkdir(mode=511,parents=True,exist_ok=True)
        piPath =piPath.joinpath(f'{thePi.piID}.json')
        # print("_getPiPath: ", piPath)
        return piPath
    def _getTypeID(self, thePi: PiPi) -> str:
        thePiUserTypes: dict = self.piCurrUser.piBody.piTypeFiles
        thePiTypePath = Path(thePiUserTypes[self.piIndexerTypes[4]])
        thePiType = PiTopic(fileName=thePiTypePath)
        thePiTypeFiles: dict = thePiType.piBody.piFiles
        thePiTypeFileName = Path(thePiTypeFiles[thePi.piBase.piType]).name
        return thePiTypeFileName.split('.')[0]
    def setPiIdexerType(self, thePiID, piType, thePiIndexID):
        # THIS SEEMS WRONG AND ONLY USED IN C OPTIPN FLAGE CPE3
        rootUserFileName = getKeyItem("rootUser")
        rootUser = PiUser(fileName=rootUserFileName)
        theLink = rootUser.piBody.piCurrIndexer.piUser
        PiPiLnDir = rootUser.piBody.piLinkDir
        currUserFileName = piPathLn(theLink,PiPiLnDir)
        currUser = PiUser(fileName=currUserFileName)
        PiPiLnDir = currUser.piBody.piLinkDir
        targetPiFileName = piPathLn(thePiID,PiPiLnDir)
        targetPi = PiPi(fileName=targetPiFileName)
        if piType == self.piIndexerTypes[1]: targetPi.piIndexer.piRealm = thePiIndexID
        if piType == self.piIndexerTypes[2]: targetPi.piIndexer.piDomain = thePiIndexID
        if piType == self.piIndexerTypes[3]: targetPi.piIndexer.piSubject = thePiIndexID
        print(piType,thePiIndexID)
        targetPi.piIndexer.setPiMD5()
        # set the current indexer in rootUser and currUser
        rootUser.piBody.piCurrIndexer = targetPi.piIndexer
        currUser.piBody.piCurrIndexer = targetPi.piIndexer
        # update modified and tuch dates
        theDate = str(datetime.datetime.now())
        targetPi.piTouch.piModificationDate = theDate
        targetPi.piTouch.piTouchDate = theDate
        rootUser.piTouch.piModificationDate = theDate
        rootUser.piTouch.piTouchDate = theDate
        currUser.piTouch.piModificationDate = theDate
        currUser.piTouch.piTouchDate = theDate
        targetPi.piSave()
        savePiLn(Path(currUser.piBody.piLinkDir).joinpath(targetPi.piID),Path(targetPi.piJsonFilePath))
        # save  rootUser and currUser and update their soft-links
        rootUser.piSave()
        savePiLn(Path(rootUser.piBody.piLinkDir).joinpath(rootUser.piID),Path(rootUser.piJsonFilePath))
        currUser.piSave()
        # print("T02", rootUser.piBase.piTitle)
        savePiLn(Path(currUser.piBody.piLinkDir).joinpath(currUser.piID),Path(currUser.piJsonFilePath))