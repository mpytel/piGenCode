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

import logging

debugOff = lable.ABORTPRT # ^(.*)(printIt)(.*debugSet\)), $1# printIt$2
debugOn = lable.DEBUG
debugSet = debugOff
#debugSet = debugOn

pisDir = Path(getKeyItem("pisDir"))

# set up logger for capturing all pis for all users to piApi.log
# Future don't record private or secret pis here.
filename = str(pisDir.joinpath("piApi.log"))
log_handler = logging.FileHandler(filename)
NEWPI = 30
logging.addLevelName(NEWPI, "NEWPI")
def newPiLog(self, message, *args, **kws):
    self.log(NEWPI, message, *args, **kws)
logging.Logger.newPi = newPiLog
CNGPI = 30
logging.addLevelName(NEWPI, "CNGPI")
def chgPiLog(self, message, *args, **kws):
    self.log(NEWPI, message, *args, **kws)
logging.Logger.chgPi = chgPiLog

def setup_log(name):
    logger = logging.getLogger(name)   # > set up a new name for a new logger
    logger.setLevel(logging.DEBUG)  # here is the missing line
    log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    log_handler.setLevel(logging.DEBUG)
    log_handler.setFormatter(log_format)
    logger.addHandler(log_handler)
    return logger

apiLogger = setup_log("piAPI_2")
apiLogger.info("piAPI restart have fun!!")
def do_something():
    apiLogger.debug("Doing something!")
def piAPILogNewPi(piType: str,piTitle: str,piSD: str):
    apiLogger.newPi("pi '"+piType+"' '"+piTitle+"' '"+piSD+"'")
def piAPILogChgPiIndex(piType: str,piTitle: str,piSD: str):
    apiLogger.chgPi("pi '"+piType+"' '"+piTitle)
def piAPILogInfo(piStr: str):
    apiLogger.info(piStr)

app = FastAPI()

# Configure CORS
origins = [
    "http://localhost:3000",  # Or whatever your React app's origin is
    "http://localhost", # for good measure
    "http://127.0.0.1:3000",
    "http://127.0.0.1",
    "*",  # DO NOT USE THIS IN PRODUCTION! Specify your exact origin.
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods, including OPTIONS
    allow_headers=["*"],  # Allows all headers
)

piCurrentIndexer = PiCurrentIndexer()
piPiClasses = PiPiClasses()

pis: dict = {} # cashed pis stored by userPiID, PiID, PI, pi
latestLoadDate: datetime = {}

piASCILogo = '''
             __
    ____    /__\\
   / __ \  ___
  / /_/ / /  /
 /  ___/ /  /
/__/    /__/
'''
piASCILogo2 = '''
        _____________________
       / ___________________/
      / /     /       /
     //     //      //
    /      //      //
         / /     / /
       /  /    /  /
      /  |    /  |
      \\_/     \\_/
'''
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
@app.get("/")
async def get_root():
    return("Pi API!")
@app.get("/currIndexerTitels",dependencies=[Depends(PiJWTBearer())])
async def get_currIndexerTitels():
    return currIndexerAsTitels()
@app.get("/currIndexer",dependencies=[Depends(PiJWTBearer())])
async def get_currIndexer(theCurrIndexer: Annotated[PiIndexerBM, Depends(getCurrIndexer)]):
    return theCurrIndexer
@app.get("/pis")
async def get_currUserPis(theCurrIndexer: Annotated[PiIndexerBM, Depends(getCurrIndexer)]):
# curl -X 'POST' \
#   'http://127.0.0.1:5000/pis' \
#   -H 'accept: application/json' \
#   -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoibSIsImV4cGlyZXMiOjE3NDEwMzk0NzEuODI3ODgwOX0.g_BAGll4Sp2KDndzH6XgziJ28eFYCdKTY5QZIO48b28' \
#   -H 'Content-Type: application/json'
    piCurrentIndexer = PiCurrentIndexer()
    outPis = piCurrentIndexer.getLatestPiList4CurrSubject(numOfPis=100)
    #outPis = piCurrentIndexer.getLatestPiList()
    return {"currIndexer": currIndexerAsTitels(), "pis": outPis}
@app.get("/pis/{piType}",dependencies=[Depends(PiJWTBearer())])
async def get_item(piType: str, request: Request):
    piCurrentIndexer = PiCurrentIndexer()
    # printIt(f'piType: {piType}',debugOn)
    outPis = "noPis Found"
    currPiTypes = ["list"] + piPiClasses.piIndexerSTypes
    # printIt(f'currPiTypes: {currPiTypes}',debugOn)
    if piType in currPiTypes:
        outPis = getCurrPis(piType)
    elif isPiID(piType):
        printIt(f'piFromLink({piType}: {piCurrentIndexer.piFromLink(piType)}',debugOn)
        outPis = [piCurrentIndexer.piFromLink(piType)[0]]
    else:
        printIt(f'piType(get): {piType}',debugOn)
        outPis = getCurrPis(piType)
    client_host = request.client.host
    piAPILogInfo(f'Get {piType}: {client_host}')
    return {"currIndexer": currIndexerAsTitels(), "pis": outPis}
