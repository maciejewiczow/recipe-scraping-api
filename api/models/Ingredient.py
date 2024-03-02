from typing import Optional
from pydantic import BaseModel


class Ingredient(BaseModel):
    unit: Optional[str]
    name: str
    quantity: Optional[str]
