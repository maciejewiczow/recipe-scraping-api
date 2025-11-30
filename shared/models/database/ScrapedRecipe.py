from typing import Dict
from pydantic import BaseModel
from shared.models.IngredientParseStatus import IngredientParseStatus
from shared.models.Recipe import Recipe


class ScrapedRecipeBase(BaseModel):
    wildModeUsed: bool
    recipe: Recipe


class ScrapedRecipe(ScrapedRecipeBase):
    ingredientStatuses: Dict[str, IngredientParseStatus]
