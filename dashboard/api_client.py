"""Lightweight HTTP client for communicating with the FastAPI backend."""
from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any, Mapping, MutableMapping, Optional
from urllib.parse import urljoin

import requests
from requests import Response


class APIClientError(RuntimeError):
    """Raised when the API client cannot fulfil a request."""


@dataclass(slots=True)
class APIClient:
    """Simple wrapper around :mod:`requests` with a configurable base URL."""

    base_url: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    timeout: float = float(os.getenv("API_TIMEOUT", "10"))

    def _prepare_url(self, path: str) -> str:
        """Return an absolute URL using the configured base path."""

        if not path:
            msg = "Path must be provided when building the request URL."
            raise APIClientError(msg)
        return urljoin(self.base_url.rstrip("/") + "/", path.lstrip("/"))

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Response:
        """Execute an HTTP request and return the underlying response."""

        url = self._prepare_url(path)
        try:
            response = requests.request(
                method,
                url,
                params=params,
                json=json,
                headers=headers,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:  # pragma: no cover - exercised via UI
            msg = f"Failed to call API endpoint {url}: {exc}"
            raise APIClientError(msg) from exc

        if response.status_code >= 400:
            details: MutableMapping[str, Any]
            try:
                details = response.json()
            except ValueError:  # pragma: no cover - defensive
                details = {"detail": response.text}
            msg = (
                "API request failed with status "
                f"{response.status_code}: {details.get('detail', details)}"
            )
            raise APIClientError(msg)
        return response

    def get_json(
        self,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """Send a GET request and decode the JSON payload."""

        response = self.request("GET", path, params=params)
        try:
            return response.json()
        except ValueError as exc:  # pragma: no cover - defensive
            msg = "API response did not contain valid JSON."
            raise APIClientError(msg) from exc

    def list_projects(self) -> list[MutableMapping[str, Any]]:
        """Return the collection of projects from the backend API."""

        projects = self.get_json("/projects/")
        return list(projects)

    def list_tasks(self, *, project_id: Optional[int] = None) -> list[MutableMapping[str, Any]]:
        """Return the collection of tasks, optionally filtered by project."""

        params = {"project_id": project_id} if project_id is not None else None
        tasks = self.get_json("/tasks/", params=params)
        return list(tasks)

    def update_task(self, task_id: int, payload: Mapping[str, Any]) -> MutableMapping[str, Any]:
        """Update a task via the backend API and return the updated object."""

        response = self.request("PUT", f"/tasks/{task_id}", json=dict(payload))
        try:
            return response.json()
        except ValueError as exc:  # pragma: no cover - defensive
            msg = "API response did not contain valid JSON."
            raise APIClientError(msg) from exc

    def health(self) -> Mapping[str, Any]:
        """Return the backend service health payload."""

        return self.get_json("/health")


__all__ = ["APIClient", "APIClientError"]
