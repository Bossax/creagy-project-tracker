"""Minimal subset of Pydantic used for the project tests."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generic, TypeVar, get_args, get_origin

_T = TypeVar("_T")


@dataclass
class FieldInfo(Generic[_T]):
    default: Any = None
    default_factory: Callable[[], Any] | None = None
    metadata: dict[str, Any] | None = None

    def get_default(self) -> Any:
        if self.default_factory is not None:
            return self.default_factory()
        return self.default


def Field(
    default: Any = None,
    *,
    default_factory: Callable[[], Any] | None = None,
    **metadata: Any,
) -> FieldInfo[Any]:
    return FieldInfo(default=default, default_factory=default_factory, metadata=metadata or None)


class ConfigDict(dict):
    """Lightweight stand-in for the mapping used by Pydantic."""


class ValidationError(Exception):
    """Exception raised when validation fails in the minimal BaseModel implementation."""


class BaseModel:
    """Very small drop-in replacement for :class:`pydantic.BaseModel`."""

    model_config: ConfigDict = ConfigDict()

    def __init__(self, **data: Any) -> None:
        annotations = getattr(self.__class__, "__annotations__", {})
        for name in annotations:
            value = self._pop_value(name, data)
            setattr(self, name, value)
        for name, value in data.items():
            setattr(self, name, value)

    @classmethod
    def _get_field_info(cls, name: str) -> FieldInfo[Any] | None:
        value = getattr(cls, name, None)
        if isinstance(value, FieldInfo):
            return value
        return None

    @classmethod
    def _get_default(cls, name: str) -> Any:
        info = cls._get_field_info(name)
        if info is not None:
            return info.get_default()
        return getattr(cls, name, None)

    @classmethod
    def _is_required(cls, name: str) -> bool:
        info = cls._get_field_info(name)
        return info is not None and info.default is ...

    @classmethod
    def _pop_value(cls, name: str, data: dict[str, Any]) -> Any:
        if name in data:
            return data.pop(name)
        if cls._is_required(name):
            raise ValidationError(f"Field '{name}' is required")
        return cls._get_default(name)

    @classmethod
    def model_validate(cls, obj: Any) -> "BaseModel":
        if isinstance(obj, cls):
            return obj
        annotations = getattr(cls, "__annotations__", {})
        data: dict[str, Any] = {}
        from_attributes = bool(cls.model_config.get("from_attributes"))
        for name in annotations:
            if isinstance(obj, dict):
                value = obj.get(name, cls._get_default(name))
            elif from_attributes and hasattr(obj, name):
                value = getattr(obj, name)
            else:
                value = cls._get_default(name)
            value = cls._coerce_value(annotations[name], value)
            data[name] = value
        return cls(**data)

    @staticmethod
    def _coerce_value(field_type: Any, value: Any) -> Any:
        origin = get_origin(field_type)
        args = get_args(field_type)
        if origin in {list, list} and args:
            inner = args[0]
            if isinstance(value, list) and hasattr(inner, "model_validate"):
                return [inner.model_validate(item) for item in value]
        if hasattr(field_type, "model_validate") and value is not None and not isinstance(value, field_type):
            return field_type.model_validate(value)
        return value

    def model_dump(self, *, exclude_unset: bool = False) -> dict[str, Any]:
        annotations = getattr(self.__class__, "__annotations__", {})
        data = {name: getattr(self, name) for name in annotations}
        if not exclude_unset:
            extras = {
                key: value
                for key, value in self.__dict__.items()
                if key not in data
            }
            data.update(extras)
        return data


__all__ = ["BaseModel", "ConfigDict", "Field", "ValidationError"]
