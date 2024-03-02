from typing import List, Optional
from pydantic import BaseModel
from api.models.IngredientGroup import IngredientGroup


class Recipe(BaseModel):
    title: str
    description: Optional[str]
    steps: List[str]
    ingredientGroups: List[IngredientGroup]
    url: str
    category: Optional[str]
    imageUrl: str
    lang: str
