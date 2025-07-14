from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    comanage_registry_url: HttpUrl
    comanage_coid: int
    comanage_api_userid: str
    comanage_api_key: str
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
