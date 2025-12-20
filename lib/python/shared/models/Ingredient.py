from pydantic import BaseModel
from shared.utils.uuid_field import Uuid


class Ingredient(BaseModel):
    id: str = Uuid
    name: str
    unit: str | None = None
    quantity: str | None = None
    preparationNotes: str | None = None
    originalText: str
    isProcessed: bool

    def __eq__(self, value: object) -> bool:
        if isinstance(value, Ingredient):
            return self.id == value.id

        if isinstance(value, str):
            return self.id == value

        return super().__eq__(value)
