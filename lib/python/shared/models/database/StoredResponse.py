from typing import Annotated
from shared.models.DTO.ProcessIngredientsInput import (
    IngredientToProcessWithLangInfoDTO,
)
from shared.utils.dynamodb import DynamodbModel, PrimaryKey


class StoredResponseProjection(DynamodbModel):
    TaskToken: str
    ResponseId: Annotated[str, PrimaryKey(key_type="hash")]


class StoredResponse(StoredResponseProjection):
    OriginalIngredientInput: IngredientToProcessWithLangInfoDTO
    RetryCount: int
