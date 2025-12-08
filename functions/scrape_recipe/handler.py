from datetime import datetime
import itertools
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from aws_lambda_powertools.utilities.typing import LambdaContext
import boto3
from botocore.exceptions import ClientError
from pydantic import TypeAdapter
from recipe_scrapers import scrape_html
from recipe_scrapers._exceptions import RecipeScrapersExceptions
from shared.models.DTO.ProcessIngredientsInput import (
    IngredientToProcessWithLangInfoDTO,
    ProcessIngredientsInput,
)
from shared.models.IngredientParseStatus import IngredientParseStatus
from shared.models.Ingredient import Ingredient
from shared.models.IngredientGroup import IngredientGroup
from shared.models.Recipe import Recipe
from shared.models.authorization.CognitoUserClaims import CognitoUserClaims
from shared.models.database.RecipeDbItem import RecipeDbItem
from shared.models.database.ScrapedRecipe import ScrapedRecipe
from shared.models.exceptions.apiExceptions import UnableToParseRecipeException
from shared.models.requests.ScrapeRecipeRequestBody import (
    ScrapeRecipeRequestBody,
)
from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventV2Model
from shared.models.requests.queries.ScrapeQuery import ScrapeQuery
from shared.models.responses.HttpResponse import (
    InternalServerErrorResponse,
    OkResponse,
    UnprocessableEntityResponse,
)
from shared.utils.environment import validate_environment
from shared.utils.dump_response import dump_response
from shared.utils.openapi import http_endpoint
from shared.utils.verify_quota import verify_user_quota
from .env import Environment
from aws_lambda_powertools import Logger

log = Logger("scrape-recipe")


@log.inject_lambda_context(log_event=True)
@dump_response
@http_endpoint(
    log,
    responses=[
        OkResponse[str],
        InternalServerErrorResponse,
        UnprocessableEntityResponse,
    ],
    query=ScrapeQuery,
    body=TypeAdapter(ScrapeRecipeRequestBody | None),
)
@validate_environment(model=Environment, log=log)
@verify_user_quota(log)
def handler(
    rawEvent: APIGatewayProxyEventV2Model,
    _: LambdaContext,
    *,
    env: Environment,
    jwtClaims: CognitoUserClaims,
    query: ScrapeQuery,
    body: ScrapeRecipeRequestBody | None = None,
    **kwargs,
):
    try:
        wild_mode = False

        html = urlopen(Request(query.url)).read().decode("utf-8")

        try:
            result = scrape_html(html, org_url=query.url)
        except RecipeScrapersExceptions:
            try:
                result = scrape_html(html, org_url=query.url, wild_mode=True)
                wild_mode = True
            except RecipeScrapersExceptions:
                raise UnableToParseRecipeException()

        rd = result.to_json()

        ingredientGroups = [
            IngredientGroup(
                name=ig.get("purpose", None),
                ingredients=[
                    Ingredient(name=name, isProcessed=not query.parseIngredients)
                    for name in ig.get("ingredients", [])
                ],
            )
            for ig in rd["ingredient_groups"]
        ]

        recipe = Recipe(
            title=rd["title"],
            imageUrl=rd["image"],
            lang=rd["language"],
            url=rd["canonical_url"],
            description=rd.get("description", None),
            category=rd.get("category", None),
            ingredientGroups=ingredientGroups,
            steps=rd["instructions_list"],
        )

        recipeContent = ScrapedRecipe(
            wildModeUsed=wild_mode,
            recipe=recipe,
            ingredientStatuses={
                ingredient.id: IngredientParseStatus.off
                for ingredient in itertools.chain.from_iterable(
                    group.ingredients for group in ingredientGroups
                )
            }
            if not query.parseIngredients
            else {},
        )

        recipesTable = boto3.resource("dynamodb").Table(env.recipesTableName)
        recipeExpiresAt = datetime.now() + env.recipeTTL

        notificationEndpointArn: str | None = None

        if query.parseIngredients and body is not None:
            snsClient = boto3.client("sns")
            # TODO: handle IOS - from useragent header or smth
            result = snsClient.create_platform_endpoint(
                PlatformApplicationArn=env.platformApplicationARN.android,
                Token=body.notificationToken,
            )
            notificationEndpointArn = result["EndpointArn"]

        recipesTable.put_item(
            Item=RecipeDbItem(
                RecipeId=recipe.id,
                Content=recipeContent,
                IsComplete=not query.parseIngredients,
                ExpiresAt=recipeExpiresAt,
                NotificationEndpointARN=notificationEndpointArn,
                OwnerId=jwtClaims.userId,
            ).model_dump(),
            ReturnValues="NONE",
        )

        if query.parseIngredients:
            stepFnClient = boto3.client("stepfunctions")

            stepFnClient.start_execution(
                stateMachineArn=env.processIngredientStepFnArn,
                input=ProcessIngredientsInput.dump_json(
                    [
                        IngredientToProcessWithLangInfoDTO(
                            content=ingredient.name,
                            recipeId=recipe.id,
                            ingredientId=ingredient.id,
                            defaultLang=query.defaultToLang,
                            lang=rd.get("language"),
                            recipeExpiresAt=recipeExpiresAt,
                        )
                        for ingredient in itertools.chain.from_iterable(
                            group.ingredients for group in ingredientGroups
                        )
                    ],
                    ensure_ascii=True,
                ).decode("utf-8"),
            )

        return OkResponse(body=recipeContent.recipe.id)
    except ClientError:
        log.exception("Boto3 client exception occurred")
        return InternalServerErrorResponse()
    except UnableToParseRecipeException:
        log.exception("Unable to parse the recipe from the given website")
        return UnprocessableEntityResponse(body="Unable to parse the recipe")
    except HTTPError as e:
        log.exception("Unable to load data from the provided url")
        return UnprocessableEntityResponse(
            body=f"Unable to load content from the provided url (received status code {e.status})"
        )
