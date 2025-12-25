from typing import Annotated, Dict, Literal

from aws_lambda_powertools import Logger
import boto3
from pydantic import BaseModel, Discriminator, TypeAdapter, ValidationError
from shared.models.environment.MessagesConfig import MessagesConfig


class PushNotificationContent(BaseModel):
    type: Literal["push"]
    title: str
    body: str


class EmailContent(BaseModel):
    type: Literal["email"]
    subject: str
    body: str


MessagesTypeAdapter = TypeAdapter(
    dict[str, Annotated[PushNotificationContent | EmailContent, Discriminator("type")]]
)


def get_messages[T: (PushNotificationContent, EmailContent)](
    config: MessagesConfig,
    msgType: type[T],
    log: Logger,
) -> T:
    s3 = boto3.client("s3")

    try:
        msg = MessagesTypeAdapter.validate_json(
            s3.get_object(Bucket=config.fileBucket, Key=config.bucketKey)
        )[config.key]

        if msg is not msgType:
            log.error(
                "Unexpected message type",
                extra={"config": config, "expectedType": msgType},
            )
            raise ValueError("Unexpected message type")

        return msg  # pyright: ignore[reportReturnType]
    except KeyError:
        log.exception("Missing message key", extra={"config": config})
        raise
    except ValidationError:
        log.exception("Invalid messages schema", extra={"config": config})
        raise
