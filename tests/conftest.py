import pytest


@pytest.fixture
def mock_client(mocker):
    client = mocker.patch("rems_co.comanage_api.client.CoManageClient", autospec=True)
    return client.return_value
