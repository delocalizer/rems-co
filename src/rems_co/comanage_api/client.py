from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from rems_co.models import CoGroup, CoPerson
from rems_co.settings import settings


@dataclass
class APIError(Exception):
    detail: str


def retry_policy() -> Any:
    return retry(
        stop=stop_after_attempt(settings.comanage_retry_attempts),
        wait=wait_exponential(
            multiplier=settings.comanage_retry_backoff, min=1, max=30
        ),
        retry=retry_if_exception_type(httpx.RequestError),
        reraise=True,
    )


class CoManageClient:
    def __init__(self) -> None:
        self.base_url = str(settings.comanage_registry_url).rstrip("/")
        self.co_id = settings.comanage_coid
        self.client = httpx.Client(
            base_url=self.base_url,
            auth=(settings.comanage_api_userid, settings.comanage_api_key),
            timeout=settings.comanage_timeout_seconds,
        )

    @retry_policy()
    def _get(self, path: str, **kwargs: Any) -> httpx.Response:
        try:
            response = self.client.get(path, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            raise APIError(
                f"GET {path} failed: {e.response.status_code} - {e.response.text}"
            ) from e
        except httpx.RequestError as e:
            raise APIError(f"GET {path} failed: {e}") from e

    @retry_policy()
    def _post(self, path: str, json: dict) -> httpx.Response:
        try:
            response = self.client.post(path, json=json)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            raise APIError(
                f"POST {path} failed: {e.response.status_code} - {e.response.text}"
            ) from e
        except httpx.RequestError as e:
            raise APIError(f"POST {path} failed: {e}") from e

    @retry_policy()
    def _delete(self, path: str) -> httpx.Response:
        try:
            response = self.client.delete(path)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            raise APIError(
                f"DELETE {path} failed: {e.response.status_code} - {e.response.text}"
            ) from e
        except httpx.RequestError as e:
            raise APIError(f"DELETE {path} failed: {e}") from e

    def resolve_person_by_email_and_uid(self, email: str, uid: str) -> CoPerson:
        resp = self._get(
            "/co_people.json",
            params={"coid": self.co_id, "search.mail": email},
        )
        people = resp.json().get("CoPeople", [])

        for person in people:
            person_id = person.get("Id")
            if not person_id:
                continue

            try:
                identifiers_resp = self._get(
                    "/identifiers.json", params={"copersonid": person_id}
                ).json()
            except Exception:
                continue  # skip if this person's identifiers can't be loaded

            for ident in identifiers_resp.get("Identifiers", []):
                if ident.get("Identifier") == uid:
                    return CoPerson(id=person_id, email=email, identifier=uid)

        raise APIError(f"No matching CoPerson found with email={email} and uid={uid}")

    def get_group_by_name(self, name: str) -> CoGroup | None:
        resp = self._get("/co_groups.json", params={"coid": self.co_id})
        groups = resp.json().get("CoGroups", [])
        for g in groups:
            if g.get("Name") == name:
                return CoGroup(id=g["Id"], name=g["Name"])
        return None

    def create_group(self, name: str) -> CoGroup:
        payload = {
            "RequestType": "CoGroups",
            "Version": "1.0",
            "CoGroups": [
                {
                    "Version": "1.0",
                    "CoId": str(self.co_id),
                    "Name": name,
                    "Description": f"Group associated with read access to resource {name}",
                    "Open": False,
                    "Status": "Active",
                }
            ],
        }
        resp = self._post("/co_groups.json", json=payload)
        newg = resp.json()
        return CoGroup(id=newg["Id"], name=name)

    def add_person_to_group(
        self, person_id: int, group_id: int, valid_through: datetime
    ) -> None:
        valid_through_str = valid_through.strftime("%Y-%m-%dT%H:%M:%SZ")
        payload = {
            "RequestType": "CoGroupMembers",
            "Version": "1.0",
            "CoGroupMembers": [
                {
                    "Version": "1.0",
                    "CoGroupId": str(group_id),
                    "Person": {"Type": "CO", "Id": str(person_id)},
                    "Member": True,
                    "ValidThrough": valid_through_str,
                }
            ],
        }
        self._post("/co_group_members.json", json=payload)

    def remove_person_from_group(self, person_id: int, group_id: int) -> None:
        resp = self._get(
            "/co_group_members.json",
            params={"cogroupid": group_id, "copersonid": person_id},
        )
        members = resp.json().get("CoGroupMembers", [])

        if not members:
            raise APIError(
                f"No group membership found for person={person_id} and group={group_id}"
            )

        member_id = members[0]["Id"]
        delete_path = f"/co_group_members/{member_id}.json"
        self._delete(delete_path)
