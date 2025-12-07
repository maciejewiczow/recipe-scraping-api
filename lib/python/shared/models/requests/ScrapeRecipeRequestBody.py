from pydantic import BaseModel


class ScrapeRecipeRequestBody(BaseModel):
    notificationToken: str
