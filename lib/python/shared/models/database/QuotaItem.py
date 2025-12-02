from decimal import Decimal
from typing import Annotated
from shared.models.database.SerializableDatetime import SerializableDatetime
from shared.utils.dynamodb import DynamodbModel, PrimaryKey


class QuotaItem(DynamodbModel):
    UserId: Annotated[str, PrimaryKey("hash")]
    RequestTimestamp: Annotated[Decimal, PrimaryKey("sort")]
    ExpiresAt: SerializableDatetime
