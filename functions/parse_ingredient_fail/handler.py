from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.parser import event_parser
import boto3
import botocore.exceptions
from pydantic import ValidationError
from shared.models.DTO.ParseIngredientInput import (
    ParseIngredientInputWithError,
)
from shared.models.DTO.ProcessIngredientsInput import IngredientToProcessDTO
from shared.models.DTO.ProcessedIngredient import ProcessedIngredientCollection
from shared.models.Ingredient import Ingredient
from shared.models.IngredientParseStatus import IngredientParseStatus
from shared.models.database.StoredResponse import StoredResponse
from shared.utils.dump_response import dump_response
from shared.utils.environment import validate_environment
from .env import Environment


log = Logger("parse-ingredient-fail")


@log.inject_lambda_context(log_event=True)
@event_parser(model=ParseIngredientInputWithError)
@validate_environment(Environment, log)
@dump_response
def handler(
    event: ParseIngredientInputWithError, context: LambdaContext, *, env: Environment
):
    responsesTable = boto3.resource("dynamodb").Table(env.dynamoResponsesTableName)

    try:
        responsesTable.delete_item(
            Key={StoredResponse.get_primary_key_name(): event.error.responseId},
            ReturnValues="NONE",
        )

        return ProcessedIngredientCollection(
            originalIngredient=IngredientToProcessDTO(
                recipeId=event.recipeId,
                ingredientId=event.ingredientId,
                content=event.content,
            ),
            result=[
                Ingredient(
                    name=event.content,
                    isProcessed=True,
                )
            ],
            status=IngredientParseStatus.generalAiError
            if event.error.error == "ResponseFailed"
            else IngredientParseStatus.ingredientTooLong,
        )
    except ValidationError:
        log.exception("Invalid dynamodb content")
        raise
    except botocore.exceptions.ClientError:
        log.exception("DynamoDB error occurred")
        raise
