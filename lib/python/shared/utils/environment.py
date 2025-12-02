import functools
from aws_lambda_powertools import Logger
from pydantic import ValidationError
from pydantic_settings import BaseSettings
from shared.models.responses.HttpResponse import InternalServerErrorResponse
import os


def validate_environment[T: BaseSettings](model: type[T], log: Logger):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                kwargs["env"] = model()
                return func(*args, **kwargs)
            except ValidationError:
                log.exception("Invalid lambda env config", {"env": os.environ})
                return InternalServerErrorResponse(
                    body="Internal server error: invalid env config"
                )

        return wrapper

    return decorator
