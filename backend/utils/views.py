from django.db.models import QuerySet
from rest_framework.exceptions import ParseError
from typing import Any, Protocol


def prevent_not_null(*args: Any) -> None:
    for item in args:
        if item is None: raise ParseError("Null is not allowed in args.")


def parse_boolean_value(value: str, default: bool = False) -> bool:
    value = value.lower()
    if value in ["true", "1"]: return True
    if value in ["false", "0"]: return False
    return default
