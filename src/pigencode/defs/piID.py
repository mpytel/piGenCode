import hashlib
from uuid import uuid4

def getMD5(inStr = "") -> str:
    return hashlib.md5(inStr.encode('utf-8')).hexdigest()

def getPiIDs(piPi = {}) -> tuple:
    piMD5 = getPiMD5(piPi['piIndexer'])
    piID = getPiID()
    return piID, piMD5

def getPiMD5(piIndexer = {}) -> str:
    retStr = ''
    inStr = piIndexer['piUser'] + piIndexer['piRealm']
    inStr += piIndexer['piDomain'] + piIndexer['piSubject']
    retStr = getMD5(inStr)
    return retStr

def getPiID() -> str:
    retStr = str(uuid4())
    return retStr
