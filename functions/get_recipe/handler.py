from aws_lambda_powertools.utilities.typing import LambdaContext
import boto3
import botocore
import botocore.exceptions
from shared.models.authorization.CognitoUserClaims import CognitoUserClaims
from shared.models.database.RecipeDbItem import RecipeDbItem
from shared.models.database.ScrapedRecipe import ScrapedRecipe
from aws_lambda_powertools import Logger
from shared.models.requests.paths.GetRecipePathParams import GetRecipePathParams
from shared.models.responses.HttpResponse import (
    MultiStatusResponse,
    NotFoundResponse,
    OkResponse,
)
from shared.openapi.tags import RecipesTag
from shared.utils.dump_response import dump_response
from shared.utils.environment import validate_environment
from shared.utils.openapi import openapi_endpoint
from shared.utils.verify_quota import verify_user_quota
from .env import Environment
from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventV2Model


log = Logger("get-recipe")


@log.inject_lambda_context(log_event=True)
@dump_response
@verify_user_quota(log)
@openapi_endpoint(
    log,
    responses=[
        OkResponse[ScrapedRecipe],
        MultiStatusResponse[str],
        NotFoundResponse,
    ],
    path=GetRecipePathParams,
    operationId="getRecipe",
    description="Get a processed recipe by id",
    summary="Returns a processed recipe given it's id",
    tags=[RecipesTag],
)
@validate_environment(Environment, log)
def handler(
    rawEvent: APIGatewayProxyEventV2Model,
    _: LambdaContext,
    *,
    env: Environment,
    jwtClaims: CognitoUserClaims,
    path: GetRecipePathParams,
    **kwargs,
):
    try:
        recipesTable = boto3.resource("dynamodb").Table(env.recipesTableName)

        rawRecipe = recipesTable.get_item(
            Key={RecipeDbItem.get_primary_key_name(): path.recipeId},
            ReturnConsumedCapacity="NONE",
        )

        recipeRow = RecipeDbItem.from_dynamo(rawRecipe.get("Item", {}))

        if not recipeRow.IsComplete or recipeRow.OwnerId != jwtClaims.userId:
            return NotFoundResponse()

        if not recipeRow.HasParsingSucceeded:
            return MultiStatusResponse(body="Parsing failed, please try again")

        return OkResponse(body=recipeRow.Content)
    except botocore.exceptions.ClientError as e:
        if e.response.get("Error", {}).get("Code") == "ResourceNotFoundException":
            return NotFoundResponse()

        log.exception("DynamoDB exception occured")
        raise
