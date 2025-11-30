from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.parser import event_parser
import boto3
from openai import InvalidWebhookSignatureError, OpenAI
from pydantic import ValidationError
from shared.models.DTO.WebhokOutput import WebhookOutput
from shared.models.database.StoredResponse import (
    StoredResponseProjection,
)
from shared.models.lambda_events.WebhookApiGatewayEvent import WebhookApiGatewayEvent
from shared.models.responses.HttpResponse import (
    BadRequestResponse,
    EmptyOkResponse,
    InternalServerErrorResponse,
)
from shared.utils.dump_response import dump_response
from shared.utils.environment import validate_environment
from .env import Environment

log = Logger("parse-result-webhook")


@log.inject_lambda_context(log_event=True)
@event_parser(model=WebhookApiGatewayEvent)
@validate_environment(Environment)
@dump_response
def handler(event: WebhookApiGatewayEvent, context: LambdaContext, *, env: Environment):
    client = OpenAI(
        api_key=env.ai.api_key,
        base_url=env.ai.base_url,
        webhook_secret=env.ai.webhook_secret,
    )

    try:
        openaiEvent = client.webhooks.unwrap(event.body, event.headers)

        if openaiEvent.type != "response.completed":
            return EmptyOkResponse()

        responsesTable = boto3.resource("dynamodb").Table(env.dynamoResponsesTableName)

        storedResponseRaw = responsesTable.get_item(
            Key={StoredResponseProjection.get_primary_key_name(): openaiEvent.data.id},
            ReturnConsumedCapacity="NONE",
            ProjectionExpression=StoredResponseProjection.top_level_fields_projection(),
        )

        storedResponse = StoredResponseProjection.from_dynamo(
            storedResponseRaw.get("Item", {})
        )

        sfnClient = boto3.client("stepfunctions")

        sfnClient.send_task_success(
            taskToken=storedResponse.TaskToken,
            output=WebhookOutput(
                responseId=openaiEvent.data.id,
            ).model_dump_json(),
        )
    except InvalidWebhookSignatureError:
        log.exception("Invalid openai webhook signature")
        return BadRequestResponse()
    except ValidationError:
        log.exception("Invalid data retrieved from dynamo")
        return InternalServerErrorResponse()
