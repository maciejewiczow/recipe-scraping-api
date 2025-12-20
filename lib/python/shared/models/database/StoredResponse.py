from typing import Annotated

from pydantic import Field
from shared.models.DTO.ProcessIngredientsInput import (
    IngredientToProcessWithLangInfoDTO,
)
from shared.utils.dynamodb import DynamodbModel, PrimaryKey, TTLField


class StoredResponse(DynamodbModel):
    ResponseId: Annotated[str, PrimaryKey(key_type="hash")]
    TaskToken: str
    ExpiresIn: TTLField
    OriginalIngredientInput: IngredientToProcessWithLangInfoDTO
    RetryCount: int


class StoredResponseProjection(StoredResponse):
    ExpiresIn: TTLField = Field(exclude=True)
    OriginalIngredientInput: IngredientToProcessWithLangInfoDTO = Field(exclude=True)
    RetryCount: int = Field(exclude=True)
