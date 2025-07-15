"""
Low-level client for interacting with the COmanage Registry API.

Encapsulates basic CRUD operations and lookups used by the REMS bridge.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from rems_co.comanage_api.models import (
    AddGroupMemberRequest,
    AddGroupRequest,
    CoGroupMemberPayload,
    CoGroupMemberResponse,
    CoGroupPayload,
    CoGroupsResponse,
    CoPeopleResponse,
    IdentifiersResponse,
    NewObjectResponse,
    PersonRef,
)
from rems_co.models import Group, Person
from rems_co.settings import settings


@dataclass
class APIError(Exception):
    """Raised on failure to interact with the COmanage API."""

    detail: str


HttpMethod = Literal["get", "post", "delete"]


def retry_policy() -> Any:
    """Return the retry policy for outgoing HTTP requests."""
    return retry(
        stop=stop_after_attempt(settings.comanage_retry_attempts),
        wait=wait_exponential(
            multiplier=settings.comanage_retry_backoff, min=1, max=30
        ),
        retry=retry_if_exception_type(httpx.RequestError),
        reraise=True,
    )


class CoManageClient:
    """Client for making authenticated calls to the COmanage Registry API."""

    def __init__(self) -> None:
        self.base_url = str(settings.comanage_registry_url).rstrip("/")
        self.co_id = settings.comanage_coid
        self.client = httpx.Client(
            base_url=self.base_url,
            auth=(settings.comanage_api_userid, settings.comanage_api_key),
            timeout=settings.comanage_timeout_seconds,
        )

    def _request(self, method: HttpMethod, path: str, **kwargs: Any) -> httpx.Response:
        """Perform an HTTP request with retries and error wrapping."""
        try:
            response = self.client.request(method=method, url=path, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            raise APIError(
                f"{method.upper()} {path} failed: {e.response.status_code} - {e.response.text}"
            ) from e
        except httpx.RequestError as e:
            raise APIError(f"{method.upper()} {path} failed: {e}") from e

    @retry_policy()
    def _get(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._request("get", path, **kwargs)

    @retry_policy()
    def _post(self, path: str, json: dict) -> httpx.Response:
        return self._request("post", path, json=json)

    @retry_policy()
    def _delete(self, path: str) -> httpx.Response:
        return self._request("delete", path)

    def resolve_person_by_email_and_uid(self, email: str, uid: str) -> Person:
        """Look up a person in COmanage by email and external UID."""
        resp = self._get(
            "/co_people.json", params={"coid": self.co_id, "search.mail": email}
        )
        people = CoPeopleResponse.model_validate(resp.json()).CoPeople

        for person in people:
            person_id = person.Id
            identifiers_resp = self._get(
                "/identifiers.json", params={"copersonid": person_id}
            )
            identifiers = IdentifiersResponse.model_validate(
                identifiers_resp.json()
            ).Identifiers

            for ident in identifiers:
                if ident.Identifier == uid:
                    return Person(id=person_id, email=email, identifier=uid)

        raise APIError(f"No matching Person found with email={email} and uid={uid}")

    def get_group_by_name(self, name: str) -> Group | None:
        """Return the COmanage group with the given name, if it exists."""
        resp = self._get("/co_groups.json", params={"coid": self.co_id})
        groups = CoGroupsResponse.model_validate(resp.json()).CoGroups
        for g in groups:
            if g.Name == name:
                return Group(id=g.Id, name=g.Name)
        return None

    def create_group(self, name: str) -> Group:
        """Create a new COmanage group."""
        payload = AddGroupRequest(
            CoGroups=[
                CoGroupPayload(
                    CoId=self.co_id,
                    Name=name,
                    Description=f"Group associated with read access to resource {name}",
                )
            ]
        ).model_dump(mode="json")

        resp = self._post("/co_groups.json", json=payload)
        new_group = NewObjectResponse.model_validate(resp.json())
        return Group(id=new_group.Id, name=name)

    def add_person_to_group(
        self, person_id: int, group_id: int, valid_through: datetime | None
    ) -> None:
        """Add a person to a group, optionally with expiration."""
        payload = AddGroupMemberRequest(
            CoGroupMembers=[
                CoGroupMemberPayload(
                    CoGroupId=group_id,
                    Person=PersonRef(Id=person_id),
                    Member=True,
                    ValidThrough=valid_through,
                )
            ]
        ).model_dump(mode="json", exclude_none=True)

        self._post("/co_group_members.json", json=payload)

    def remove_person_from_group(self, person_id: int, group_id: int) -> None:
        """Remove a person from a group, if they are a member."""
        resp = self._get(
            "/co_group_members.json",
            params={"cogroupid": group_id, "copersonid": person_id},
        )
        members = CoGroupMemberResponse.model_validate(resp.json()).CoGroupMembers

        if not members:
            raise APIError(
                f"No group membership found for person={person_id} and group={group_id}"
            )

        member_id = members[0].Id
        self._delete(f"/co_group_members/{member_id}.json")
