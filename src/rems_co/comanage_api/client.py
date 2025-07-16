"""
Low-level client for interacting with the COmanage Registry API.

Encapsulates basic CRUD operations and lookups.
"""

import logging
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
from rems_co.exceptions import (
    AlreadyMemberOfGroup,
    COmanageAPIError,
    MembershipNotFound,
    PersonNotFound,
)
from rems_co.models import Group, Person
from rems_co.settings import settings

logger = logging.getLogger(__name__)

HttpMethod = Literal["get", "post", "delete"]


def retry_policy() -> Any:
    """Return the retry policy for outgoing HTTP requests."""
    return retry(
        stop=stop_after_attempt(settings.comanage_retry_attempts),
        wait=wait_exponential(
            multiplier=settings.comanage_retry_backoff, min=1, max=10
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
        logger.debug(f"Initialized CoManageClient with base_url={self.base_url}")

    def _request(self, method: HttpMethod, path: str, **kwargs: Any) -> httpx.Response:
        """Perform an HTTP request with retries and error wrapping."""
        try:
            logger.debug(f"Request: {method.upper()} {path} {kwargs}")
            response = self.client.request(method=method, url=path, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error from COmanage: {e.response.status_code} {e.response.text}",
            )
            raise COmanageAPIError(
                detail=f"{method.upper()} {path} failed: {e.response.status_code} - {e.response.text}",
                response=e.response,
            ) from e
        except httpx.RequestError as e:
            logger.error(f"Request error from COmanage: {e}")
            raise

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
        logger.debug(f"Resolving person: email={email}, uid={uid}")
        resp = self._get(
            "/co_people.json", params={"coid": self.co_id, "search.mail": email}
        )
        people = CoPeopleResponse.model_validate(resp.json()).CoPeople
        if not people:
            raise PersonNotFound(f"No match for email={email}")

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
                    logger.info(f"Resolved person id={person_id} for uid={uid}")
                    return Person(id=person_id, email=email, identifier=uid)

        raise PersonNotFound(f"No match for email={email} and uid={uid}")

    def get_group_by_name(self, name: str) -> Group | None:
        """Return the COmanage group with the given name, if it exists."""
        logger.debug(f"Looking up group by name: {name}")
        resp = self._get("/co_groups.json", params={"coid": self.co_id})
        groups = CoGroupsResponse.model_validate(resp.json()).CoGroups
        for g in groups:
            if g.Name == name:
                logger.info(f"Found group: {g.Name} (id={g.Id})")
                return Group(id=g.Id, name=g.Name)
        logger.info(f"Group not found: {name}")
        return None

    def create_group(self, name: str) -> Group:
        """Create a new COmanage group."""
        logger.info(f"Creating group: {name}")
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
        logger.info(f"Adding person {person_id} to group {group_id}")
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

        try:
            self._post("/co_group_members.json", json=payload)
        except COmanageAPIError as e:
            if (
                e.response is not None
                and e.response.status_code == 403
                and "already member" in e.response.reason_phrase.lower()
            ):
                raise AlreadyMemberOfGroup(
                    f"Person {person_id} already in group {group_id}",
                    response=e.response,
                ) from e
            raise

    def remove_person_from_group(self, person_id: int, group_id: int) -> None:
        """Remove a person from a group, if they are a member."""
        logger.info(f"Removing person {person_id} from group {group_id}")
        resp = self._get(
            "/co_group_members.json",
            params={"cogroupid": group_id, "copersonid": person_id},
        )
        members = CoGroupMemberResponse.model_validate(resp.json()).CoGroupMembers

        if not members:
            raise MembershipNotFound(f"Person {person_id} not in group {group_id}")
        for member in members:
            logger.info(f"Found membership id={member.Id}, removing")
            self._delete(f"/co_group_members/{member.Id}.json")
