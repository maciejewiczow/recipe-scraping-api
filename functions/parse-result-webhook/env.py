from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from shared.models.environment.AiConfig import AiConfig


class AiConfigWithWebhook(AiConfig):
    webhook_secret: str = Field(validation_alias="WEBHOOK_SECRET")


class Environment(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="__")

    ai: AiConfigWithWebhook = Field(validation_alias="AI")
    dynamoResponsesTableName: str = Field(
        validation_alias="DYNAMO_RESPONSES_TABLE_NAME"
    )
