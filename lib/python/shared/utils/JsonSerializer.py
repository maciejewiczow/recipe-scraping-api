from typing import Any
from pydantic import BaseModel, SerializerFunctionWrapHandler, WrapSerializer


def serialize_to_json(data: Any, handler: SerializerFunctionWrapHandler):
    if isinstance(data, BaseModel):
        return data.model_dump_json()

    return handler(data)


JsonSerializer = WrapSerializer(serialize_to_json)
