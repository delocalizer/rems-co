import pytest

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
    mocker, example_event, capsys
):
    mock_client = mocker.patch(
        "rems_co.service.rems_handlers.CoManageClient"
    ).return_value
    mock_client.get_group_by_name.return_value = None

    settings.create_groups_for_resources = ["urn:abc:*"]  # restrictive

    handle_approve(example_event)

    mock_client.create_group.assert_not_called()
    mock_client.add_person_to_group.assert_not_called()

    captured = capsys.readouterr()
    assert "creation not allowed" in captured.out


def test_handle_approve_existing_group(mocker, example_event):
    mock_client = mocker.patch(
        "rems_co.service.rems_handlers.CoManageClient"
    ).return_value
    mock_client.get_group_by_name.return_value.id = 101
    mock_client.get_group_by_name.return_value.name = example_event.resource

    handle_approve(example_event)

    mock_client.add_person_to_group.assert_called_once()


def test_handle_revoke_group_found(mocker, example_event):
    mock_client = mocker.patch(
        "rems_co.service.rems_handlers.CoManageClient"
    ).return_value
    mock_client.get_group_by_name.return_value.id = 101
    mock_client.get_group_by_name.return_value.name = example_event.resource

    handle_revoke(example_event)

    mock_client.remove_person_from_group.assert_called_once()


def test_handle_revoke_group_not_found(mocker, example_event, capsys):
    mock_client = mocker.patch(
        "rems_co.service.rems_handlers.CoManageClient"
    ).return_value
    mock_client.get_group_by_name.return_value = None

    handle_revoke(example_event)

    mock_client.remove_person_from_group.assert_not_called()
    captured = capsys.readouterr()
    assert "Group 'urn:test:group123' not found during revoke" in captured.out
