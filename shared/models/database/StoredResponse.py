from typing import Annotated
from pydantic import Field
from shared.models.DTO.ProcessIngredientsInput import IngredientToProcessDTO
from shared.utils.dynamodb import DynamodbModel, PrimaryKey


class StoredResponse(DynamodbModel):
    TaskToken: str
    ResponseId: Annotated[str, PrimaryKey(key_type="hash")]
    OriginalIngredientInput: IngredientToProcessDTO
    RetryCount: int


class StoredResponseProjection(StoredResponse):
    OriginalIngredientInput: IngredientToProcessDTO = Field(exclude=True)
    RetryCount: int = Field(exclude=True)
