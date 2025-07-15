"""
Custom exceptions for the REMS–COmanage bridge service.

Guiding principles:
- Use exceptions to signal broken assumptions or unrecoverable external state.
- Do NOT raise exceptions for expected outcomes (e.g. a group not existing),
  unless that violates the intended business flow.
- Centralizing domain-specific exceptions aids readability and logging.
"""

import httpx


class RemsCOError(Exception):
    """Base class for all REMS–COmanage bridge errors."""


class PersonNotFound(RemsCOError):
    """Raised when a person cannot be resolved in COmanage."""


class GroupCreationDisallowed(RemsCOError):
    """Raised when a group should not be created per policy."""


class MembershipNotFound(RemsCOError):
    """Raised when a person is not found in a group during removal."""


class COmanageAPIError(RemsCOError):
    """Raised when a low-level HTTP/API error occurs."""

    def __init__(self, detail: str, response: httpx.Response | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        self.response = response


class AlreadyMemberOfGroup(COmanageAPIError):
    """Raised when attempting to add someone who is already a group member."""
