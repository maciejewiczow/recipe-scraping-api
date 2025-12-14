from pydantic import BaseModel


class GetRecipePathParams(BaseModel):
    recipeId: str