@app.post("/pi/user", status_code=201,dependencies=[Depends(PiJWTBearer())])
async def add_piUser(piUserBase: PiUserBaseBM, request: Request):
    piCurrentIndexer = PiCurrentIndexer()
    printIt(f'app.post /pi/user {piUserBase}',debugSet)
    newPiUser = None
    client_host = request.client.host
    if piUserBase.piType == piCurrentIndexer.piPiClasses.piIndexerTypes[0]:
        piAPILogNewPi(piUserBase.piType,piUserBase.piTitle,piUserBase.piSD)
        piAPILogInfo(f'Post: {client_host}')
        piUserProfile = PiUserProfile(**piUserBase.piUserProfile.model_dump())
        newPiUser: PiUser = piCurrentIndexer.createNewUser(piUserBase.piTitle,piUserBase.piSD,piUserProfile)
    if newPiUser:
        printIt(f'{newPiUser.piBase.piType}, {newPiUser.piBase.piTitle} ({newPiUser.piID})', lable.NewPi)
        printIt(f'{newPiUser.piIndexer}',debugSet)
        piCurrentIndexer.setCurrentIndexer(newPiUser.piBase.piType,newPiUser.piBase.piTitle)
        newPiUser = newPiUser.json()
    else:
        raise HTTPException(
            status_code=status.HTTP_304_NOT_MODIFIED,
            detail=f'{piUserBase.piTitle} is not a valid {piUserBase.piType}.',
        )
    return newPiUser
@app.get("/piSpcWord",status_code=200,dependencies=[Depends(PiJWTBearer())])
async def get_PiWord(piBase: PiBaseBM, request: Request):
    piCurrentIndexer = PiCurrentIndexer()
    currIndexerAsTitels = piCurrentIndexer.currIndexerAsTitels()
    source = currIndexerAsTitels.piUser+' private'
    print('xxxxxo')
    spcWordTrie: PiTrie = piCurrentIndexer.getWordTrie(currIndexerAsTitels.piUser,'private','piSpcWord')
    piTrieBody: PiTrieBody = spcWordTrie.piBody
    piTrieNode: PiTrieNode = piTrieBody.search(piBase.piTitle)
    if piTrieNode.word == piBase.piTitle:
        found = True
    else:
        found = False
    client_host = request.client.host
    if found: condition = 'found'
    else: condition = 'not found'
    piAPILogInfo(f'{piBase.piTitle} {condition} in {source}: {client_host}')
    return {"source": source, "found": found}
