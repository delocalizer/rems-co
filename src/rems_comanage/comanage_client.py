"""
COmanage REST API Client

Utilities for interfacing with COmanage REST API.
The function names try to match the remote API method and paths.

From: https://github.com/ADA-ANU/rems/blob/master/src/clj/rems/ext/comanage.clj
"""

import logging
from typing import Optional, Dict, Any, List
from functools import wraps
from urllib.parse import urljoin
import requests
from requests.auth import HTTPBasicAuth
from pydantic import BaseModel, Field, HttpUrl, validator


logger = logging.getLogger(__name__)


class COmanageConfig(BaseModel):
    """Configuration for COmanage API client with validation."""

    registry_url: HttpUrl = Field(..., description="COmanage registry base URL")
    core_api_userid: str = Field(..., min_length=1, description="API user ID")
    core_api_key: str = Field(..., min_length=1, description="API key")
    registry_coid: str = Field(..., min_length=1, description="Registry CO ID")
    connect_timeout: float = Field(
        default=9.5, gt=0, description="Connection timeout in seconds"
    )
    read_timeout: float = Field(
        default=9.5, gt=0, description="Read timeout in seconds"
    )

    class Config:
        env_prefix = "COMANAGE_"
        extra = "forbid"
        allow_mutation = False

    @validator("registry_url")
    def normalize_registry_url(cls, v):
        return str(v).rstrip("/")


def handle_api_errors(func):
    """Decorator to handle common API errors and logging."""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except requests.RequestException as e:
            logger.error(f"COmanage API error in {func.__name__}: {e}")
            raise

    return wrapper


