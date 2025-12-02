from pydantic import BaseModel, Field


class WebhookOutput(BaseModel):
    responseId: str


class AWSError(BaseModel):
    error: str | None = Field(validation_alias="Error")
    cause: str | None = Field(validation_alias="Cause")


class ErrorWebhookOutput(WebhookOutput):
    error: AWSError
