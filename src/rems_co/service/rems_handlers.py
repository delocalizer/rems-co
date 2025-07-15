"""
Business logic for handling REMS entitlement events.

Translates ApproveEvent and RevokeEvent objects into actions on COmanage,
such as creating groups and managing memberships.
"""

import fnmatch
import logging

from rems_co.comanage_api.client import CoManageClient
from rems_co.exceptions import (
    AlreadyMemberOfGroup,
    COmanageAPIError,
    MembershipNotFound,
    PersonNotFound,
)
from rems_co.models import ApproveEvent, RevokeEvent
from rems_co.settings import settings

logger = logging.getLogger(__name__)


def should_create_group(resource: str) -> bool:
    """Return True if group creation is allowed for this resource."""
    return any(
        fnmatch.fnmatch(resource, pattern)
        for pattern in settings.create_groups_for_resources
    )


def handle_approve(event: ApproveEvent) -> None:
    """Handle an approval event by ensuring the group exists and adding the user."""
    api = CoManageClient()

    try:
        person = api.resolve_person_by_email_and_uid(email=event.mail, uid=event.user)
    except PersonNotFound as e:
        logger.warning(f"Skipping approval: {e}")
        return

    group = api.get_group_by_name(event.resource)

    if not group:
        if should_create_group(event.resource):
            logger.info(f"Creating new group for resource: {event.resource}")
            group = api.create_group(event.resource)
        else:
            logger.info(
                f"Group '{event.resource}' not found and creation not allowed by policy. Skipping."
            )
            return

    try:
        api.add_person_to_group(
            person_id=person.id, group_id=group.id, valid_through=event.end
        )
    except AlreadyMemberOfGroup:
        logger.info(
            f"User {person.id} already in group '{group.name}', skipping re-add."
        )
    except COmanageAPIError as e:
        logger.error(f"Unexpected error adding user to group: {e}")
        raise


def handle_revoke(event: RevokeEvent) -> None:
    """Handle a revocation event by removing the user from the group."""
    api = CoManageClient()

    try:
        person = api.resolve_person_by_email_and_uid(email=event.mail, uid=event.user)
    except PersonNotFound as e:
        logger.warning(f"Skipping revocation: {e}")
        return

    group = api.get_group_by_name(event.resource)

    if not group:
        logger.warning(
            f"Group '{event.resource}' not found during revoke for user {person.id}. Skipping."
        )
        return

    try:
        api.remove_person_from_group(person_id=person.id, group_id=group.id)
    except MembershipNotFound:
        logger.warning(
            f"Membership not found: user {person.id} not in group '{group.name}'. Skipping revoke."
        )
    except COmanageAPIError as e:
        logger.error(f"Unexpected error removing user from group: {e}")
        raise
