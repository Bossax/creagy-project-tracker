"""Tiny subset of SQLAlchemy interfaces used for offline testing."""
from __future__ import annotations

from typing import Any, Iterable, Iterator, Sequence


class _Type:
    def __repr__(self) -> str:  # pragma: no cover - trivial
        return self.__class__.__name__


class Integer(_Type):
    pass


class String(_Type):
    def __init__(self, length: int | None = None) -> None:
        self.length = length


class Float(_Type):
    pass


class Date(_Type):
    pass


class Text(_Type):
    pass


class ForeignKey:
    def __init__(self, target: str, ondelete: str | None = None) -> None:
        self.target = target
        self.ondelete = ondelete


class Column:
    """Descriptor that stores attribute values on instances."""

    def __init__(
        self,
        column_type: Any,
        primary_key: bool = False,
        index: bool = False,
        nullable: bool = True,
        default: Any | None = None,
        **_: Any,
    ) -> None:
        self.column_type = column_type
        self.primary_key = primary_key
        self.index = index
        self.nullable = nullable
        self.default = default
        self.name: str | None = None

    def __set_name__(self, owner: type[Any], name: str) -> None:
        self.name = name

    def __get__(self, instance: Any, owner: type[Any]) -> Any:
        if instance is None:
            return self
        return instance.__dict__.get(self.name or "", self.default)

    def __set__(self, instance: Any, value: Any) -> None:
        instance.__dict__[self.name or ""] = value


class SelectStatement:
    def __init__(self, model: type[Any]) -> None:
        self.model = model
        self._order_by: Any | None = None
        self._filters: list[Any] = []

    def order_by(self, clause: Any) -> "SelectStatement":
        self._order_by = clause
        return self

    def where(self, clause: Any) -> "SelectStatement":
        self._filters.append(clause)
        return self


def select(model: type[Any]) -> SelectStatement:
    return SelectStatement(model)


class Engine:
    def __init__(self, url: str, *, connect_args: dict[str, Any] | None = None) -> None:
        self.url = url
        self.connect_args = connect_args or {}


def create_engine(url: str, connect_args: dict[str, Any] | None = None) -> Engine:
    return Engine(url, connect_args=connect_args)


class ScalarResult:
    def __init__(self, items: Sequence[Any]) -> None:
        self._items = list(items)

    def all(self) -> list[Any]:
        return list(self._items)


__all__ = [
    "Column",
    "Date",
    "Float",
    "ForeignKey",
    "Integer",
    "String",
    "Text",
    "create_engine",
    "select",
]
