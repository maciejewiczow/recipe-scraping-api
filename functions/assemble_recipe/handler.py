from itertools import chain
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.parser import event_parser
import boto3
import botocore
import botocore.exceptions
from pydantic import ValidationError
from shared.models.DTO.ProcessedIngredient import (
    ProcessIngredientsMapResult,
)
from shared.models.database.RecipeDbItem import RecipeDbItem
from shared.models.notifications.GCMNotification import (
    GCMNotification,
    Notification,
    NotificationContent,
)
from shared.models.notifications.RecipeReadyNotificationData import (
    RecipeReadyNotificationData,
)
from shared.utils.find import find
from shared.utils.dump_response import dump_response
from aws_lambda_powertools.utilities.typing import LambdaContext
from shared.utils.dynamodb import DynamoDBItemNotFoundException, is_not_found_exception
from shared.utils.environment import validate_environment
from .env import Environment

log = Logger("assemble-recipe")


@log.inject_lambda_context(log_event=True)
@event_parser(
    model=ProcessIngredientsMapResult,
)
@validate_environment(Environment, log)
@dump_response
def handler(
    event: ProcessIngredientsMapResult, context: LambdaContext, *, env: Environment
):
    recipesTable = boto3.resource("dynamodb").Table(env.recipesTableName)

    try:
        recipeId = event.results[0].originalIngredient.recipeId

        rawRecipeItem = recipesTable.get_item(
            Key={RecipeDbItem.get_primary_key_name(): recipeId},
            ReturnConsumedCapacity="NONE",
        )

        recipeItem = RecipeDbItem.from_dynamo(rawRecipeItem.get("Item", {}))

        for parseResult in event.results:
            originalIngredient = find(
                chain.from_iterable(
                    ig.ingredients for ig in recipeItem.Content.recipe.ingredientGroups
                ),
                lambda ingr: ingr.id == parseResult.originalIngredient.ingredientId,
            )

            if originalIngredient is None:
                log.warning(
                    "Original ingredient not found by id in the recipe",
                    extra={
                        "recipe": recipeItem.Content.model_dump(),
                        "originalIngredientId": parseResult.originalIngredient.ingredientId,
                    },
                )
                continue

            resultIter = iter(parseResult.result)

            firstParsedIngredient = next(resultIter)

            originalIngredient.isProcessed = True
            originalIngredient.name = firstParsedIngredient.name
            originalIngredient.quantity = firstParsedIngredient.quantity
            originalIngredient.unit = firstParsedIngredient.unit
            originalIngredient.preparationNotes = firstParsedIngredient.preparationNotes
            originalIngredient.originalText = parseResult.originalIngredient.content

            recipeItem.Content.ingredientStatuses[
                parseResult.originalIngredient.ingredientId
            ] = parseResult.status

            if len(parseResult.result) > 1:
                group = find(
                    recipeItem.Content.recipe.ingredientGroups,
                    lambda ig: parseResult.originalIngredient.ingredientId
                    in ig.ingredients,
                )

                if group is None:
                    log.warning(
                        "Ingredient group not found for first parsed ingredient",
                        extra={"firsParsedIngredientId": firstParsedIngredient.id},
                    )
                    continue

                firstParsedIngredientIndex = find(
                    enumerate(group.ingredients),
                    lambda x: x[1].id == parseResult.originalIngredient.ingredientId,
                )

                assert firstParsedIngredientIndex is not None, "It can't be"

                firstParsedIngredientIndex = firstParsedIngredientIndex[0]

                for parsedIngredient in resultIter:
                    log.debug(
                        "Inserting additional parsed ingredients",
                        extra={
                            "index": firstParsedIngredientIndex + 1,
                            "parsedIngredient": parsedIngredient,
                            "ingredients": group.ingredients,
                        },
                    )
                    parsedIngredient.originalText = (
                        parseResult.originalIngredient.content
                    )

                    group.ingredients.insert(
                        firstParsedIngredientIndex + 1, parsedIngredient
                    )
                    recipeItem.Content.ingredientStatuses[parsedIngredient.id] = (
                        parseResult.status
                    )
                    log.debug(
                        "inserted the ingredient",
                        extra={
                            "ingredients": group.ingredients,
                        },
                    )

        recipeItem.IsComplete = True
        recipeItem.HasParsingSucceeded = True

        if recipeItem.NotificationEndpointARN is not None:
            snsClient = boto3.client("sns")

            snsClient.publish(
                MessageStructure="json",
                Message=GCMNotification(
                    GCM=Notification(
                        notification=NotificationContent(
                            **env.notification.model_dump()
                        ),
                        data=RecipeReadyNotificationData(recipeId=recipeItem.RecipeId),
                    )
                ).model_dump_json(),
                TargetArn=recipeItem.NotificationEndpointARN,
            )
            snsClient.delete_endpoint(EndpointArn=recipeItem.NotificationEndpointARN)
            recipeItem.NotificationEndpointARN = None

        recipesTable.put_item(Item=recipeItem.model_dump(), ReturnValues="NONE")
    except ValidationError:
        log.exception("Invalid recipe in dynamo")
        raise
    except botocore.exceptions.ClientError as e:
        if is_not_found_exception(e):
            log.exception("Recipe not found in dynamo")
            raise DynamoDBItemNotFoundException()

        log.exception("boto3 exception")
        raise
