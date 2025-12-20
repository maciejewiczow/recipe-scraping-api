from pydantic import BaseModel, TypeAdapter
from shared.models.SupportedLanguage import SupportedLanguage
from shared.models.database.SerializableDatetime import SerializableDatetime


class IngredientToProcessDTO(BaseModel):
    recipeId: str
    ingredientId: str
    content: str


class IngredientToProcessWithLangInfoDTO(IngredientToProcessDTO):
    lang: str | None
    defaultLang: SupportedLanguage
    recipeExpiresAt: SerializableDatetime
    retryCount: int = 0


ProcessIngredientsInput = list[IngredientToProcessWithLangInfoDTO]

ProcessIngredientsInputTypeAdapter = TypeAdapter(
    list[IngredientToProcessWithLangInfoDTO]
)
