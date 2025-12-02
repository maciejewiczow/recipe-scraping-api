from pydantic import BaseModel, Field


class NotificationsConfig(BaseModel):
    android: str = Field(validation_alias="ANDROID")
    # ios: str = Field(validation_alias="IOS")
