from uuid import uuid4
from pydantic import BaseModel, Field


class Ingredient(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    name: str
    unit: str | None = None
    quantity: int | None = None
    preparationNotes: str | None = None
    isProcessed: bool

    def __eq__(self, value: object) -> bool:
        if isinstance(value, Ingredient):
            return self.id == value.id

        if isinstance(value, str):
            return self.id == value

        return super().__eq__(value)
