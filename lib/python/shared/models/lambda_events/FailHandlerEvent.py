from pydantic import TypeAdapter
from shared.models.DTO.ProcessIngredientsInput import (
    ProcessIngredientsInput,
)
from shared.models.DTO.ProcessedIngredient import ProcessedIngredientCollectionList


FailHandlerEvent = ProcessedIngredientCollectionList | ProcessIngredientsInput

FailHandlerEventTypeAdapter = TypeAdapter(FailHandlerEvent)
