from pydantic import Field
from shared.models.environment.MessagesConfig import MessagesConfig
from shared.models.environment.settings import BaseEnvironment


class Environment(BaseEnvironment):
    recipesTableName: str = Field(validation_alias="RECIPES_TABLE_NAME")
    notification: MessagesConfig = Field(validation_alias="NOTIFICATION")
