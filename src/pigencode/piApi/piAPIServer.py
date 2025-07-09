# piAPIServer functions - synced from existing code
import logging
from datetime import datetime
from hashlib import sha256
from fastapi import FastAPI, Body, Depends, Request, Response, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated
from pi.defs.piFileIO import getKeyItem
from pi.defs.piTouch import isPiID
from pathlib import Path
from pi.defs.logIt import printIt, lable
from pi.classes.piCurrentIndexer import PiCurrentIndexer
from pi.piClasses.piPiClasses import PiPiClasses
from pi.piWords.piWords import isWord
from pi.piClasses.piBase import PiBase
from pi.piClasses.piIndexer import PiIndexer
from pi.piClasses.piPi import PiPi
from pi.piClasses.piTopic import PiTopic
from pi.piClasses.piTrie import PiTrie, PiTrieBody, PiTrieNode
from pi.piClasses.piUser import PiUser, PiUserProfile
from pi.piApi.piAPIModel import *
from pi.piApi.piAuth.piHandler import sign_jwt
from pi.piApi.piAuth.piBearer import PiJWTBearer
from re import compile as reCompile

debugOff = lable.ABORTPRT # ^(.*)(printIt)(.*debugSet\)), $1# printIt$2
debugOn = lable.DEBUG
debugSet = debugOff
pisDir = Path(getKeyItem("pisDir"))
filename = str(pisDir.joinpath("piApi.log"))
log_handler = logging.FileHandler(filename)
NEWPI = 30
logging.Logger.newPi = newPiLog
CNGPI = 30
logging.Logger.chgPi = chgPiLog
apiLogger = setup_log("piAPI_2")
app = FastAPI()
origins = [
piCurrentIndexer = PiCurrentIndexer()
piPiClasses = PiPiClasses()
piASCILogo = '''
piASCILogo2 = '''

def newPiLog(self, message, *args, **kws):
    self.log(NEWPI, message, *args, **kws)

def chgPiLog(self, message, *args, **kws):
    self.log(NEWPI, message, *args, **kws)

def setup_log(name):
    logger = logging.getLogger(name)   # > set up a new name for a new logger
    logger.setLevel(logging.DEBUG)  # here is the missing line
    log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    log_handler.setLevel(logging.DEBUG)
    log_handler.setFormatter(log_format)
    logger.addHandler(log_handler)
    return logger


def do_something():
    apiLogger.debug("Doing something!")

def piAPILogNewPi(piType: str,piTitle: str,piSD: str):
    apiLogger.newPi("pi '"+piType+"' '"+piTitle+"' '"+piSD+"'")

def piAPILogChgPiIndex(piType: str,piTitle: str,piSD: str):
    apiLogger.chgPi("pi '"+piType+"' '"+piTitle)

def piAPILogInfo(piStr: str):
    apiLogger.info(piStr)


def PiUserBMFromPiPi(currPiUserPiPi: PiPi) -> PiUserBM:
    piBM:PiBM = PiBMFromPiPi(currPiUserPiPi)
    piUserBodyBM = PiUserBodyBM(**currPiUserPiPi.piBody.__dict__)
    piUserBM = PiUserBM(
        piProlog = piBM.piProlog,
        piBase = piBM.piBase,
        piID = currPiUserPiPi.piID,
        piTouch = piBM.piTouch,
        piIndexer = piBM.piIndexer,
        piInfluence = piBM.piInfluences,
        piBody = piUserBodyBM)
    return piUserBM

def PiTypeBMFromPiPi(currPiUserPiPi: PiPi) -> PiTypeBM:
    piBM:PiBM = PiBMFromPiPi(currPiUserPiPi)
    piTypeBodyBM = PiTypeBodyBM(**currPiUserPiPi.piBody.__dict__)
    piTypeBM = PiTypeBM(
        piProlog = piBM.piProlog,
        piBase = piBM.piBase,
        piID = currPiUserPiPi.piID,
        piTouch = piBM.piTouch,
        piIndexer = piBM.piIndexer,
        piInfluence = piBM.piInfluences,
        piBody = piTypeBodyBM)
    return piTypeBM

def PiBMFromPiPi(currPiUserPiPi: PiUser) -> PiBM:
    piPrologBM = PiPrologBM(
        title = currPiUserPiPi.piProlog.title,
        version = currPiUserPiPi.piProlog.version,
        author = currPiUserPiPi.piProlog.author,
        copyright = currPiUserPiPi.piProlog.copyright)
    piBaseBM = PiBaseBM(
        piType = currPiUserPiPi.piBase.piType,
        piTitle = currPiUserPiPi.piBase.piTitle,
        piSD = currPiUserPiPi.piBase.piSD)
    piDatesBM = PiDatesBM(
        piCreationDate = currPiUserPiPi.piTouch.piCreationDate,
        piModificationDate = currPiUserPiPi.piTouch.piModificationDate,
        piTouchDate = currPiUserPiPi.piTouch.piTouchDate)
    piIndexerBM = PiIndexerBM(
        piMD5 = currPiUserPiPi.piIndexer.piMD5,
        piUser = currPiUserPiPi.piIndexer.piUser,
        piRealm = currPiUserPiPi.piIndexer.piRealm,
        piDomain = currPiUserPiPi.piIndexer.piDomain,
        piSubject = currPiUserPiPi.piIndexer.piSubject)
    piInfluencesBM = PiInfluencesBM(
        piPrecedent = currPiUserPiPi.piInfluence.piPrecedent,
        piDescendent = currPiUserPiPi.piInfluence.piDescendent)
    piBM = PiBM(
        piProlog = piPrologBM,
        piBase = piBaseBM,
        piID = currPiUserPiPi.piID,
        piTouch = piDatesBM,
        piIndexer = piIndexerBM,
        piInfluence = piInfluencesBM,
        piBody = currPiUserPiPi.piBody.json())
    return piBM

def getRootPiUser() -> PiUser:
    rootUserFileName = getKeyItem("rootUser")
    rootUserPath = Path(rootUserFileName)
    return PiUser(fileName=rootUserPath)

def getCurrIndexer() -> PiIndexerBM:
    piCurrentIndexer = PiCurrentIndexer()
    currentIndexer: PiIndexer = piCurrentIndexer.currIndexer
    return PiIndexerBM(**currentIndexer.__dict__)

def getCurrPis(piType: str = "list") -> list[PI]:
    piCurrentIndexer = PiCurrentIndexer()
    outPis = []
    if piType == "list":
        outPis = piCurrentIndexer.getLatestPiList4CurrSubject(numOfPis=100)
        #outPis = piCurrentIndexer.getLatestPiList(numOfPis=100)
        # if outPis: printIt(f'len(outPis): {len(outPis)}',lable.DEBUG)
        # else: printIt(f'outPis: None',lable.DEBUG)
        # outPis = piCurrentIndexer.getLatestPiList(numOfPis=100)
    else:
        # here is the foced truncation of s from plural form.
        print('getCurrPis piType:',piType)
        _, piFiles = piCurrentIndexer.getUserTypeFileList(piType[:-1])
        if piFiles:
            for piFileName in piFiles.values():
                piFilePath = Path(piFileName)
                if piFilePath.is_file:
                    pi = piCurrentIndexer.piFromLink(piFilePath)[0]
                    outPis.append(pi.json())
        else:
            printIt(f'\'{piType}\' is not a type of pi.',lable.INFO)
    return outPis

def getTypeID(piType: str, currPiIndexer: PiIndexerBM) -> str:
    piCurrentIndexer = PiCurrentIndexer()
    currentIndexer: PiIndexer = piCurrentIndexer.currIndexer
    currPiUser: PiUser = piCurrentIndexer.piFromLink(currentIndexer.piUser)[0]
    thePiUserTypes: dict = currPiUser.piBody["piTypeFiles"]
    thePiTypePath = Path(thePiUserTypes["type"])
    thePiType = PiTopic(fileName=thePiTypePath)
    thePiTypeFiles: dict = thePiType.piBody.piFiles
    thePiTypeFileName = Path(thePiTypeFiles[piType]).name
    return thePiTypeFileName.split('.')[0]

def currIndexerAsTitels() -> PiIndexerBM:
    piCurrentIndexer = PiCurrentIndexer()
    piIndexerDict = piCurrentIndexer.currIndexerAsTitels().json()
    if piIndexerDict: aPiIndexerBM = PiIndexerBM(**piIndexerDict)
    else: aPiIndexerBM = None
    return aPiIndexerBM

def check_user(data: UserLoginSchema) -> PiUser:
    userPi:PiUser = None
    users = getRootPiUser().users
    for user in users.keys():
        if user == data.username:
            try:
                userPi = PiUser(fileName=users[user])
                hashed_password = userPi.piBody.piUserProfile.hashed_password
                username = userPi.piBody.piUserProfile.username
                data_hashed_password = sha256(data.password.encode('utf-8')).hexdigest()
                printIt(f'username: {username}',debugSet)
                printIt(f'user_hashed_password: {hashed_password}',debugSet)
                printIt(f'input_hashed_password: {data_hashed_password}',debugSet)
                if not userPi.piBase.piTitle == username: return None
                if not hashed_password == data_hashed_password: return None
                break
            except: return None
    return userPi

