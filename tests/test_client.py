from datetime import datetime

import pytest

from rems_co.comanage_api.client import APIError, CoManageClient
from rems_co.comanage_api.models import (
    AddGroupMemberRequest,
    AddGroupRequest,
    CoGroup,
    CoGroupMember,
    CoGroupMemberPayload,
    CoGroupMemberResponse,
    CoGroupsResponse,
    CoPeopleResponse,
    CoPerson,
    Identifier,
    IdentifiersResponse,
    NewObjectResponse,
    PersonRef,
)
from rems_co.models import Group, Person


def test_resolve_person_by_email_and_uid_found(mocker):
    mock_get = mocker.patch.object(CoManageClient, "_get")

    mock_get.side_effect = [
        # CoPeople response
        mocker.Mock(
            json=lambda: CoPeopleResponse(
                CoPeople=[CoPerson(Id=1234), CoPerson(Id=5678)],
            ).model_dump()
        ),
        # Identifiers for 1234
        mocker.Mock(
            json=lambda: IdentifiersResponse(
                Identifiers=[
                    Identifier(
                        Id=1,
                        Identifier="eppn-for-1234",
                        Type="eppn",
                        Person=CoPerson(Id=1234),
                    )
                ],
            ).model_dump()
        ),
        # Identifiers for 5678, includes match
        mocker.Mock(
            json=lambda: IdentifiersResponse(
                Identifiers=[
                    Identifier(
                        Id=2,
                        Identifier="eppn-for-5678",
                        Type="eppn",
                        Person=CoPerson(Id=5678),
                    ),
                    Identifier(
                        Id=3,
                        Identifier="http://cilogon.org/serverI/users/2769",
                        Type="oidcsub",
                        Person=CoPerson(Id=5678),
                    ),
                ],
            ).model_dump()
        ),
    ]

    client = CoManageClient()
    person = client.resolve_person_by_email_and_uid(
        email="foo.bar@baz.com", uid="http://cilogon.org/serverI/users/2769"
    )

    assert isinstance(person, Person)
    assert person.id == 5678
    assert person.email == "foo.bar@baz.com"
    assert person.identifier == "http://cilogon.org/serverI/users/2769"


def test_resolve_person_by_email_and_uid_not_found(mocker):
    mock_get = mocker.patch.object(CoManageClient, "_get")

    mock_get.side_effect = [
        mocker.Mock(
            json=lambda: CoPeopleResponse(CoPeople=[CoPerson(Id=5678)]).model_dump()
        ),
        mocker.Mock(
            json=lambda: IdentifiersResponse(
                Identifiers=[
                    Identifier(
                        Id=1,
                        Identifier="no-match",
                        Type="eppn",
                        Person=CoPerson(Id=5678),
                    )
                ],
            ).model_dump()
        ),
    ]

    client = CoManageClient()
    with pytest.raises(APIError, match="No matching Person found"):
        client.resolve_person_by_email_and_uid("a@b.com", "someuser")


def test_create_group_success(mocker):
    mock_post = mocker.patch.object(CoManageClient, "_post")
    mock_post.return_value.json.return_value = NewObjectResponse(
        ObjectType="CoGroup",
        Id=42,
    ).model_dump()

    client = CoManageClient()
    group = client.create_group("urn:test:xyz")

    assert isinstance(group, Group)
    assert group.id == 42
    assert group.name == "urn:test:xyz"

    # Validate request payload using the model
    payload = mock_post.call_args.kwargs["json"]
    parsed = AddGroupRequest.model_validate(payload)
    assert parsed.CoGroups[0].Name == "urn:test:xyz"
    assert parsed.CoGroups[0].CoId == client.co_id
    assert parsed.CoGroups[0].Status == "Active"


def test_get_group_by_name_found(mocker):
    mock_get = mocker.patch.object(CoManageClient, "_get")
    mock_get.return_value.json.return_value = CoGroupsResponse(
        CoGroups=[
            CoGroup(Id=1, Name="urn:other"),
            CoGroup(Id=2, Name="urn:target"),
        ],
    ).model_dump()

    client = CoManageClient()
    group = client.get_group_by_name("urn:target")

    assert isinstance(group, Group)
    assert group.id == 2
    assert group.name == "urn:target"


def test_get_group_by_name_not_found(mocker):
    mock_get = mocker.patch.object(CoManageClient, "_get")
    mock_get.return_value.json.return_value = CoGroupsResponse(CoGroups=[]).model_dump()

    client = CoManageClient()
    assert client.get_group_by_name("urn:missing") is None


def test_add_person_to_group(mocker):
    mock_post = mocker.patch.object(CoManageClient, "_post")
    client = CoManageClient()
    end = datetime(2025, 7, 20, 23, 59, 59)

    client.add_person_to_group(person_id=5678, group_id=1000, valid_through=end)

    payload = mock_post.call_args.kwargs["json"]
    parsed = AddGroupMemberRequest.model_validate(payload)

    assert len(parsed.CoGroupMembers) == 1
    member = parsed.CoGroupMembers[0]
    assert member.Person.Id == 5678
    assert member.CoGroupId == 1000
    assert member.ValidThrough == end


def test_group_member_payload_omits_valid_through_if_none():
    req = AddGroupMemberRequest(
        RequestType="CoGroupMembers",
        Version="1.0",
        CoGroupMembers=[
            CoGroupMemberPayload(
                Version="1.0",
                CoGroupId=123,
                Person=PersonRef(Type="CO", Id=456),
                ValidThrough=None,
            )
        ],
    )
    dumped = req.model_dump(mode="json", exclude_none=True)
    assert "ValidThrough" not in dumped["CoGroupMembers"][0]


def test_remove_person_from_group(mocker):
    mock_get = mocker.patch.object(CoManageClient, "_get")
    mock_delete = mocker.patch.object(CoManageClient, "_delete")

    mock_get.return_value.json.return_value = CoGroupMemberResponse(
        CoGroupMembers=[CoGroupMember(Id=777)],
    ).model_dump()

    client = CoManageClient()
    client.remove_person_from_group(person_id=5678, group_id=1000)

    mock_delete.assert_called_once_with("/co_group_members/777.json")


def test_remove_person_from_group_missing(mocker):
    mock_get = mocker.patch.object(CoManageClient, "_get")

    mock_get.return_value.json.return_value = CoGroupMemberResponse(
        CoGroupMembers=[]
    ).model_dump()

    client = CoManageClient()
    with pytest.raises(APIError, match="No group membership found"):
        client.remove_person_from_group(person_id=1, group_id=2)
