from typing import Annotated
from shared.models.database.SerializableDatetime import SerializableDatetime
from shared.utils.dynamodb import DynamodbModel, PrimaryKey


class QuotaItem(DynamodbModel):
    UserId: Annotated[str, PrimaryKey("hash")]
    RequestTimestamp: Annotated[float, PrimaryKey("sort")]
    ExpiresAt: SerializableDatetime
