"""
Business logic for handling REMS entitlement events.

Translates ApproveEvent and RevokeEvent objects into actions on COmanage,
such as creating groups and managing memberships.
"""

import fnmatch

from rems_co.comanage_api.client import CoManageClient
from rems_co.models import ApproveEvent, RevokeEvent
from rems_co.settings import settings


def should_create_group(resource: str) -> bool:
    """Return True if group creation is allowed for this resource."""
    return any(
        fnmatch.fnmatch(resource, pattern)
        for pattern in settings.create_groups_for_resources
    )


def handle_approve(event: ApproveEvent) -> None:
    """Handle an approval event by ensuring the group exists and adding the user."""
    api = CoManageClient()
    person = api.resolve_person_by_email_and_uid(email=event.mail, uid=event.user)
    group = api.get_group_by_name(event.resource)

    if not group:
        if should_create_group(event.resource):
            group = api.create_group(event.resource)
        else:
            print(
                f"[INFO] Group '{event.resource}' not found and creation not allowed by pattern policy."
            )
            return

    api.add_person_to_group(
        person_id=person.id, group_id=group.id, valid_through=event.end
    )


def handle_revoke(event: RevokeEvent) -> None:
    """Handle a revocation event by removing the user from the group."""
    api = CoManageClient()
    person = api.resolve_person_by_email_and_uid(email=event.mail, uid=event.user)
    group = api.get_group_by_name(event.resource)

    if group:
        api.remove_person_from_group(person_id=person.id, group_id=group.id)
    else:
        print(
            f"[INFO] Group '{event.resource}' not found during revoke. No action taken."
        )
