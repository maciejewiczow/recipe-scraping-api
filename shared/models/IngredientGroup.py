from typing import List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field
from shared.models.Ingredient import Ingredient


class IngredientGroup(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex, frozen=True, init=False)
    name: Optional[str]
    ingredients: List[Ingredient]
