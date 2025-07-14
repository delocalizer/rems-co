from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Service settings.
    """

    comanage_registry_url: HttpUrl
    comanage_coid: int
    comanage_api_userid: str
    comanage_api_key: str

    comanage_timeout_seconds: int = Field(10, description="HTTP client timeout")
    comanage_retry_attempts: int = Field(
        3, description="Max retry attempts for COmanage API"
    )
    comanage_retry_backoff: float = Field(3, description="Backoff multiplier")
    create_groups_for_resources: list[str] = ["*"]  # Default: all resources

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()  # type: ignore[call-arg]
