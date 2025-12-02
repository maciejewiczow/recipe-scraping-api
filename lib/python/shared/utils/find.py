from typing import Callable, Iterable


def find[T](iterable: Iterable[T], predicate: Callable[[T], bool]) -> T | None:
    try:
        return next(x for x in iterable if predicate(x))
    except StopIteration:
        return None