class COmanageClient:
    """COmanage REST API client with clean, functional interface."""

    def __init__(self, config: COmanageConfig):
        self.config = config
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(config.core_api_userid, config.core_api_key)
        self.session.timeout = (config.connect_timeout, config.read_timeout)

    def _url(self, path: str) -> str:
        """Build complete URL from path."""
        return urljoin(self.config.registry_url + "/", path.lstrip("/"))

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        expected_status: int = 200,
    ) -> Optional[Dict]:
        """Make HTTP request with error handling."""
        response = self.session.request(
            method, self._url(path), params=params, json=json_data
        )

        if response.status_code == expected_status:
            return response.json() if response.content else None
        elif response.status_code == 204:
            return None
        else:
            raise requests.HTTPError(f"HTTP {response.status_code}", response=response)

    @handle_api_errors
    def get_group_member_id(self, co_group_id: str, co_person_id: str) -> Optional[str]:
        """Get COmanage group member id for a given co-group-id."""
        response = self._request(
            "GET", "co_group_members.json", {"cogroupid": co_group_id}
        )
        members = response.get("CoGroupMembers", []) if response else []
        matching = [m for m in members if m.get("Person", {}).get("Id") == co_person_id]
        return matching[0].get("Id") if matching else None

    @handle_api_errors
    def get_person_id(self, user_id: str) -> Optional[str]:
        """Get COmanage person id for a given user identifier."""
        response = self._request(
            "GET",
            "co_people.json",
            {"coid": self.config.registry_coid, "search.identifier": user_id},
        )
        people = response.get("CoPeople", []) if response else []
        return people[0].get("Id") if people else None

    @handle_api_errors
    def delete_org_identity(self, org_identity_id: str) -> str:
        """Delete COmanage organisational entity."""
        self._request(
            "DELETE",
            f"org_identities/{org_identity_id}.json",
            {"coid": self.config.registry_coid},
        )
        return org_identity_id

    @handle_api_errors
    def unlink_orcid(self, org_link: Dict[str, Any]) -> Optional[str]:
        """Remove orcid link from user by unlinking then deleting the COmanage organisation identity."""
        if not (org_link_id := org_link.get("Id")):
            return None

        self._request(
            "DELETE",
            f"co_org_identity_links/{org_link_id}.json",
            {"coid": self.config.registry_coid},
        )

        return (
            self.delete_org_identity(org_identity_id)
            if (org_identity_id := org_link.get("OrgIdentityId"))
            else None
        )

    @handle_api_errors
    def get_org_identity_links(self, co_person_id: str) -> List[Dict[str, Any]]:
        """Get COmanage organisation identity links for a user."""
        response = self._request(
            "GET",
            "co_org_identity_links.json",
            {"coid": self.config.registry_coid, "copersonid": co_person_id},
        )
        return response.get("CoOrgIdentityLinks", []) if response else []

    @handle_api_errors
    def get_orcid_identifiers(self, org: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get orcid identifiers (if any) from the org identity id."""
        if not (org_identity_id := org.get("OrgIdentityId")):
            return None

        response = self._request(
            "GET",
            "identifiers.json",
            {"coid": self.config.registry_coid, "orgidentityid": org_identity_id},
        )

        if not response:
            return None

        identifiers = response.get("Identifiers", [])
        enrolled_orcids = [
            i
            for i in identifiers
            if "orcid" in i.get("Type", "").lower()
            and "http" not in i.get("Identifier", "")
        ]

        return org if enrolled_orcids else None

    @handle_api_errors
    def get_group_id(self, resource_id: str) -> Optional[str]:
        """Get COmanage group id for a given entitlement resource id."""
        response = self._request(
            "GET", "co_groups.json", {"coid": self.config.registry_coid}
        )
        if not response:
            return None

        groups = response.get("CoGroups", [])
        matching = [g for g in groups if resource_id in g.get("Name", "")]
        return matching[0].get("Id") if matching else None

    @handle_api_errors
    def create_or_update_permissions(self, post_data: Dict[str, Any]) -> Optional[str]:
        """Add member to COmanage group."""
        response = self._request(
            "POST", "co_group_members.json", json_data=post_data, expected_status=201
        )
        return response.get("Id") if response else None

    @handle_api_errors
    def delete_identifier(self, identifier_id: str) -> str:
        """Delete a COmanage identifier."""
        self._request("DELETE", f"identifiers/{identifier_id}.json")
        return identifier_id

    @handle_api_errors
    def delete_permissions(self, co_group_member_id: str) -> str:
        """Delete a COmanage group member id."""
        self._request("DELETE", f"co_group_members/{co_group_member_id}.json")
        return co_group_member_id

    @handle_api_errors
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a given user's identities."""
        response = self._request(
            "GET",
            f"api/co/{self.config.registry_coid}/core/v1/people",
            {"identifier": user_id},
        )
        return response.get("0") if response else None

    @handle_api_errors
    def get_terms_and_conditions(self) -> Optional[Dict[str, Any]]:
        """Get all of the terms and conditions for the CO."""
        return self._request(
            "GET", "co_terms_and_conditions.json", {"coid": self.config.registry_coid}
        )

    @handle_api_errors
    def get_accepted_terms_and_conditions(
        self, person_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a given user's accepted terms and conditions."""
        return self._request(
            "GET",
            "co_t_and_c_agreements.json",
            {"copersonid": str(person_id), "coid": self.config.registry_coid},
        )

    @handle_api_errors
    def post_terms_and_conditions_acceptance(
        self, post_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """POST terms and conditions agreements to COmanage."""
        return self._request(
            "POST",
            "co_t_and_c_agreements.json",
            {"coid": self.config.registry_coid},
            post_data,
            expected_status=201,
        )


# Functional interface
def create_client(
    registry_url: str, core_api_userid: str, core_api_key: str, registry_coid: str
) -> COmanageClient:
    """Create a COmanage client with configuration."""
    return COmanageClient(
        COmanageConfig(
            registry_url=registry_url,
            core_api_userid=core_api_userid,
            core_api_key=core_api_key,
            registry_coid=registry_coid,
        )
    )


def create_client_from_env() -> COmanageClient:
    """Create a COmanage client from environment variables."""
    return COmanageClient(COmanageConfig())
