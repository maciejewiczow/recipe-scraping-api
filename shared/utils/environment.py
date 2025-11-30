import functools
from pydantic import BaseModel, ValidationError
from shared.models.responses.HttpResponse import InternalServerErrorResponse


def validate_environment[T: BaseModel](model: type[T]):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                kwargs["env"] = model()
                return func(*args, **kwargs)
            except ValidationError:
                return InternalServerErrorResponse(
                    body="Internal server error: invalid env config"
                )

        return wrapper

    return decorator
