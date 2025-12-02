from pydantic import BaseModel, computed_field
from shared.models.DTO.ProcessIngredientsInput import IngredientToProcessWithLangInfoDTO
from shared.models.DTO.WebhokOutput import AWSError


class ParseIngredientInput(BaseModel):
    taskToken: str
    ingredient: IngredientToProcessWithLangInfoDTO


class AWSErrorWithResponseId(AWSError):
    @computed_field
    @property
    def responseId(self) -> str | None:
        return self.cause


class ParseIngredientInputWithError(IngredientToProcessWithLangInfoDTO):
    error: AWSErrorWithResponseId
