from datetime import datetime
from pydantic import BaseModel, Field, EmailStr
from typing import Any, Dict, List

class PiPrologBM(BaseModel):
    title: str
    version: str
    author: str
    copyright: str
class PiBaseBM(BaseModel):
    piType: str
    piTitle: str
    piSD: str
class PiDatesBM(BaseModel):
    piCreationDate: str
    piModificationDate: str
    piTouchDate: str
class PiIndexerBM(BaseModel):
    piMD5: str
    piUser: str
    piRealm: str
    piDomain: str
    piSubject: str
class PiInfluencesBM(BaseModel):
    piPrecedent: List
    piDescendent: List
class PiUserProfileBM(BaseModel):
    username: str
    full_name: str
    email: str
    hashed_password: str
    userToken: str
    scope: str
    grants: list
    client_id: str
    client_secret: str
    disabled: bool
class PiUserBodyBM(BaseModel):
    piUserProfile: PiUserProfileBM
    realm: str
    realms: dict
    user: str
    users: dict
    piIDIndex: str
class PiUserBaseBM(PiBaseBM):
    piType: str
    piTitle: str
    piSD: str
    piUserProfile: PiUserProfileBM
class PiTypeBodyBM(BaseModel):
    piFiles: dict
class PiBM(BaseModel):
    piProlog: PiPrologBM
    piBase: PiBaseBM
    piID: str
    piTouch: PiDatesBM
    piIndexer: PiIndexerBM
    piInfluence: PiInfluencesBM
    piBody: Dict[str, Any]
class PiUserBM(BaseModel):
    piProlog: PiPrologBM
    piBase: PiBaseBM
    piID: str
    piTouch: PiDatesBM
    piIndexer: PiIndexerBM
    piInfluence: PiInfluencesBM
    piBody: PiUserBodyBM
class PiTypeBM(BaseModel):
    piProlog: PiPrologBM
    piBase: PiBaseBM
    piID: str
    piTouch: PiDatesBM
    piIndexer: PiIndexerBM
    piInfluence: PiInfluencesBM
    piBody: PiTypeBodyBM
class PI(BaseModel):
    pi: PiBM
    loadDate: datetime

class UserSchema(BaseModel):
    username: str = Field(...)
    fullname: str = Field(...)
    email: EmailStr = Field(...)
    password: str = Field(...)
    class Config:
        json_schema_extra = {
            "example": {
                "username": "piDev",
                "fullname": "pi dev",
                "email": "pi@pidev.com",
                "password": "pi77dev"
            }
        }

class UserLoginSchema(BaseModel):
    username: str = Field(...)
    password: str = Field(...)

    class Config:
        json_schema_extra = {
            "example": {
                "username": "piDev",
                "password": "pi77dev"
            }
        }
