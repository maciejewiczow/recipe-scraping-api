from pydantic import BaseModel
from shared.models.DTO.ProcessIngredientsInput import IngredientToProcessDTO
from shared.models.Ingredient import Ingredient
from shared.models.IngredientParseStatus import IngredientParseStatus


class ProcessedIngredientCollection(BaseModel):
    status: IngredientParseStatus
    originalIngredient: IngredientToProcessDTO
    result: list[Ingredient]


ProcessedIngredientCollectionList = list[ProcessedIngredientCollection]


class ProcessIngredientsMapResult(BaseModel):
    results: ProcessedIngredientCollectionList
