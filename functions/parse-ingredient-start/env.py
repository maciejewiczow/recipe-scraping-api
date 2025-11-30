from pydantic import BaseModel, Field

from shared.models.environment.AiConfig import AiConfig
from shared.models.environment.settings import BaseEnvironment


class PromptIdByLanguage(BaseModel):
    pl: str = Field(validation_alias="PL")
    en: str = Field(validation_alias="EN")


class AiConfigWithModel(AiConfig):
    model: str = Field(validation_alias="MODEL_NAME")


class Environment(BaseEnvironment):
    ai: AiConfigWithModel = Field(validation_alias="AI")
    promptId: PromptIdByLanguage = Field(validation_alias="PROMPT_ID")
    dynamoResponsesTableName: str = Field(
        validation_alias="DYNAMO_RESPONSES_TABLE_NAME"
    )
