from typing import Annotated
from shared.models.DTO.ProcessIngredientsInput import (
    IngredientToProcessWithLangInfoDTO,
)
from shared.utils.dynamodb import DynamodbModel, PrimaryKey, TTLField


class StoredResponseProjection(DynamodbModel):
    ResponseId: Annotated[str, PrimaryKey(key_type="hash")]
    TaskToken: str


class StoredResponse(StoredResponseProjection):
    ExpiresAt: TTLField
    OriginalIngredientInput: IngredientToProcessWithLangInfoDTO
    RetryCount: int
