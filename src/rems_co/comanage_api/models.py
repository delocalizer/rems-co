"""
Data Transfer Object (DTO) models for the COmanage Registry API.

These models mirror the exact request and response schema expected and returned
by the COmanage REST API. Field names and structure match COmanage conventions.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

# === Response Models ===


class CoPerson(BaseModel):
    """Minimal representation of a person in COmanage responses."""

    Id: int

    model_config = {"extra": "ignore"}


class CoPeopleResponse(BaseModel):
    """Response wrapper for /co_people.json queries."""

    ResponseType: Literal["CoPeople"] = "CoPeople"
    Version: Literal["1.0"] = "1.0"
    CoPeople: list[CoPerson]


class Identifier(BaseModel):
    """A person-linked identifier (e.g. eppn, oidcsub) in COmanage."""

    Id: int
    Identifier: str
    Type: str
    Person: CoPerson

    model_config = {"extra": "ignore"}


class IdentifiersResponse(BaseModel):
    """Response wrapper for /identifiers.json queries."""

    ResponseType: Literal["Identifiers"] = "Identifiers"
    Version: Literal["1.0"] = "1.0"
    Identifiers: list[Identifier]


class CoGroup(BaseModel):
    """Representation of a COmanage group."""

    Id: int
    Name: str

    model_config = {"extra": "ignore"}


class CoGroupsResponse(BaseModel):
    """Response wrapper for /co_groups.json queries."""

    ResponseType: Literal["CoGroups"] = "CoGroups"
    Version: Literal["1.0"] = "1.0"
    CoGroups: list[CoGroup]


class NewObjectResponse(BaseModel):
    """Response for object creation requests (e.g. new group)."""

    ResponseType: Literal["NewObject"] = "NewObject"
    Version: Literal["1.0"] = "1.0"
    ObjectType: str
    Id: int


class CoGroupMember(BaseModel):
    """Membership record within a COmanage group."""

    Id: int

    model_config = {"extra": "ignore"}


class CoGroupMemberResponse(BaseModel):
    """Response wrapper for /co_group_members.json queries."""

    ResponseType: Literal["CoGroupMembers"] = "CoGroupMembers"
    Version: Literal["1.0"] = "1.0"
    CoGroupMembers: list[CoGroupMember]


# === Request Models ===


class CoGroupPayload(BaseModel):
    """Payload describing a new group to be created."""

    Version: Literal["1.0"] = "1.0"
    CoId: int
    Name: str
    Description: str
    Open: bool = False
    Status: Literal["Active"] = "Active"


class AddGroupRequest(BaseModel):
    """Top-level request to create one or more groups."""

    RequestType: Literal["CoGroups"] = "CoGroups"
    Version: Literal["1.0"] = "1.0"
    CoGroups: list[CoGroupPayload]


class PersonRef(BaseModel):
    """Reference to a person in membership assignment."""

    Type: Literal["CO"] = "CO"
    Id: int


class CoGroupMemberPayload(BaseModel):
    """Payload for adding a person to a group, with optional expiration."""

    Version: Literal["1.0"] = "1.0"
    CoGroupId: int
    Person: PersonRef
    Member: bool = True
    ValidThrough: datetime | None


class AddGroupMemberRequest(BaseModel):
    """Top-level request to add members to one or more groups."""

    RequestType: Literal["CoGroupMembers"] = "CoGroupMembers"
    Version: Literal["1.0"] = "1.0"
    CoGroupMembers: list[CoGroupMemberPayload]
