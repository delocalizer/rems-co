# def test_handle_approve_creates_group(mock_client, mocker):
#    mock_client.get_group_by_name.return_value = None
#    mock_client.create_group.return_value.id = 100
#    mock_client.resolve_user_by_email_and_uid.return_value.id = 200
#    mock_client.add_user_to_group.return_value = None
#
#    event = ApproveEvent(
#        application=1,
#        resource="urn:allowed:resource",
#        user="alice",
#        mail="alice@example.com",
#        end="2030-01-01T00:00:00Z",
#    )
#    mocker.patch("rems_co.settings.settings.create_groups_for_resources", ["*"])
#    handle_approve(event)
#
#
# def test_handle_approve_skips_unmatched_group(mock_client, mocker):
#    mock_client.get_group_by_name.return_value = None
#    mocker.patch(
#        "rems_co.settings.settings.create_groups_for_resources", ["urn:match:this*"]
#    )
#    event = ApproveEvent(
#        application=1,
#        resource="urn:not:matching",
#        user="alice",
#        mail="alice@example.com",
#        end="2030-01-01T00:00:00Z",
#    )
#    handle_approve(event)
#    mock_client.create_group.assert_not_called()
