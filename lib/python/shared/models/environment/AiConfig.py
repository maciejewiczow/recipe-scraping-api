from pydantic import BaseModel, Field


class AiConfig(BaseModel):
    api_key: str = Field(validation_alias="API_KEY")
    base_url: str = Field(validation_alias="BASE_URL")
