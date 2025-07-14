import os
from unittest import mock

from rems_co.settings import Settings


class TestSettings:
    """Test Settings class"""

    def test_settings_from_file(self):
        """
        Read from .env.example file
        """
        example = Settings(_env_file=".env.example")
        assert str(example.comanage_registry_url) == "https://my.domain/registry/"
        assert example.comanage_coid == 99
        assert example.comanage_api_userid == "xxxuser"
        assert example.comanage_api_key == "xxxkey"

    @mock.patch.dict(os.environ, {"COMANAGE_COID": "42"})
    def test_settings_env_override(self):
        """
        Read from .env.example file and override with env var
        """
        example = Settings(_env_file=".env.example")
        # value from file is 99 (see test_settings_from_file)
        assert example.comanage_coid == 42
