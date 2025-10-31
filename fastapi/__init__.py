"""Minimal FastAPI stand-ins for offline testing environments."""
from __future__ import annotations

from typing import Any, Callable, Iterable


class FastAPI:
    """Lightweight shim of :class:`fastapi.FastAPI` for tests without the dependency."""

    def __init__(self, *, title: str | None = None) -> None:
        self.title = title or "FastAPI"
        self.routers: list[Any] = []
        self.routes: list[tuple[str, str, Callable[..., Any]]] = []

    def include_router(self, router: Any) -> None:
        self.routers.append(router)

    def get(
        self,
        path: str,
        *,
        tags: Iterable[str] | None = None,
        response_model: Any | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.routes.append(("GET", path, func))
            return func

        return decorator

    def on_event(self, event: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return func

        return decorator


class APIRouter:
    """Simplified API router."""

    def __init__(self, *, prefix: str = "", tags: Iterable[str] | None = None) -> None:
        self.prefix = prefix
        self.tags = list(tags or [])
        self.routes: list[tuple[str, str, Callable[..., Any]]] = []

    def get(
        self,
        path: str,
        *,
        response_model: Any | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.routes.append(("GET", path, func))
            return func

        return decorator


def Depends(dependency: Callable[..., Any]) -> Callable[..., Any]:
    """Placeholder for :func:`fastapi.Depends`. Returns dependency unchanged."""

    return dependency


__all__ = ["FastAPI", "APIRouter", "Depends"]
