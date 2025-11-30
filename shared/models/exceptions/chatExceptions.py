class IngredientParsingException(Exception):
    pass


class OutOfCreditsException(IngredientParsingException):
    pass


class InputTooLongException(IngredientParsingException):
    pass


class UnableToParseAIResponseException(IngredientParsingException):
    pass


class UnexpectedAIBehaviorException(IngredientParsingException):
    pass
