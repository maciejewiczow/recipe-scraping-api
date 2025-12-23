from pydantic import BaseModel, TypeAdapter
from shared.models.DTO.ProcessIngredientsInput import (
    IngredientToProcessWithLangInfoDTO,
    ProcessIngredientsInput,
)
from shared.models.DTO.ProcessedIngredient import ProcessedIngredientCollectionList


class SendOutOfCreditsNotificationOutput(BaseModel):
    originalInput: IngredientToProcessWithLangInfoDTO


FailHandlerEvent = (
    ProcessedIngredientCollectionList
    | ProcessIngredientsInput
    | list[SendOutOfCreditsNotificationOutput]
)

FailHandlerEventTypeAdapter = TypeAdapter(FailHandlerEvent)
