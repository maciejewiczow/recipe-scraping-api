from pydantic import BaseModel, Field


class NotificationConfig(BaseModel):
    body: str = Field(validation_alias="BODY")
    title: str = Field(validation_alias="TITLE")
