# def test_resolve_user_by_email_and_uid_found(mock_client):
#    mock_client._get.return_value.json.return_value = {
#        "users": [
#            {"id": 1, "email": "a@b.com", "identifier": "user1"},
#            {"id": 2, "email": "a@b.com", "identifier": "user2"},
#        ]
#    }
#    client = CoManageClient()
#    result = client.resolve_user_by_email_and_uid(email="a@b.com", uid="user2")
#    assert result.id == 2
#
#
# def test_resolve_user_by_email_and_uid_not_found(mock_client):
#    mock_client._get.return_value.json.return_value = {"users": []}
#    client = CoManageClient()
#    with pytest.raises(APIError):
#        client.resolve_user_by_email_and_uid("a@b.com", "nope")
#
#
# def test_create_group_success(mock_client):
#    mock_client._post.return_value.json.return_value = {
#        "CoGroups": [{"Id": 42, "Name": "urn:test:xyz"}]
#    }
#    client = CoManageClient()
#    group = client.create_group("urn:test:xyz")
#    assert group.id == 42
