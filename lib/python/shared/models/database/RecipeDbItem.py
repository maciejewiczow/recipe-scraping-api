from typing import Annotated
from pydantic import Field
from shared.models.database.ScrapedRecipe import ScrapedRecipe
from shared.utils.dynamodb import DynamodbModel, PrimaryKey, TTLField


class RecipeDbItem(DynamodbModel):
    RecipeId: Annotated[str, PrimaryKey(key_type="hash")]
    Content: ScrapedRecipe
    IsComplete: bool
    HasParsingSucceeded: bool | None
    OwnerId: str
    ExpiresAt: TTLField
    NotificationEndpointARN: str | None


class RecipeDbItemProjection(RecipeDbItem):
    Content: ScrapedRecipe = Field(exclude=True)
    HasParsingSucceeded: bool | None = Field(exclude=True)
    IsComplete: bool = Field(exclude=True)
    OwnerId: str = Field(exclude=True)
    ExpiresAt: TTLField = Field(exclude=True)
