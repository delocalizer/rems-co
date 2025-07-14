import pytest

from rems_co.comanage_api.client import APIError, CoManageClient
from rems_co.models import CoPerson


def test_resolve_person_by_email_and_uid_found(mocker):
    # Patch the _get method on the client instance
    mock_get = mocker.patch.object(CoManageClient, "_get")
    mock_get.return_value.json.return_value = {
        "people": [
            {"id": 1, "email": "a@b.com", "identifier": "person1"},
            {"id": 2, "email": "a@b.com", "identifier": "person2"},
        ]
    }

    client = CoManageClient()
    result = client.resolve_person_by_email_and_uid(email="a@b.com", uid="person2")
    assert isinstance(result, CoPerson)
    assert result.id == 2


def test_resolve_person_by_email_and_uid_not_found(mocker):
    mock_get = mocker.patch.object(CoManageClient, "_get")
    mock_get.return_value.json.return_value = {"people": []}

    client = CoManageClient()
    with pytest.raises(APIError):
        client.resolve_person_by_email_and_uid("a@b.com", "nope")


def test_create_group_success(mocker):
    mock_post = mocker.patch.object(CoManageClient, "_post")
    mock_post.return_value.json.return_value = {
        "CoGroups": [{"Id": 42, "Name": "urn:test:xyz"}]
    }

    client = CoManageClient()
    group = client.create_group("urn:test:xyz")
    assert group.id == 42
    assert group.name == "urn:test:xyz"
