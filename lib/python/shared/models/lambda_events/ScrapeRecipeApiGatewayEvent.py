from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventV2Model
from pydantic import BaseModel, field_validator

from shared.models.queries.ScrapeQuery import ScrapeQuery


class ScrapeRecipeRequestBody(BaseModel):
    notificationToken: str


class ScrapeRecipeApiGatewayEvent(APIGatewayProxyEventV2Model):
    body: ScrapeRecipeRequestBody | None = None
    queryStringParameters: ScrapeQuery = None  # type: ignore

    @field_validator("queryStringParameters", mode="after")
    @classmethod
    def validateQueryStringParams(cls, value: ScrapeQuery | None):
        if value is None:
            raise ValueError("Query cannot be none")

        return value
