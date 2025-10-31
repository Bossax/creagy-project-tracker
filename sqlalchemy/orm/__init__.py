"""Simplified ORM primitives used in tests."""
from __future__ import annotations

from typing import Any, Sequence

from .. import ScalarResult


class Session:
    """Very small placeholder for :class:`sqlalchemy.orm.Session`."""

    def __init__(self) -> None:
        self._store: dict[type[Any], list[Any]] = {}

    def get(self, model: type[Any], pk: Any) -> Any:  # pragma: no cover - not used
        raise RuntimeError("Database access is unavailable in the test environment")

    def scalars(self, statement: Any) -> ScalarResult:
        items: Sequence[Any] = self._store.get(getattr(statement, "model", object()), [])
        return ScalarResult(items)

    def add(self, obj: Any) -> None:  # pragma: no cover - not used
        self._store.setdefault(type(obj), []).append(obj)

    def commit(self) -> None:  # pragma: no cover - not used
        return None

    def refresh(self, obj: Any) -> None:  # pragma: no cover - not used
        return None

    def delete(self, obj: Any) -> None:  # pragma: no cover - not used
        try:
            self._store[type(obj)].remove(obj)
        except (KeyError, ValueError):
            pass


class _Metadata:
    def create_all(self, bind: Any | None = None) -> None:  # pragma: no cover - inert
        return None


def declarative_base() -> type[Any]:
    class Base:
        metadata = _Metadata()

        def __init__(self, **kwargs: Any) -> None:
            for key, value in kwargs.items():
                setattr(self, key, value)

    return Base


class sessionmaker:
    """Factory producing :class:`Session` objects."""

    def __init__(self, **_: Any) -> None:
        pass

    def __call__(self, *args: Any, **kwargs: Any) -> Session:
        return Session()


class relationship:
    """Descriptor establishing simple attribute defaults for relationships."""

    def __init__(
        self,
        target: str | type[Any],
        *,
        back_populates: str | None = None,
        cascade: str | None = None,
        passive_deletes: bool | None = None,
    ) -> None:
        self.target = target
        self.back_populates = back_populates
        self.cascade = cascade
        self.passive_deletes = passive_deletes
        self.name: str | None = None

    def __set_name__(self, owner: type[Any], name: str) -> None:
        self.name = name

    def __get__(self, instance: Any, owner: type[Any]) -> Any:
        if instance is None:
            return self
        if self.name is None:
            raise AttributeError("relationship descriptor improperly configured")
        if self.name not in instance.__dict__:
            default: Any = [] if self._is_collection_name(self.name) else None
            instance.__dict__[self.name] = default
        return instance.__dict__[self.name]

    def __set__(self, instance: Any, value: Any) -> None:
        if self.name is None:
            raise AttributeError("relationship descriptor improperly configured")
        instance.__dict__[self.name] = value

    @staticmethod
    def _is_collection_name(name: str) -> bool:
        return name.endswith("s")


__all__ = [
    "Session",
    "declarative_base",
    "relationship",
    "sessionmaker",
]
