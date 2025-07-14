from dataclasses import dataclass
from datetime import datetime


@dataclass
class ApproveEvent:
    application: int
    resource: str
    user: str
    mail: str
    end: datetime


@dataclass
class RevokeEvent:
    application: int
    resource: str
    user: str
    mail: str
    end: datetime


@dataclass
class User:
    id: int
    email: str


@dataclass
class Group:
    id: int
    name: str
