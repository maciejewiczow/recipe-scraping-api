from typing import Annotated
from pydantic import BaseModel

from shared.utils.JsonSerializer import JsonSerializer


class NotificationContent(BaseModel):
    title: str
    body: str


class Notification[T: BaseModel](BaseModel):
    notification: NotificationContent
    data: T


class GCMNotification[T: BaseModel](BaseModel):
    GCM: Annotated[Notification[T], JsonSerializer]
