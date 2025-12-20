from pydantic import Field
from shared.models.environment.NotificationConfig import NotificationConfig
from shared.models.environment.settings import BaseEnvironment


class Environment(BaseEnvironment):
    recipesTableName: str = Field(validation_alias="RECIPES_TABLE_NAME")
    failedProcessingNotification: NotificationConfig = Field(
        validation_alias="FAIL_NOTIFICATION"
    )