@app.post("/pi", status_code=201,dependencies=[Depends(PiJWTBearer())])
async def piAPIPost(piBase: PiBaseBM, request: Request, response: Response):
    # This post should direct x different procedures.
    # 1. Add new pis when an piBase/piIndexer comiation dose not exist.
    # 2. Change the currPi when the piBase/piIndexer comiation dose not exist.
    # 3. Change the currPiIndexer if piSD not present and piType is a piIndexer field.
    piCurrentIndexer = PiCurrentIndexer()
    client_host = request.client.host
    newPiPi = None
    dashStr = "_"* 50
    printIt(f'{dashStr}',lable.INFO)
    if piBase.piSD: # Add new pi or change the currPi
        # print('piAPIPost',piBase)
        if piBase.piType in piCurrentIndexer.piPiClasses.piIndexerTypes[0:2]: # user and realm are immutable using pi post
            raise HTTPException(
                status_code=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION,
                detail=f'{piBase.piType}s are imutable.',
            )
        elif piBase.piType in piPiClasses.piIndexerTypes[2:]:
            thePiBase = PiBase(**piBase.model_dump())
            # here is the problem the new link written to  indexer need to be corrcted
            # WE NEED TO CREATE GENRIC TYPES BEFORE REQ IF TYPE NOT PRESENT.
            newPiPi = piCurrentIndexer.reqNewPi(thePiBase.piType, thePiBase.piTitle, thePiBase.piSD)
            if newPiPi:
                piCurrentIndexer.setCurrentIndexer(newPiPi.piBase.piType,newPiPi.piBase.piTitle)
                #print('currIndexerAsTitels_API',str(piCurrentIndexer.currIndexerAsTitels()))
                piAPILogNewPi(newPiPi.piBase.piType,newPiPi.piBase.piTitle,newPiPi.piBase.piSD)
                printIt(f'{newPiPi.piBase.piType}, {newPiPi.piBase.piTitle} ({newPiPi.piID})', lable.NewPi)
            else:
                raise HTTPException(
                    status_code=status.HTTP_302_FOUND,
                    detail=f'File {thePiBase.piType} {thePiBase.piTitle} exists.')
            piAPILogInfo(f'Post: {piBase.piType}')
            piAPILogInfo(f'Post: {client_host}')
        else: # build generic type
            thePiBase = PiBase(**piBase.model_dump())
            # printIt(f'thePiBase: {thePiBase}',debugSet)
            newPiPi = piCurrentIndexer.reqNewPi(thePiBase.piType, thePiBase.piTitle, thePiBase.piSD)
            if newPiPi:
                piAPILogNewPi(newPiPi.piBase.piType,newPiPi.piBase.piTitle,newPiPi.piBase.piSD)
                printIt(f'{newPiPi.piBase.piType}, {newPiPi.piBase.piTitle} ({newPiPi.piID})', lable.NewPi)
                piAPILogInfo(f'Post: {client_host}')
            else:
                raise HTTPException(
                    status_code=status.HTTP_302_FOUND,
                    detail=f'{thePiBase.piType} {thePiBase.piTitle} exists.',
                )
        if newPiPi:
            newPiPi = newPiPi.json()
        else:
            raise HTTPException(
                status_code=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION,
                detail=f'Not authorized to create {piBase.piType}',
            )
    else: # change currPiIndexer
        currIndexerSet: bool = piCurrentIndexer.setCurrentIndexer(piBase.piType, piBase.piTitle)
        if currIndexerSet:
            #piCurrentIndexer.piPiClasses.piIndexerTypes = ["user", "realm", "domain", "subject", "type"]
            piIndexerIndex = piCurrentIndexer.piPiClasses.piIndexerTypes.index(piBase.piType)
            indexerLevel = piIndexerIndex
            # print('indexerLevel:',indexerLevel)
            # print('piIndexerTypes:',piCurrentIndexer.piPiClasses.piIndexerTypes[indexerLevel+1])
            # print('piBase:',piBase)
            currPis = piCurrentIndexer.getLatestPiList4CurrSubject(numOfPis=100)
            #currPis = piCurrentIndexer.getLatestPiList(piType=piCurrentIndexer.piPiClasses.piIndexerTypes[piIndexerIndex-1], numOfPis=indexerLevel)
            if currPis:
                newPiPi = currPis[0]
                response.status_code = status.HTTP_202_ACCEPTED
                piAPILogNewPi(newPiPi.piBase.piType,newPiPi.piBase.piTitle,'')
                printIt(f'Current {newPiPi.piBase.piType} set to: {newPiPi.piBase.piTitle}',lable.INFO)
            else:
                response.status_code = status.HTTP_202_ACCEPTED
                # raise HTTPException(
                #     status_code=status.HTTP_304_NOT_MODIFIED,
                #     detail=f'Short description not proveded for {piBase.piType}, {piBase.piTitle}.',
                # )
        else:
            raise HTTPException(
                status_code=status.HTTP_304_NOT_MODIFIED,
                detail=f'{piBase.piTitle} is not a valid {piBase.piType}.',
            )
    return newPiPi
@app.get("/pi/chkLogin", dependencies=[Depends(PiJWTBearer())])
async def chk_login():
    rtnStr = ''
    # replace with db call, making sure to hash the password first
    #users.append(user)
    return 'logedIn-go'
@app.post("/user/signup", tags=["user"])
async def create_user(user: UserSchema = Body(...)):
    # replace with db call, making sure to hash the password first
    #users.append(user)
    return sign_jwt(user.username)
@app.post("/pi/login", tags=["user"])
async def user_login(user: UserLoginSchema = Body(...)):
# curl -X 'POST' \
#   'http://127.0.0.1:5000/pi/login' \
#   -H 'accept: application/json' \
#   -H 'Content-Type: application/json' \
#   -d '{
#   "username": "m",
#   "password": "p"
# }'
#  Returns:
# {"Authorization":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoibSIsImV4cGlyZXMiOjE3NDEwMzk0NzEuODI3ODgwOX0.g_BAGll4Sp2KDndzH6XgziJ28eFYCdKTY5QZIO48b28"}
    printIt(f'app.post /pi/login {user}',debugSet)
    userPi: PiUser = check_user(user)
    if userPi:
        userToken = sign_jwt(user.username)
        userPi.piBody.piUserProfile.userToken = userToken["Authorization"]
        userPi.piSave()
        return userToken
    return {
        "error": "Wrong login details!"
    }
@app.delete("/pi/{piID}",dependencies=[Depends(PiJWTBearer())])
async def delete_Pi(piID: str, request: Request):
    outPis = []
    if isPiID(piID):
        piCurrentIndexer = PiCurrentIndexer()
        outPis = piCurrentIndexer.rmPi(piID)
    else:
        raise HTTPException(
            status_code=status.HTTP_304_NOT_MODIFIED,
            detail=f'Invalied piID (UUID4): {piID}.',
        )
    return {"pis": outPis}
