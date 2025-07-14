import fnmatch

from rems_co.comanage_api.client import CoManageClient
from rems_co.models import ApproveEvent
from rems_co.settings import settings


def should_create_group(resource: str) -> bool:
    """
    Helper: are we allowed to create missing group for this resource?
    """
    return any(
        fnmatch.fnmatch(resource, pattern)
        for pattern in settings.create_groups_for_resources
    )


def handle_approve(event: ApproveEvent) -> None:
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


def handle_revoke(event: ApproveEvent) -> None:
    api = CoManageClient()
    person = api.resolve_person_by_email_and_uid(email=event.mail, uid=event.user)
    group = api.get_group_by_name(event.resource)

    if group:
        api.remove_person_from_group(person_id=person.id, group_id=group.id)
    else:
        print(
            f"[INFO] Group '{event.resource}' not found during revoke. No action taken."
        )
