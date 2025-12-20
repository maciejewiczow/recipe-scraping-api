from decimal import Decimal
from typing import Annotated
from shared.utils.dynamodb import DynamodbModel, PrimaryKey, TTLField


class QuotaItem(DynamodbModel):
    UserId: Annotated[str, PrimaryKey("hash")]
    RequestTimestamp: Annotated[Decimal, PrimaryKey("sort")]
    ExpiresAt: TTLField
