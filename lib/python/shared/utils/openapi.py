from dataclasses import dataclass
import functools
from typing import Any, Callable
from aws_lambda_powertools import Logger
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


def _serialize_request_param(param: RequestParamType):
    if isinstance(param, TypeAdapter):
        return param.json_schema()

    if param is None:
        return None

    if issubclass(param, BaseModel):
        return param.model_json_schema()


class Tag(BaseModel):
    name: str
    description: str | None = None

    def __hash__(self):
        return hash(self.name)


@dataclass
class OpenApiMetadata:
    responses: list[type[HttpResponse]]
    body: RequestParamType | None
    queryParams: RequestParamType | None
    pathParams: RequestParamType | None
    operationId: str | None
    description: str | None
    summary: str | None
    tags: list[Tag]

    def to_dict(self):
        return {
            "responseNames": [
                res.__name__.replace("[", "_").replace("]", "_")
                for res in self.responses
            ],
            "body": _serialize_request_param(self.body),
            "queryParams": _serialize_request_param(self.queryParams),
            "pathParams": _serialize_request_param(self.pathParams),
            "operationId": self.operationId,
            "description": self.description,
            "summary": self.summary,
            "tags": [tag.name for tag in self.tags],
        }


def openapi_endpoint(
    log: Logger,
    *,
    responses: list[type[HttpResponse]],
    body: RequestParamType = None,
    query: RequestParamType = None,
    path: RequestParamType = None,
    operationId: str | None = None,
    description: str | None = None,
    summary: str | None = None,
    tags: list[Tag] = [],
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
                operationId=operationId,
                description=description,
                summary=summary,
                tags=tags,
            ),
        )

        @functools.wraps(func)
        def wrapped(raw_event: dict[str, Any], *args, **kwargs):
            try:
                event = parse(model=APIGatewayProxyEventV2Model, event=raw_event)
            except ValidationError:
                log.exception("Event validation error")
                return InternalServerErrorResponse(body="Invalid lambda event")

            result = _handle_param(body, event.body, "body", log)  # type: ignore

            if isinstance(result, HttpResponse):
                return result

            kwargs["body"] = result

            result = _handle_param(query, event.queryStringParameters, "query", log)

            if isinstance(result, HttpResponse):
                return result

            kwargs["query"] = result

            result = _handle_param(path, event.pathParameters, "path", log)

            if isinstance(result, HttpResponse):
                return result

            kwargs["path"] = result

            return func(event, *args, **kwargs)

        return wrapped

    return wrapper


def _handle_param(
    paramType: RequestParamType,
    value: dict[str, Any] | str | None,
    paramName: str,
    log: Logger,
):
    with log.append_context_keys(paramName=paramName):
        try:
            match (paramType, value):
                case (TypeAdapter(), str()):
                    log.debug("Type adapter + string param")
                    return paramType.validate_json(value)
                case (TypeAdapter(), dict() as d) if len(d) == 0:
                    log.debug("Type adapter + empty dict")
                    return paramType.validate_python(None)
                case (TypeAdapter(), _):
                    log.debug("Type adapter + other")
                    return paramType.validate_python(value)
                case (type(), str()):
                    log.debug("BaseModel + string param")
                    return paramType.model_validate_json(value)
                case (type(), dict() as d) if len(d) == 0:
                    log.debug("BaseModel + empty dict")
                    return paramType.model_validate(None)
                case (type(), _):
                    log.debug("BaseModel + other")
                    return paramType.model_validate(value)
                case (None, None):
                    log.debug("None param + None value")
                    return None
                case (None, dict() as d) if len(d) != 0:
                    log.debug("None param + Empty dict")
                    return None
                case (None, t) if t is not None:
                    log.debug("None param + other not none")
                    return BadRequestResponse(body=f"{paramName} not allowed")
                case _:
                    log.debug("Other")
                    return None
        except ValidationError:
            log.exception(f"Invalid {paramName}")
            return BadRequestResponse(body=f"Invalid {paramName}")
