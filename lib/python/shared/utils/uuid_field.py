from uuid import uuid4
from pydantic import Field


Uuid = Field(default_factory=lambda: str(uuid4()), frozen=True, init=False)
