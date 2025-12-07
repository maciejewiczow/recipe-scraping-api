from dataclasses import dataclass
import functools
from typing import Any, Callable, Type
from aws_lambda_powertools import Logger
from openai import InternalServerError
from pydantic import BaseModel, TypeAdapter, ValidationError
from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventV2Model
from aws_lambda_powertools.utilities.parser import parse
from shared.models.responses.HttpResponse import (
    BadRequestResponse,
    HttpResponse,
    InternalServerErrorResponse,
)

openapi_meta_key_name = "_openapi"

RequestParamType = type[BaseModel] | TypeAdapter[BaseModel | None] | None


@dataclass
class OpenApiMetadata:
    responses: list[type[HttpResponse]]
    body: RequestParamType | None
    queryParams: RequestParamType | None
    pathParams: RequestParamType | None


def handle_param(
    paramType: RequestParamType,
    value: dict[str, Any] | str | None,
    paramName: str,
    log: Logger,
):
    try:
        match (paramType, value):
            case (TypeAdapter(), str()):
                return paramType.validate_json(value)
            case (TypeAdapter(), dict() as d) if len(d) == 0:
                return paramType.validate_python(None)
            case (TypeAdapter(), _):
                return paramType.validate_python(value)
            case (None, None):
                return BadRequestResponse(body=f"{paramName} not allowed")
            case (None, dict() as d) if len(d) != 0:
                return BadRequestResponse(body=f"{paramName} not allowed")
            case (Type(), str()):
                return paramType.model_validate_json(value)
            case (Type(), dict() as d) if len(d) == 0:
                return paramType.model_validate(None)
            case (Type(), _):
                return paramType.model_validate(value)
            case _:
                return None
    except ValidationError:
        log.exception(f"Invalid {paramName}")
        return BadRequestResponse(body=f"Invalid {paramName}")


def http_endpoint(
    log: Logger,
    *,
    responses: list[type[HttpResponse]],
    body: RequestParamType = None,
    query: RequestParamType = None,
    path: RequestParamType = None,
):
    def wrapper(func: Callable):
        if BadRequestResponse not in responses:
            responses.append(BadRequestResponse)

        if InternalServerErrorResponse not in responses:
            responses.append(InternalServerErrorResponse)

        setattr(
            func,
            openapi_meta_key_name,
            OpenApiMetadata(
                responses=responses,
                body=body,
                queryParams=query,
                pathParams=path,
            ),
        )

        @functools.wraps(func)
        def wrapped(raw_event: dict[str, Any], *args, **kwargs):
            try:
                event = parse(model=APIGatewayProxyEventV2Model, event=raw_event)
            except ValidationError:
                log.exception("Event validation error")
                return InternalServerErrorResponse(body="Invalid lambda event")

            result = handle_param(body, event.body, "body", log)  # type: ignore

            if isinstance(result, HttpResponse):
                return result

            kwargs["body"] = result

            result = handle_param(query, event.queryStringParameters, "query", log)

            if isinstance(result, HttpResponse):
                return result

            kwargs["query"] = result

            result = handle_param(path, event.pathParameters, "path", log)

            if isinstance(result, HttpResponse):
                return result

            kwargs["path"] = result

            return func(event, *args, **kwargs)

        return wrapped

    return wrapper
