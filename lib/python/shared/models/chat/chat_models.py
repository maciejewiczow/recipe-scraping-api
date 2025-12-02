from pydantic import BaseModel, Field
from shared.models.SupportedLanguage import SupportedLanguage

schema_name: dict[SupportedLanguage, str] = {"pl": "Skladniki", "en": "Ingredients"}

field_descriptions: dict[SupportedLanguage, dict[str, str]] = {
    "en": {
        "name": "Name of the ingredient being processed",
        "quantity": "Amount of the ingredient, if specified, otherwise null. If a quantity range is given, it will be saved like <range-start>-<range-end> (see examples)",
        "unit": "The unit that the ingredient quantity is specified in, if present, otherwise null.",
        "preparationNotes": "Additional info about the ingredient if given; null if none given.",
        "ingredients": "List of all the ingredients present in the parsed text. If there is only one ingredient, the list will include only one element.",
    },
    "pl": {
        "name": "Nazwa przetwarzanego składnika kulinarnego w mianowniku i niezmienionej liczbie gramatycznej.",
        "quantity": "Ilość składnika, jeśli podana. Null jeżeli ilość nie jest podana. Jeżeli podany został zakres ilościwy, powinien zostać on wyrażony w następnującym formacie: <range-start>-<range-end> (patrz: przykłady)",
        "unit": "Jednostka ilościowa, jeśli wyrażona. Null, jeżeli nie podano.",
        "preparationNotes": "Dodatkowe informacje o składniku, jeżeli podane. Null jeżeli brak dodatkowych informacji.",
        "ingredients": "Lista wszystkich składników obecnych w przetwarzanym tekście. Jeżeli obecny jest tylko jeden składnik, lista będzie miała jeden element",
    },
}

ingredient_field_examples: dict[SupportedLanguage, dict[str, list[str]]] = {
    "en": {
        "name": ["tofu", "shrimp", "eggs", "mayo"],
        "quantity": ["1", "2", "0.4", "1/2", "1-2", "10-20"],
        "unit": ["pcs", "g", "ml", "l"],
        "preparationNotes": ["finely chopped", "diced", "freshly brewed"],
    },
    "pl": {
        "name": ["cebula", "ziemniaki", "jajka", "ocet"],
        "quantity": ["1", "2", "0.4", "1/2", "1-2", "10-20"],
        "unit": ["g", "ml", "sztuk", "sztuka", "sztuki"],
        "preparationNotes": ["posiekane", "zmielone"],
    },
}


def create_chat_models(lang: SupportedLanguage):
    class Ingredient(BaseModel):
        name: str = Field(
            description=field_descriptions[lang]["name"],
            examples=ingredient_field_examples[lang]["name"],
        )
        quantity: str | None = Field(
            description=field_descriptions[lang]["quantity"],
            examples=ingredient_field_examples[lang]["quantity"],
        )
        unit: str | None = Field(
            description=field_descriptions[lang]["unit"],
            examples=ingredient_field_examples[lang]["unit"],
        )
        preparationNotes: str | None = Field(
            description=field_descriptions[lang]["preparationNotes"],
            examples=ingredient_field_examples[lang]["preparationNotes"],
        )

    class Ingredients(BaseModel):
        ingredients: list[Ingredient] = Field(
            description=field_descriptions[lang]["ingredients"]
        )

    return Ingredient, Ingredients
