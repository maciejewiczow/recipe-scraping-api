from typing import List, Optional
from pydantic import BaseModel

from api.models.Ingredient import Ingredient


class IngredientGroup(BaseModel):
    name: Optional[str]
    ingredients: List[Ingredient]
