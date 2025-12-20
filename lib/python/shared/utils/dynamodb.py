from dataclasses import dataclass
from datetime import datetime
from types import UnionType
from typing import Annotated, Literal, Type, get_args, get_type_hints
import botocore
import botocore.exceptions
from pydantic import (
    BaseModel,
    PlainSerializer,
)
from shared.utils.find import find

KeyType = Literal["hash"] | Literal["sort"]


@dataclass
class PrimaryKey:
    key_type: KeyType = "hash"


class MissingPrimaryKey(Exception):
    pass


def metadata_has_primary_key_with_type(metadata: list, key_type: KeyType) -> bool:
    primaryKeyMetadata = find(metadata, lambda x: isinstance(x, PrimaryKey))

    return primaryKeyMetadata is not None and primaryKeyMetadata.key_type == key_type


def is_base_model_subclass_unions(type: Type | UnionType):
    if not isinstance(type, UnionType):
        return issubclass(type, BaseModel)

    return any(issubclass(arg, BaseModel) for arg in get_args(type))


class DynamodbModel(BaseModel):
    @classmethod
    def from_dynamo(cls, data: dict):
        return cls.model_validate(data)

    @classmethod
    def top_level_fields_projection(cls) -> str:
        types = get_type_hints(cls)

        return ",".join(
            field_name
            for field_name, field_info in cls.model_fields.items()
            if not field_info.exclude
            and not is_base_model_subclass_unions(types[field_name])
        )

    @classmethod
    def get_primary_key_name(cls, key_type: KeyType = "hash") -> str:
        try:
            return next(
                field_name
                for field_name, field_info in cls.model_fields.items()
                if not field_info.exclude
                and metadata_has_primary_key_with_type(
                    field_info.metadata,
                    key_type,
                )
            )
        except StopIteration:
            raise MissingPrimaryKey() from None


def is_not_found_exception(e: botocore.exceptions.ClientError) -> bool:
    return e.response.get("Error", {}).get("Code") == "ResourceNotFoundException"


class DynamoDBItemNotFoundException(Exception):
    pass


TTLField = Annotated[datetime, PlainSerializer(lambda x: int(x.timestamp()))]
