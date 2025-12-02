import functools
from pydantic import BaseModel


def dump_response(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)

        if isinstance(result, BaseModel):
            return result.model_dump()

        return result

    return wrapper
