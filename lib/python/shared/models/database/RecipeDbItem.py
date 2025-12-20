from typing import Annotated
from shared.models.database.ScrapedRecipe import ScrapedRecipe
from shared.utils.dynamodb import DynamodbModel, PrimaryKey, TTLField


class RecipeDbItemProjection(DynamodbModel):
    RecipeId: Annotated[str, PrimaryKey(key_type="hash")]
    NotificationEndpointARN: str | None


class RecipeDbItem(RecipeDbItemProjection):
    Content: ScrapedRecipe
    IsComplete: bool
    HasParsingSucceeded: bool | None
    OwnerId: str
    ExpiresAt: TTLField
