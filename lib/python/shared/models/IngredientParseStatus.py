from enum import Enum


class IngredientParseStatus(str, Enum):
    off = "off"
    ok = "ok"
    ingredientTooLong = "ingredientTooLong"
    failedToParseAIOutput = "failedToParseAIOutput"
    generalAiError = "generalAiError"
