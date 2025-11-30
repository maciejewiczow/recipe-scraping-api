from pydantic import BaseModel, Field
from shared.models.environment.settings import BaseEnvironment


class NotificationConfig(BaseModel):
    body: str = Field(validation_alias="BODY")
    title: str = Field(validation_alias="TITLE")


class Environment(BaseEnvironment):
    recipesTableName: str = Field(validation_alias="RECIPES_TABLE_NAME")
    notification: NotificationConfig = Field(validation_alias="NOTIFICATION")
