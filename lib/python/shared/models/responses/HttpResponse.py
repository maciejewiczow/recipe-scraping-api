from typing import Annotated, Literal
from pydantic import BaseModel, Field, PlainSerializer, PrivateAttr, computed_field
from shared.utils.JsonSerializer import JsonSerializer


class HttpResponse(BaseModel):
    statusCode: int
    body: Annotated[str | BaseModel, JsonSerializer]


class BadRequestResponse(HttpResponse):
    statusCode: Literal[400] = Field(400, init=False, frozen=True)
    body: str = "Bad request"


class NotFoundResponse(HttpResponse):
    statusCode: Literal[404] = Field(404, init=False, frozen=True)
    body: str = "Not found"


class UnprocessableEntityResponse(HttpResponse):
    statusCode: Literal[422] = Field(422, init=False, frozen=True)
    body: str = "Unprocessable entity"


class InternalServerErrorResponse(HttpResponse):
    statusCode: Literal[500] = Field(500, init=False, frozen=True)
    body: str = "Internal server error"


class ForbiddenResponse(HttpResponse):
    statusCode: Literal[403] = Field(403, init=False, frozen=True)
    body: str = "Forbidden"


class TooManyRequestsHeaders(BaseModel):
    retryAfter: Annotated[int, PlainSerializer(lambda x: str(x))] = Field(
        serialization_alias="Retry-After"
    )


class TooManyRequestsResponse(HttpResponse):
    statusCode: Literal[429] = Field(429, init=False, frozen=True)
    body: str = "Too many requests"
    headers: TooManyRequestsHeaders


class OkResponse[T: BaseModel | str](HttpResponse):
    statusCode: Literal[200] = Field(200, init=False, frozen=True)
    body: Annotated[T, JsonSerializer]

    _headers: dict[str, str] = PrivateAttr({})

    @computed_field
    @property
    def headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json"
            if isinstance(self.body, BaseModel)
            else "text/plain",
            **self._headers,
        }

    @headers.setter
    def set_headers(self, value: dict[str, str]):
        self._headers = value


class MultiStatusResponse[T: BaseModel | str](OkResponse[T]):
    statusCode: Literal[207] = Field(207, init=False, frozen=True)


class EmptyOkResponse(OkResponse):
    body: str = Field("", init=False, frozen=True)
