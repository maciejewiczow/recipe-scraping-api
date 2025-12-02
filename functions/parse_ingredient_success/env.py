from pydantic import Field
from shared.models.environment.AiConfig import AiConfig
from shared.models.environment.settings import BaseEnvironment


class Environment(BaseEnvironment):
    ai: AiConfig = Field(validation_alias="AI")
    dynamoResponsesTableName: str = Field(
        validation_alias="DYNAMO_RESPONSES_TABLE_NAME"
    )
    maxRetryCount: int = Field(validation_alias="MAX_RETRY_COUNT", ge=0)
