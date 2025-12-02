from typing import List, Optional
from pydantic import BaseModel
from shared.models.IngredientGroup import IngredientGroup
from shared.utils.uuid_field import Uuid


class Recipe(BaseModel):
    id: str = Uuid
    title: str
    description: Optional[str]
    steps: List[str]
    ingredientGroups: List[IngredientGroup]
    url: str
    category: Optional[str]
    imageUrl: str
    lang: str
