from pydantic import Field
from shared.models.environment.AiConfig import AiConfig
from shared.models.environment.settings import BaseEnvironment


class AiConfigWithWebhook(AiConfig):
    webhook_secret: str = Field(validation_alias="WEBHOOK_SECRET")


class Environment(BaseEnvironment):
    ai: AiConfigWithWebhook = Field(validation_alias="AI")
    dynamoResponsesTableName: str = Field(
        validation_alias="DYNAMO_RESPONSES_TABLE_NAME"
    )
