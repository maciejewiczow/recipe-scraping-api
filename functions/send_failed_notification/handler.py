from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.parser import event_parser
import boto3
import botocore
import botocore.exceptions
from pydantic import ValidationError
from shared.models.DTO.ProcessIngredientsInput import (
    IngredientToProcessDTO,
    IngredientToProcessWithLangInfoDTO,
)
from shared.models.DTO.ProcessedIngredient import ProcessedIngredientCollection
from shared.models.database.RecipeDbItem import RecipeDbItemProjection
from shared.models.lambda_events.FailHandlerEvent import (
    FailHandlerEventTypeAdapter,
    FailHandlerEvent,
)
from shared.models.notifications.GCMNotification import (
    GCMNotification,
    Notification,
    NotificationContent,
)
from shared.models.notifications.RecipeReadyNotificationData import (
    RecipeReadyNotificationData,
)
from shared.utils.dump_response import dump_response
from shared.utils.environment import validate_environment
from .env import Environment

log = Logger("send_failed_notification")


@log.inject_lambda_context(log_event=True)
@event_parser(
    model=FailHandlerEventTypeAdapter,
)
@validate_environment(model=Environment, log=log)
@dump_response
def handler(
    event: FailHandlerEvent,
    context: LambdaContext,
    *,
    env: Environment,
):
    try:
        match event:
            case [
                ProcessedIngredientCollection(
                    originalIngredient=IngredientToProcessDTO(recipeId=myRecipeId)
                )
            ]:
                recipeId = myRecipeId
            case [IngredientToProcessWithLangInfoDTO(recipeId=myRecipeId)]:
                recipeId = myRecipeId
            case _:
                log.error("Unknown event type")
                raise ValueError("Unknown event type")

        recipesTable = boto3.resource("dynamodb").Table(env.recipesTableName)

        rawRecipeItem = recipesTable.get_item(
            Key={RecipeDbItemProjection.get_primary_key_name(): recipeId},
            ProjectionExpression=RecipeDbItemProjection.top_level_fields_projection(),
            ReturnConsumedCapacity="NONE",
        )

        recipeItem = RecipeDbItemProjection.from_dynamo(rawRecipeItem.get("Item", {}))

        if recipeItem.NotificationEndpointARN is not None:
            snsClient = boto3.client("sns")

            snsClient.publish(
                MessageStructure="json",
                Message=GCMNotification(
                    GCM=Notification(
                        notification=NotificationContent(
                            **env.failedProcessingNotification.model_dump()
                        ),
                        data=RecipeReadyNotificationData(recipeId=recipeId),
                    )
                ).model_dump_json(),
                TargetArn=recipeItem.NotificationEndpointARN,
            )
            snsClient.delete_endpoint(EndpointArn=recipeItem.NotificationEndpointARN)

        recipesTable.update_item(
            Key={RecipeDbItemProjection.get_primary_key_name(): recipeId},
            UpdateExpression="SET IsComplete = :isComplete, HasParsingSucceeded = :hasSucceeded, NotificationEndpointARN = :endpointArn",
            ExpressionAttributeValues={
                ":isComplete": True,
                ":hasSucceeded": False,
                ":endpointArn": None,
            },
            ReturnValues="NONE",
        )
    except botocore.exceptions.ClientError:
        log.exception("Error when calling some aws service")
    except ValidationError:
        log.exception("Error while deserializing the recipe from dynamo")
