from dataclasses import dataclass
from typing import Literal, get_type_hints
import botocore
import botocore.exceptions
from pydantic import (
    BaseModel,
    SerializerFunctionWrapHandler,
    model_serializer,
)
from boto3.dynamodb.types import TypeSerializer, TypeDeserializer

KeyType = Literal["hash"] | Literal["sort"]


@dataclass
class PrimaryKey:
    key_type: KeyType = "hash"


class MissingPrimaryKey(Exception):
    pass


class DynamodbModel(BaseModel):
    @model_serializer(mode="wrap")
    def serialize_model(self, handler: SerializerFunctionWrapHandler):
        dump = handler(self)

        if isinstance(dump, dict):
            serializer = TypeSerializer()

            return {key: serializer.serialize(value) for key, value in dump.items()}

        return dump

    @classmethod
    def from_dynamo(cls, data: dict):
        deserializer = TypeDeserializer()

        return cls.model_validate(
            {key: deserializer.deserialize(value) for key, value in data.items()}
        )

    @classmethod
    def top_level_fields_projection(cls) -> str:
        types = get_type_hints(cls)

        return ",".join(
            field_name
            for field_name, field_info in cls.model_fields.items()
            if not field_info.exclude and not issubclass(types[field_name], BaseModel)
        )

    @classmethod
    def get_primary_key_name(cls, keyType: KeyType = "hash") -> str:
        try:
            return next(
                field_name
                for field_name, field_info in cls.model_fields.items()
                if not field_info.exclude
                and isinstance(field_info.annotation, PrimaryKey)
                and field_info.annotation.key_type == keyType
            )
        except StopIteration:
            raise MissingPrimaryKey()


def is_not_found_exception(e: botocore.exceptions.ClientError) -> bool:
    return e.response.get("Error", {}).get("Code") == "ResourceNotFoundException"


class DynamoDBItemNotFoundException(Exception):
    pass
