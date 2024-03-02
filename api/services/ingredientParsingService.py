from itertools import repeat
import re
from typing import Any, Generator, List, Tuple
from openai import OpenAI, RateLimitError
from openai.types.chat import ChatCompletionMessageParam
from api.models.Ingredient import Ingredient
from api.models.responses.ScrapeRecipeResponse import IngredientsParseStatus


class IngredientParsingException(Exception):
    pass


class OutOfCreditsException(IngredientParsingException):
    pass


class InputTooLongException(IngredientParsingException):
    pass


class UnableToParseAIResponseException(IngredientParsingException):
    pass


class UnexpectedAIBehaviorException(IngredientParsingException):
    pass


messages_pl: List[ChatCompletionMessageParam] = [
    {
        "role": "system",
        "content": """Jesteś parserem składników przepisów. Zostatnie ci podany składnik przepisu, a twoim zadaniem jest wyodrębnienie z niego nazwy składnika (wraz z jakimikolwiek dodakowymi wskazówkami przygotowania), jednostkę i ilość składnika. Nazwa składnika powinna być w mianowniku, ale jej liczebnośc gramatyczna powinna pozostać niezmieniona.
Odpowiesz używając następującego formatu:
Ingredient:
Unit:
Quantity:
Preparation notes:
Jeżeli zostanie ci podany więcej niż jeden składnik na raz, utworz listę. Przykładowy rezulat z listami wygląda następująco:
Ingredient:
 - składnik 1
 - składnik 2
 ...
Unit:
 - jednostka składnika 1
 - jednostka składnika 2
 ...
Quantity:
 - ilość składnika 1
 - ilość składnika 2
 ...
Preparation notes:
 - dodakowe wskazówki do składnika 1
 - dodakowe wskazówki do składnika 2
 ...
Jeżeli któraś z pozycji nie jest aplikowalna, użyte zostanie słowo None.""",
    },
    {"role": "user", "content": "100 g serka kremowego typu Philadelphia, Almette"},
    {
        "role": "assistant",
        "content": """Ingredient: serek kremowy
Unit: g
Quantity: 100
Preparation notes: typu Philadelphia, Almette""",
    },
    {"role": "user", "content": "100 g kukurydzy z puszki, waga po odsączeniu"},
    {
        "role": "assistant",
        "content": """Ingredient: kukurydza z puszki
Unit: g
Quantity: 100
Preparation notes: waga po odsączeniu""",
    },
    {"role": "user", "content": "4 ząbki czosnku, drobno posiekane"},
    {
        "role": "assistant",
        "content": """Ingredient: ząbki czosnku
Unit: None
Quantity: 4
Preparation notes: drobno posiekane""",
    },
    {"role": "user", "content": "listki z 2 gałązek natki pietruszki"},
    {
        "role": "assistant",
        "content": """Ingredient: listki z natki pietruszki
Unit: gałązki
Quantity: 2
Preparation notes: None""",
    },
    {
        "role": "user",
        "content": "250 g (około 20 sztuk) krewetek (surowych lub gotowanych, mrożonych lub świeżych)",
    },
    {
        "role": "assistant",
        "content": """Ingredient: krewetki
Unit: g
Quantity: 250
Preparation notes: surowe lub gotowane, mrożone lub świeże""",
    },
    {"role": "user", "content": "3 łyżki oliwy extra vergine"},
    {
        "role": "assistant",
        "content": """Ingredient: oliwa
Unit: łyżki
Quantity: 3
Preparation notes: extra vergine""",
    },
    {
        "role": "user",
        "content": "1 puszka krojonych pomidorów + 2 łyżki koncentratu pomidorowego*",
    },
    {
        "role": "assistant",
        "content": """Ingredient:
 - pomidory krojone
 - koncentrat pomidorowy
Unit:
 - puszka
 - łyżki
Quantity:
 - 1
 - 2
Preparation notes:
 - None
 - None""",
    },
    {
        "role": "user",
        "content": "przyprawy: 3 ziela angielskie, liść laurowy, 2 płaskie łyżki suszonego majeranku",
    },
    {
        "role": "assistant",
        "content": """Ingredient:
 - ziela angielskie
 - liść laurowy
 - majeranek suszony
Unit:
 - None
 - None
 - płaska łyżka
Quantity:
 - 3
 - 1
 - 2
Preparation notes:
 - None
 - None
 - None""",
    },
    {
        "role": "user",
        "content": '400 g suchej fasolki "Piękny Jaś" lub 2 puszki fasolki',
    },
    {
        "role": "assistant",
        "content": """Ingredient: fasolka "Piękny Jaś"
Unit: g
Quantity: 400
Preparation notes: sucha

Ingredient: fasolka
Unit: puszki
Quantity: 2
Preparation notes: None""",
    },
    {"role": "user", "content": "250 g boczku (parzonego lub wędzonego)"},
    {
        "role": "assistant",
        "content": """Ingredient: boczek
Unit: g
Quantity: 250
Preparation notes: parzony lub wędzony""",
    },
    {"role": "user", "content": "sól do smaku"},
    {
        "role": "assistant",
        "content": """Ingredient: sól
Unit: None
Quantity: None
Preparation notes: do smaku""",
    },
]

