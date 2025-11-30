from pydantic import BaseModel


class RecipeReadyNotificationData(BaseModel):
    recipeId: str
