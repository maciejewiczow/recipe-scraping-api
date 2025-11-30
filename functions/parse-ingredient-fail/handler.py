from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.parser import event_parser
import boto3
import botocore
import botocore.exceptions
from pydantic import ValidationError
from shared.models.DTO.ProcessedIngredient import ProcessedIngredientCollection
from shared.models.DTO.WebhokOutput import ErrorWebhookOutput
from shared.models.Ingredient import Ingredient
from shared.models.IngredientParseStatus import IngredientParseStatus
from shared.models.database.StoredResponse import StoredResponse
from shared.utils.dump_response import dump_response
from shared.utils.environment import validate_environment
from .env import Environment


log = Logger("parse-ingredient-fail")


@log.inject_lambda_context(log_event=True)
@event_parser(model=ErrorWebhookOutput)
@validate_environment(Environment)
@dump_response
def handler(event: ErrorWebhookOutput, context: LambdaContext, *, env: Environment):
    responsesTable = boto3.resource("dynamodb").Table(env.dynamoResponsesTableName)

    try:
        storedResponseRaw = responsesTable.get_item(
            Key={StoredResponse.get_primary_key_name(): event.responseId},
            ReturnConsumedCapacity="NONE",
        )

        storedResponse = StoredResponse.from_dynamo(storedResponseRaw.get("Item", {}))

        responsesTable.delete_item(
            Key={StoredResponse.get_primary_key_name(): event.responseId},
            ReturnValues="NONE",
        )

        return ProcessedIngredientCollection(
            originalIngredient=storedResponse.OriginalIngredientInput,
            result=[
                Ingredient(
                    name=storedResponse.OriginalIngredientInput.content,
                    unit=None,
                    quantity=None,
                    isProcessed=True,
                )
            ],
            status=IngredientParseStatus.ingredientTooLong,
        )
    except ValidationError:
        log.exception("Invalid dynamodb content")
        raise
    except botocore.exceptions.ClientError:
        log.exception("DynamoDB error occurred")
        raise
