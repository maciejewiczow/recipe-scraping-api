from pydantic import BaseModel


class WebhookOutput(BaseModel):
    responseId: str


class ErrorWebhookOutput(WebhookOutput):
    error: str
