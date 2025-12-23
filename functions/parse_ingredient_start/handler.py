from datetime import datetime, timedelta
from aws_lambda_powertools import Logger
import boto3
from openai import BadRequestError, OpenAI, RateLimitError
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.parser import event_parser
from shared.models.DTO.ParseIngredientInput import ParseIngredientInput
from shared.models.chat.chat_models import create_chat_models, schema_name
from shared.models.database.StoredResponse import StoredResponse
from shared.models.exceptions.chatExceptions import (
    InputTooLongException,
    OutOfCreditsException,
)
from shared.utils.dump_response import dump_response
from shared.utils.environment import validate_environment
from botocore.exceptions import ClientError
from .env import Environment

log = Logger("parse-ingredient-start")


@log.inject_lambda_context(log_event=True)
@event_parser(model=ParseIngredientInput)
@dump_response
@validate_environment(model=Environment, log=log)
def handler(event: ParseIngredientInput, context: LambdaContext, *, env: Environment):
    client = OpenAI(api_key=env.ai.api_key, base_url=env.ai.base_url)

    if event.ingredient.lang is not None and "pl" in event.ingredient.lang:
        lang = "pl"
    elif event.ingredient.lang is not None and "en" in event.ingredient.lang:
        lang = "en"
    else:
        lang = event.ingredient.defaultLang

    promptId = env.promptId.pl if lang == "pl" else env.promptId.en

    _, Ingredients = create_chat_models(lang)

    raise OutOfCreditsException()

    try:
        response = client.responses.create(
            prompt={
                "id": promptId,
            },
            input=event.ingredient.content,
            text={
                "format": {
                    "type": "json_schema",
                    "name": schema_name[lang],
                    "strict": False,
                    "schema": Ingredients.model_json_schema(),
                },
                "verbosity": "low",
            },
            reasoning={"effort": "minimal"},
            store=True,
            background=True,
            service_tier="flex",
            model=env.ai.model,
        )

        dynamo = boto3.resource("dynamodb")
        responsesTable = dynamo.Table(env.dynamoResponsesTableName)

        responsesTable.put_item(
            Item=StoredResponse(
                ResponseId=response.id,
                TaskToken=event.taskToken,
                OriginalIngredientInput=event.ingredient,
                RetryCount=event.ingredient.retryCount,
                ExpiresAt=datetime.now() + timedelta(days=1),
            ).model_dump(),
            ReturnValues="NONE",
        )
    except ClientError:
        log.exception("Boto3 client exception occurred")
        raise
    except RateLimitError as e:
        if e.code == "insufficient_quota":
            log.exception("Out of openai credits")
            raise OutOfCreditsException() from e

        raise e
    except BadRequestError as e:
        if e.code == "string_above_max_length":
            log.exception("Ingredient too long")
            raise InputTooLongException() from e

        log.exception("OpenAI returned bad request status")
        raise e
