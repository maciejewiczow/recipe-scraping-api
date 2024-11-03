from enum import Enum
from pydantic import BaseModel
from api.models.Recipe import Recipe


class IngredientsParseStatus(str, Enum):
    off = "off"
    ok = "ok"
    ingredientTooLong = "ingredientTooLong"
    ranOutOfCredits = "ranOutOfCredits"
    failedToParseAIOutput = "failedToParseAIOutput"


class ScrapeRecipeResponse(BaseModel):
    recipe: Recipe
    wildModeUsed: bool
    ingredientParseStatus: IngredientsParseStatus
