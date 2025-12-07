from pydantic import BaseModel
from shared.models.SupportedLanguage import SupportedLanguage


class ScrapeQuery(BaseModel):
    url: str
    parseIngredients: bool = False
    defaultToLang: SupportedLanguage = "pl"
