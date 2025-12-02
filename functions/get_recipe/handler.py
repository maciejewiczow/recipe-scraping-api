from aws_lambda_powertools.utilities.typing import LambdaContext
import boto3
import botocore
import botocore.exceptions
from shared.models.authorization.CognitoUserClaims import CognitoUserClaims
from shared.models.database.RecipeDbItem import RecipeDbItem
from shared.models.lambda_events.GetRecipeApiGatewayEvent import (
    GetRecipeApiGatewayEvent,
)
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.parser import event_parser
from shared.models.responses.HttpResponse import NotFoundResponse, OkResponse
from shared.utils.dump_response import dump_response
from shared.utils.environment import validate_environment
from shared.utils.verify_quota import verify_user_quota
from .env import Environment

log = Logger("get-recipe")


@log.inject_lambda_context(log_event=True)
@event_parser(model=GetRecipeApiGatewayEvent)
@validate_environment(Environment, log)
@dump_response
@verify_user_quota(log)
def handler(
    event: GetRecipeApiGatewayEvent,
    _: LambdaContext,
    *,
    env: Environment,
    jwtClaims: CognitoUserClaims,
):
    try:
        recipesTable = boto3.resource("dynamodb").Table(env.recipesTableName)

        rawRecipe = recipesTable.get_item(
            Key={RecipeDbItem.get_primary_key_name(): event.pathParameters.recipeId},
            ReturnConsumedCapacity="NONE",
        )

        recipeRow = RecipeDbItem.from_dynamo(rawRecipe.get("Item", {}))

        if not recipeRow.IsComplete or recipeRow.OwnerId != jwtClaims.userId:
            return NotFoundResponse()

        return OkResponse(body=recipeRow.Content)
    except botocore.exceptions.ClientError as e:
        if e.response.get("Error", {}).get("Code") == "ResourceNotFoundException":
            return NotFoundResponse()

        log.exception("DynamoDB exception occured")
        raise
