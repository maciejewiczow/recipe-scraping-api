from typing import Annotated
from shared.models.database.ScrapedRecipe import ScrapedRecipe
from shared.utils.dynamodb import DynamodbModel, PrimaryKey, TTLField


class RecipeDbItem(DynamodbModel):
    RecipeId: Annotated[str, PrimaryKey(key_type="hash")]
    Content: ScrapedRecipe
    IsComplete: bool
    OwnerId: str
    ExpiresAt: TTLField
    NotificationEndpointARN: str | None