messages_en: List[ChatCompletionMessageParam] = [
    {
        "role": "system",
        "content": """You are a recipe ingredient parser. You will be presented with a recipe ingredient and your job is to extract the ingredient name together with any additional preparation notes, unit and quantity from it. Also make sure that the ingredient name is in it's base form, but it's grammatical number should remain unchanged. The ingredient names should not be translated from their original language.
You will reply using the following format:
Ingredient:
Unit:
Quantity:
Preparation notes:
When presented with more than one ingredient description prepare a list. An example output with lists should look like this:
Ingredient:
 - ingredient 1
 - ingredient 2
 ...
Unit:
 - unit 1
 - unit 2
 ...
Quantity:
 - quantity 1
 - quantity 2
 ...
Preparation notes:
 - note 1
 - note 2
 ...
When something is not applicable to the input, the word None will be used.""",
    },
    {"role": "user", "content": "100 g cream cheese like Philadelphia or Almette"},
    {
        "role": "assistant",
        "content": """Ingredient: cream cheese
Unit: g
Quantity: 100
Preparation notes: like Philadelphia or Almette""",
    },
    {"role": "user", "content": "100 g canned corn, weighted after draining"},
    {
        "role": "assistant",
        "content": """Ingredient: canned corn
Unit: g
Quantity: 100
Preparation notes: wighed after draining""",
    },
    {"role": "user", "content": "4 cloves of garlick, finely chopped"},
    {
        "role": "assistant",
        "content": """Ingredient: cloves of garlic
Unit: None
Quantity: 4
Preparation notes: finely chopped""",
    },
    {"role": "user", "content": "1 tsp Pure Vanilla Extract"},
    {
        "role": "assistant",
        "content": """Ingredient: vanilla exctract
Unit: tsp
Quantity: 1
Preparation notes: Pure""",
    },
    {
        "role": "user",
        "content": "250 g (around 20 pieces) shripms (raw, cooked or frozen)",
    },
    {
        "role": "assistant",
        "content": """Ingredient: shrimps
Unit: g
Quantity: 250
Preparation notes: raw, cooked or frozen""",
    },
    {"role": "user", "content": "3 tbsp olive oil"},
    {
        "role": "assistant",
        "content": """Ingredient: olive oil
Unit: tbsp
Quantity: 3
Preparation notes: None""",
    },
    {
        "role": "user",
        "content": "1 can of chopped tomatoes + 2 tbsp tomato concentrate",
    },
    {
        "role": "assistant",
        "content": """Ingredient:
 - chopped tomatoes
 - tomato concentrate
Unit:
 - can
 - tbsp
Quantity:
 - 1
 - 2
Preparation notes:
 - None
 - None""",
    },
    {
        "role": "user",
        "content": "przyprawy: 3 allspice, bay leaf, 2 flat tbsp dried marjoram",
    },
    {
        "role": "assistant",
        "content": """Ingredient:
 - allspice
 - bay leaf
 - dried marjoram
Unit:
 - None
 - None
 - flat tbsp
Quantity:
 - 3
 - 1
 - 2
Preparation notes:
 - None
 - None
 - None""",
    },
    {
        "role": "user",
        "content": '400 g dry White Emergo beans or 2 cans of beans',
    },
    {
        "role": "assistant",
        "content": """Ingredient: White Emergo beans
Unit: g
Quantity: 400
Preparation notes: dry

Ingredient: beans
Unit: can
Quantity: 2
Preparation notes: None""",
    },
    {"role": "user", "content": "2 tsp Baking Powder"},
    {
        "role": "assistant",
        "content": """Ingredient: baking powder
Unit: tsp
Quantity: 2
Preparation notes: None""",
    },
    {"role": "user", "content": "a pinch of salt"},
    {
        "role": "assistant",
        "content": """Ingredient: salt
Unit: pinch
Quantity: 1
Preparation notes: None""",
    },
]


