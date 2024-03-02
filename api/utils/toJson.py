from flask import jsonify
from pydantic import BaseModel


def toJson(obj: BaseModel):
    return jsonify(obj.model_dump())
