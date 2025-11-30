from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseEnvironment(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="__")
