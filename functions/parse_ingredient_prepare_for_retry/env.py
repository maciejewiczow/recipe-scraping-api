from pydantic import Field
from shared.models.environment.settings import BaseEnvironment


class Environment(BaseEnvironment):
    dynamoResponsesTableName: str = Field(
        validation_alias="DYNAMO_RESPONSES_TABLE_NAME"
    )
