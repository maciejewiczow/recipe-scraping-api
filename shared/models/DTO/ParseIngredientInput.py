from pydantic import BaseModel

from shared.models.DTO.ProcessIngredientsInput import IngredientToProcessWithLangInfoDTO
from shared.models.exceptions.stepFunctionFlowExceptions import FailedToParseAIOutput


class ParseIngredientInput(BaseModel):
    taskToken: str
    ingredient: IngredientToProcessWithLangInfoDTO
    error: FailedToParseAIOutput | None
