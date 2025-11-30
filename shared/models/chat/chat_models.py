from pydantic import BaseModel, TypeAdapter
from shared.models.SupportedLanguage import SupportedLanguage

schema_name: dict[SupportedLanguage, str] = {"pl": "Składniki", "en": "Ingredients"}

ingredient_field_descriptions: dict[SupportedLanguage, dict[str, str]] = {
    "en": {
        "name": "Name of the ingredient being processed, for instance 'tomatoes', 'shrimp', 'tofu'.",
        "quantity": "Amount of the ingredient, if specified, otherwise null.",
        "unit": "The unit that the ingredient quantity is specified in, if present, otherwise null.",
        "preparationNotes": "Additional info about the ingredient if given, for instance 'finely chopped', 'diced', 'freshly brewed'. Null if none given.",
    },
    "pl": {
        "name": "Nazwa przetwarzanego składnika kulinarnego w mianowniku i niezmienionej liczbie gramatycznej (np. 'cebula', 'ziemniaki').",
        "quantity": "Ilość składnika, jeśli podana. Null jeżeli ilość nie jest podana",
        "unit": "Jednostka ilościowa, jeśli wyrażona (np. 'g', 'ml', 'sztuka'). Null, jeżeli nie podano.",
        "preparationNotes": "Dodatkowe informacje o składniku, jeżeli podane (np 'posiekane', 'zmielone' itp.). Null jeżeli brak dodatkowych informacji.",
    },
}


class Ingredient(BaseModel):
    name: str
    quantity: int | None
    unit: str | None
    preparationNotes: str | None

    @classmethod
    def apply_schema_lang(cls, lang: SupportedLanguage):
        for field_name, field_info in cls.model_fields.items():
            field_info.description = ingredient_field_descriptions[lang].get(field_name)


Ingredients = TypeAdapter(list[Ingredient])
