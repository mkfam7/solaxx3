from typing import Any


def getnext(iterable: list, default: Any = 0):
    for item in iterable:
        yield item
    while True:
        yield default
