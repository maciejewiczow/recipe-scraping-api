from typing import Literal, Union
from pydantic import BaseModel


class ScrapeQuery(BaseModel):
    url: str
    parseIngredients: bool = False
    defaultToLang: Union[Literal["en"], Literal["pl"]] = "pl"
