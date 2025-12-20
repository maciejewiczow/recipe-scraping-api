from pydantic import TypeAdapter
from shared.models.DTO.ProcessIngredientsInput import (
    ProcessIngredientsInput,
)
from shared.models.DTO.ProcessedIngredient import ProcessIngredientsMapResult


FailHandlerEvent = ProcessIngredientsMapResult | ProcessIngredientsInput

FailHandlerEventTypeAdapter = TypeAdapter(FailHandlerEvent)
