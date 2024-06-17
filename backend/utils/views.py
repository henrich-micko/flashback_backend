from rest_framework.exceptions import ParseError
from typing import Any


def prevent_not_null(*args: Any) -> None:
    for item in args:
        if item is None: raise ParseError("Null is not allowed in args.")