from datetime import datetime

from pydantic import BaseModel


class ApproveEvent(BaseModel):
    application: int
    resource: str
    user: str
    mail: str
    end: datetime


class RevokeEvent(BaseModel):
    application: int
    resource: str
    user: str
    mail: str
    end: datetime


class CoPerson(BaseModel):
    id: int
    email: str
    identifier: str


class CoGroup(BaseModel):
    id: int
    name: str