openai = OpenAI()


def parseIngredients(
    ingredients: List[str],
    lang: str,
    defaultLang: str
) -> Generator[Ingredient, Any, IngredientsParseStatus]:
    status = IngredientsParseStatus.ok

    if 'pl' in lang:
        lang = 'pl'
    elif 'en' in lang:
        lang = 'en'
    else:
        lang = defaultLang

    messages = messages_pl if lang == 'pl' else messages_en

    for input_ingredient in ingredients:
        try:
            chat_result = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[*messages, {"role": "user", "content": input_ingredient}],
            )

            if chat_result.choices[0].finish_reason == "length":
                raise InputTooLongException()
            elif chat_result.choices[0].finish_reason != "stop":
                raise UnexpectedAIBehaviorException()

            chat_response_str = chat_result.choices[0].message.content

            if not chat_response_str:
                raise UnableToParseAIResponseException()

            for ingredient, unit, quantity, preparationNote in parseChatResponse(
                chat_response_str
            ):
                if re.search(noneRegex, ingredient) or len(ingredient) == 0:
                    continue

                ing = Ingredient(
                    unit=unit if not re.search(noneRegex, unit) else None,
                    name=(
                        ingredient
                        + (
                            f" {preparationNote}"
                            if not re.search(noneRegex, preparationNote)
                            else ""
                        )
                    ),
                    quantity=(quantity if not re.search(noneRegex, quantity) else None),
                )
                yield ing

        except RateLimitError:
            raise OutOfCreditsException()
        except UnableToParseAIResponseException:
            status = IngredientsParseStatus.failedToParseAIOutput
        except UnexpectedAIBehaviorException:
            status = IngredientsParseStatus.failedToParseAIOutput
        except InputTooLongException:
            status = IngredientsParseStatus.ingredientTooLong

    return status


parsingRegex = re.compile(
    r"Ingredients?:\s(.*|(?:\s?-\s?.*\n)+)\s*Units?:\s(.*|(?:\s?-\s?.*\n)+)\s*Quantit(?:y|ies):\s(.*|(?:\s?-\s?.*\n)+)\s*Preparation notes?:\s(.*|(?:\s?-\s?.*\n)+)",
    re.IGNORECASE,
)

listSeparatorRegex = re.compile(r"\n?-\s+")
noneRegex = re.compile(r"\s?None\s?", re.IGNORECASE)


def parseChatResponse(response: str) -> Generator[Tuple[str, str, str, str], Any, None]:
    matches = re.findall(parsingRegex, response)

    if len(matches) == 0:
        raise UnableToParseAIResponseException()

    for match in matches:
        ingredients = match[0]
        unit = match[1]
        quantity = match[2]
        notes = match[3]

        if re.search(listSeparatorRegex, ingredients):
            ingredients = listSeparatorRegex.split(ingredients)

        if re.search(listSeparatorRegex, unit):
            unit = listSeparatorRegex.split(unit)
            unit[len(unit) : len(ingredients)] = "None"
        elif type(ingredients) == list:
            unit = list(repeat(unit, len(ingredients)))

        if re.search(listSeparatorRegex, quantity):
            quantity = listSeparatorRegex.split(quantity)
            quantity[len(quantity) : len(ingredients)] = "None"
        elif type(ingredients) == list:
            quantity = list(repeat(quantity, len(ingredients)))

        if re.search(listSeparatorRegex, notes):
            notes = listSeparatorRegex.split(notes)
            notes[len(notes) : len(ingredients)] = "None"
        elif type(ingredients) == list:
            notes = list(repeat(notes, len(ingredients)))

        if (
            type(ingredients) == str
            and type(unit) == str
            and type(quantity) == str
            and type(notes) == str
        ):
            yield ingredients, unit, quantity, notes
        else:
            assert len(ingredients) == len(unit) == len(quantity) == len(notes)
            yield from zip(ingredients, unit, quantity, notes)
