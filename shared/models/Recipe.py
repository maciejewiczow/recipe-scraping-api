from typing import List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field
from shared.models.IngredientGroup import IngredientGroup


class Recipe(BaseModel):
    id: str = Field(default_factory=lambda : uuid4().hex, frozen=True, init=False)
    title: str
    description: Optional[str]
    steps: List[str]
    ingredientGroups: List[IngredientGroup]
    url: str
    category: Optional[str]
    imageUrl: str
    lang: str
