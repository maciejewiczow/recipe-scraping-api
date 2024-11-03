from http import HTTPStatus
import os
from flask import request
from flask_openapi3 import Info, OpenAPI, ValidationErrorModel, Tag
from api.models.queries.ScrapeQuery import ScrapeQuery
from api.models.responses.ErrorResponse import ErrorResponse
from api.models.responses.ScrapeRecipeResponse import (
    IngredientsParseStatus,
    ScrapeRecipeResponse,
)
from api.services.scrapingService import UnableToParseRecipeException, tryScrapeRecipe
from api.utils.toJson import toJson

api_key_header = "X-api-key"
api_key_scheme_name = "api_key"

info = Info(
    title="Recipe Scraping API",
    description="API allowing to try to scrape a recipe from a website using recipe-scrapers library",
    version="1.0.0",
)
app = OpenAPI(
    __name__,
    info=info,
    validation_error_status=400,
    security_schemes={
        api_key_scheme_name: {"type": "apiKey", "name": api_key_header, "in": "header"}
    },
)


def verify_authentication(query: ScrapeQuery):
    if not query.parseIngredients:
        return

    suppliedKey = request.headers.get(api_key_header)

    if not suppliedKey:
        return toJson(ErrorResponse(error="Unauthorized")), 401

    actualKey = os.getenv("API_KEY")

    if not actualKey:
        return toJson(ErrorResponse(error="Forbidden")), 403

    if suppliedKey != actualKey:
        return toJson(ErrorResponse(error="Unauthorized")), 401


@app.get(
    "/recipe",
    summary="Try to scrape a recipe from a given website",
    responses={
        HTTPStatus.OK: ScrapeRecipeResponse,
        HTTPStatus.UNPROCESSABLE_ENTITY: ErrorResponse,
        HTTPStatus.BAD_REQUEST: ValidationErrorModel,
        HTTPStatus.UNAUTHORIZED: ErrorResponse,
        HTTPStatus.FORBIDDEN: ErrorResponse,
    },
    tags=[Tag(name="Scraping")],
    security=[{api_key_scheme_name: []}],
)
def scrape_recipe(query: ScrapeQuery):
    authResult = verify_authentication(query)

    if authResult:
        return authResult

    try:
        wildModeUsed, recipe, status = tryScrapeRecipe(
            query.url, query.parseIngredients, query.defaultToLang
        )

        return (
            toJson(
                ScrapeRecipeResponse(
                    recipe=recipe,
                    wildModeUsed=wildModeUsed,
                    ingredientParseStatus=(
                        (status if status else IngredientsParseStatus.ok)
                        if query.parseIngredients
                        else IngredientsParseStatus.off
                    ),
                )
            ),
            200,
        )
    except UnableToParseRecipeException:
        return toJson(ErrorResponse(error="Unable to scrape the recipe")), 422


if __name__ == "__main__":
    app.run()
