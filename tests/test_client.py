from datetime import datetime

import pytest

from rems_co.comanage_api.client import APIError, CoManageClient
from rems_co.models import CoGroup, CoPerson


def test_resolve_person_by_email_and_uid_found(mocker):
    mock_get = mocker.patch.object(CoManageClient, "_get")

    # First _get: returns CoPeople list
    mock_get.side_effect = [
        mocker.Mock(json=lambda: {"CoPeople": [{"Id": 2988}, {"Id": 1234}]}),
        mocker.Mock(
            json=lambda: {
                "Identifiers": [
                    {"Identifier": "wrong-id", "Type": "eppn"},
                    {
                        "Identifier": "http://cilogon.org/serverI/users/2769",
                        "Type": "oidcsub",
                    },
                ]
            }
        ),
    ]

    client = CoManageClient()
    person = client.resolve_person_by_email_and_uid(
        email="foo.bar@baz.com", uid="http://cilogon.org/serverI/users/2769"
    )

    assert isinstance(person, CoPerson)
    assert person.id == 2988
    assert person.email == "foo.bar@baz.com"
    assert person.identifier == "http://cilogon.org/serverI/users/2769"


def test_resolve_person_by_email_and_uid_not_found(mocker):
    mock_get = mocker.patch.object(CoManageClient, "_get")
    mock_get.side_effect = [
        mocker.Mock(json=lambda: {"CoPeople": [{"Id": 2988}]}),
        mocker.Mock(json=lambda: {"Identifiers": [{"Identifier": "no-match"}]}),
    ]

    client = CoManageClient()
    with pytest.raises(APIError, match="No matching CoPerson found"):
        client.resolve_person_by_email_and_uid("a@b.com", "someuser")


def test_create_group_success(mocker):
    mock_post = mocker.patch.object(CoManageClient, "_post")
    mock_post.return_value.json.return_value = {
        "CoGroups": [{"Id": 42, "Name": "urn:test:xyz"}]
    }

    client = CoManageClient()
    group = client.create_group("urn:test:xyz")
    assert group.id == 42
    assert group.name == "urn:test:xyz"


def test_get_group_by_name_found(mocker):
    mock_get = mocker.patch.object(CoManageClient, "_get")
    mock_get.return_value.json.return_value = {
        "groups": [{"id": 1, "name": "urn:other"}, {"id": 2, "name": "urn:target"}]
    }

    client = CoManageClient()
    group = client.get_group_by_name("urn:target")
    assert isinstance(group, CoGroup)
    assert group.id == 2


def test_get_group_by_name_not_found(mocker):
    mock_get = mocker.patch.object(CoManageClient, "_get")
    mock_get.return_value.json.return_value = {"groups": []}

    client = CoManageClient()
    assert client.get_group_by_name("urn:missing") is None


def test_add_person_to_group(mocker):
    mock_post = mocker.patch.object(CoManageClient, "_post")
    client = CoManageClient()
    now = datetime(2025, 7, 20, 23, 59, 59)
    client.add_person_to_group(person_id=2988, group_id=1647, valid_through=now)

    payload = mock_post.call_args.kwargs["json"]
    assert payload["CoGroupMembers"][0]["Person"]["Id"] == "2988"
    assert payload["CoGroupMembers"][0]["CoGroupId"] == "1647"


def test_remove_person_from_group(mocker):
    mock_get = mocker.patch.object(CoManageClient, "_get")
    mock_delete = mocker.patch.object(CoManageClient, "_delete")

    mock_get.return_value.json.return_value = {"CoGroupMembers": [{"Id": 777}]}

    client = CoManageClient()
    client.remove_person_from_group(person_id=2988, group_id=1647)

    mock_delete.assert_called_once_with("/co_group_members/777.json")


def test_remove_person_from_group_missing(mocker):
    mock_get = mocker.patch.object(CoManageClient, "_get")
    mock_get.return_value.json.return_value = {"CoGroupMembers": []}

    client = CoManageClient()
    with pytest.raises(APIError, match="No group membership found"):
        client.remove_person_from_group(person_id=1, group_id=2)
