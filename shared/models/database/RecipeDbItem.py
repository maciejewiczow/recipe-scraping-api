from typing import Annotated
from shared.models.database.SerializableDatetime import SerializableDatetime
from shared.models.database.ScrapedRecipe import ScrapedRecipe
from shared.utils.dynamodb import DynamodbModel, PrimaryKey


class RecipeDbItem(DynamodbModel):
    RecipeId: Annotated[str, PrimaryKey(key_type="hash")]
    Content: ScrapedRecipe
    IsComplete: bool
    OwnerId: str
    ExpiresAt: SerializableDatetime
    NotificationEndpointARN: str | None
