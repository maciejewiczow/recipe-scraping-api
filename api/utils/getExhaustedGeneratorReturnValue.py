from collections.abc import Generator
from typing import Any, Optional, TypeVar


T = TypeVar("T")


def getExhaustedGeneratorReturnValue(gen: Generator[Any, Any, T]) -> Optional[T]:
    try:
        next(gen)
    except StopIteration as e:
        return e.value
