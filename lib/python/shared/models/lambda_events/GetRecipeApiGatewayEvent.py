from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventV2Model
from pydantic import BaseModel, field_validator


class GetRecipePathParams(BaseModel):
    recipeId: str


class GetRecipeApiGatewayEvent(APIGatewayProxyEventV2Model):
    body: None = None
    queryStringParameters: None = None
    pathParameters: GetRecipePathParams = None  # type: ignore

    @field_validator("pathParameters", mode="after")
    @classmethod
    def validateQueryStringParams(cls, value: GetRecipePathParams | None):
        if value is None:
            raise ValueError("Path params cannot be none")

        return value
