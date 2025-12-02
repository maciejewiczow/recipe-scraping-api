from typing import List, Optional
from pydantic import BaseModel
from shared.models.Ingredient import Ingredient
from shared.utils.uuid_field import Uuid


class IngredientGroup(BaseModel):
    id: str = Uuid
    name: Optional[str]
    ingredients: List[Ingredient]
