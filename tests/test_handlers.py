import pytest

from rems_co.exceptions import AlreadyMemberOfGroup, MembershipNotFound
from rems_co.models import ApproveEvent
from rems_co.service.rems_handlers import (
    handle_approve,
    handle_revoke,
    should_create_group,
)
from rems_co.settings import settings


@pytest.fixture
def example_event():
    return ApproveEvent(
        application=42,
        resource="urn:test:group123",
        user="user-oidc-123",
        mail="alice@example.org",
        end="2025-12-31T23:59:59Z",
    )


def test_should_create_group_default_allows_anything():
    settings.create_groups_for_resources = ["*"]
    assert should_create_group("urn:test:anygroup")


def test_should_create_group_restrictive_match():
    settings.create_groups_for_resources = ["urn:abc:*", "urn:def:specific"]
    assert should_create_group("urn:abc:foo")
    assert should_create_group("urn:def:specific")
    assert not should_create_group("urn:xyz:nomatch")


def test_handle_approve_creates_group_if_allowed(mocker, example_event):
    mock_client = mocker.patch(
        "rems_co.service.rems_handlers.CoManageClient"
    ).return_value
    mock_client.get_group_by_name.return_value = None
    mock_client.create_group.return_value.id = 101
    mock_client.create_group.return_value.name = example_event.resource

    settings.create_groups_for_resources = ["*"]

    handle_approve(example_event)

    mock_client.resolve_person_by_email_and_uid.assert_called_once_with(
        email="alice@example.org", uid="user-oidc-123"
    )
    mock_client.create_group.assert_called_once_with(example_event.resource)
    mock_client.add_person_to_group.assert_called_once()


def test_handle_approve_does_not_create_group_if_disallowed(
    mocker, example_event, caplog
):
    mock_client = mocker.patch(
        "rems_co.service.rems_handlers.CoManageClient"
    ).return_value
    mock_client.get_group_by_name.return_value = None

    settings.create_groups_for_resources = ["urn:abc:*"]  # restrictive pattern

    with caplog.at_level("INFO"):
        handle_approve(example_event)

    mock_client.create_group.assert_not_called()
    mock_client.add_person_to_group.assert_not_called()

    assert any("creation not allowed" in message for message in caplog.messages)


def test_handle_approve_existing_group(mocker, example_event):
    mock_client = mocker.patch(
        "rems_co.service.rems_handlers.CoManageClient"
    ).return_value
    mock_client.get_group_by_name.return_value.id = 101
    mock_client.get_group_by_name.return_value.name = example_event.resource

    handle_approve(example_event)

    mock_client.add_person_to_group.assert_called_once()


def test_handle_approve_skips_already_member(mocker, example_event, caplog):
    mock_client = mocker.patch(
        "rems_co.service.rems_handlers.CoManageClient"
    ).return_value
    mock_client.get_group_by_name.return_value.id = 101
    mock_client.get_group_by_name.return_value.name = example_event.resource
    mock_client.add_person_to_group.side_effect = AlreadyMemberOfGroup(
        "already a member"
    )

    with caplog.at_level("INFO"):
        handle_approve(example_event)

    assert any("already in group" in msg for msg in caplog.messages)


def test_handle_revoke_group_found(mocker, example_event):
    mock_client = mocker.patch(
        "rems_co.service.rems_handlers.CoManageClient"
    ).return_value
    mock_client.get_group_by_name.return_value.id = 101
    mock_client.get_group_by_name.return_value.name = example_event.resource

    handle_revoke(example_event)

    mock_client.remove_person_from_group.assert_called_once()


def test_handle_revoke_group_not_found(mocker, example_event, caplog):
    mock_client = mocker.patch(
        "rems_co.service.rems_handlers.CoManageClient"
    ).return_value
    mock_client.get_group_by_name.return_value = None

    with caplog.at_level("WARNING"):
        handle_revoke(example_event)

    mock_client.remove_person_from_group.assert_not_called()

    assert any(
        "Group 'urn:test:group123' not found during revoke" in message
        for message in caplog.messages
    )


def test_handle_revoke_skips_membership_not_found(mocker, example_event, caplog):
    mock_client = mocker.patch(
        "rems_co.service.rems_handlers.CoManageClient"
    ).return_value
    mock_client.get_group_by_name.return_value.id = 101
    mock_client.get_group_by_name.return_value.name = example_event.resource
    mock_client.remove_person_from_group.side_effect = MembershipNotFound(
        "not in group"
    )

    with caplog.at_level("WARNING"):
        handle_revoke(example_event)

    assert any("Membership not found" in msg for msg in caplog.messages)
