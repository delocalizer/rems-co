"""
Domain models used internally by the REMS-COmanage bridge.

These are not the same as the API-facing DTO models used to communicate
with COmanage.
"""

from datetime import datetime

from pydantic import BaseModel


class ApproveEvent(BaseModel):
    """Entitlement approval event from REMS."""

    application: int
    resource: str
    user: str
    mail: str
    end: datetime | None


class RevokeEvent(BaseModel):
    """Entitlement revocation event from REMS."""

    application: int
    resource: str
    user: str
    mail: str
    end: datetime | None


class Person(BaseModel):
    """A known person in COmanage."""

    id: int
    email: str
    identifier: str


class Group(BaseModel):
    """A COmanage group."""

    id: int
    name: str
