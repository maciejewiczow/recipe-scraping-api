from recipe_scrapers import scrape_me
from recipe_scrapers._exceptions import RecipeScrapersExceptions
from api.models.Ingredient import Ingredient
from api.models.IngredientGroup import IngredientGroup
from api.models.Recipe import Recipe
from api.models.responses.ScrapeRecipeResponse import IngredientsParseStatus
from api.services.ingredientParsingService import parseIngredients
from api.utils.getExhaustedGeneratorReturnValue import getExhaustedGeneratorReturnValue


class UnableToParseRecipeException(Exception):
    pass


def tryScrapeRecipe(url: str, doParseIngredients: bool, defaultLang: str):
    wild_mode = False

    try:
        result = scrape_me(url)
    except RecipeScrapersExceptions:
        try:
            result = scrape_me(url, wild_mode=True)
            wild_mode = True
        except RecipeScrapersExceptions:
            raise UnableToParseRecipeException()

    rd = result.to_json()

    ingredientGroups = []

    status = IngredientsParseStatus.ok
    for rg in rd["ingredient_groups"]:
        ingredientGen = parseIngredients(
            rg.get("ingredients", []), rd.get("language", ""), defaultLang
        )
        ig = IngredientGroup(
            name=rg.get("purpose", None),
            ingredients=(
                [
                    Ingredient(name=ingr, unit=None, quantity=None)
                    for ingr in rg.get("ingredients", [])
                ]
                if not doParseIngredients
                else list(ingredientGen)
            ),
        )
        status = getExhaustedGeneratorReturnValue(ingredientGen)
        ingredientGroups.append(ig)

    return (
        wild_mode,
        Recipe(
            title=rd["title"],
            imageUrl=rd["image"],
            lang=rd["language"],
            url=rd["canonical_url"],
            description=rd.get("description", None),
            category=rd.get("category", None),
            ingredientGroups=ingredientGroups,
            steps=rd["instructions_list"],
        ),
        status,
    )
