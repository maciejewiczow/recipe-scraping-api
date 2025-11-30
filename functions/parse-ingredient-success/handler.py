from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.parser import event_parser
import boto3
from openai import OpenAI
from pydantic import ValidationError
from shared.models.DTO.ProcessIngredientsInput import IngredientToProcessDTO
from shared.models.IngredientParseStatus import IngredientParseStatus
from shared.models.DTO.ProcessedIngredient import ProcessedIngredientCollection
from shared.models.DTO.WebhokOutput import WebhookOutput
from shared.models.Ingredient import Ingredient
from shared.models.chat.chat_models import Ingredients
from shared.models.database.StoredResponse import StoredResponse
from shared.models.exceptions.stepFunctionFlowExceptions import FailedToParseAIOutput
from shared.utils.dump_response import dump_response
from shared.utils.environment import validate_environment
from botocore.exceptions import ClientError
from .env import Environment

log = Logger("parse-ingredient-success")


@log.inject_lambda_context(log_event=True)
@event_parser(model=WebhookOutput)
@validate_environment(Environment)
@dump_response
def handler(
    event: WebhookOutput, context: LambdaContext, *, env: Environment
) -> ProcessedIngredientCollection:
    client = OpenAI(
        api_key=env.ai.api_key,
        base_url=env.ai.base_url,
    )

    try:
        responsesTable = boto3.resource("dynamodb").Table(env.dynamoResponsesTableName)

        storedResponseRaw = responsesTable.get_item(
            Key={StoredResponse.get_primary_key_name(): event.responseId},
            ReturnConsumedCapacity="NONE",
        )

        try:
            storedResponse = StoredResponse.from_dynamo(
                storedResponseRaw.get("Item", {})
            )
        except ValidationError:
            log.exception("Invalid dynamodb content")
            raise

        status = IngredientParseStatus.ok

        if storedResponse.RetryCount > env.maxRetryCount:
            log.warning(
                "Failed to parse the ingredient even after retries",
                extra={"retryCount": storedResponse.RetryCount},
            )
            status = IngredientParseStatus.failedToParseAIOutput

        response = client.responses.retrieve(event.responseId)

        try:
            ingredients = Ingredients.validate_json(response.output_text)

            responsesTable.delete_item(
                Key={StoredResponse.get_primary_key_name(): event.responseId},
                ReturnValues="NONE",
            )

            return ProcessedIngredientCollection(
                originalIngredient=storedResponse.OriginalIngredientInput,
                result=[
                    Ingredient(
                        name=i.name, unit=i.unit, quantity=i.quantity, isProcessed=True
                    )
                    for i in ingredients
                ],
                status=status,
            )
        except ValidationError:
            log.exception("Unable to parse ai response into an object")

            if status == IngredientParseStatus.ok:
                raise FailedToParseAIOutput(retryCount=storedResponse.RetryCount + 1)

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
                status=status,
            )
    except ClientError:
        log.exception("Dynamodb exception")
        raise


def create_unprocessed_response(
    originalIngredient: IngredientToProcessDTO, status: IngredientParseStatus
) -> ProcessedIngredientCollection:
    return ProcessedIngredientCollection(
        originalIngredient=originalIngredient,
        result=[
            Ingredient(
                name=originalIngredient.content,
                unit=None,
                quantity=None,
                isProcessed=True,
            )
        ],
        status=status,
    )
