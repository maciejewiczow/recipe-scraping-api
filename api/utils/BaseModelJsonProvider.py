import json
from flask.json.provider import JSONProvider
from pydantic import BaseModel


class BaseModelJsonProvider(JSONProvider):
    def dumps(self, obj):
        if isinstance(obj, BaseModel):
            return json.dumps(obj.model_dump())

        return json.dumps(obj)

    def loads(self, value):
        return json.loads(value)
