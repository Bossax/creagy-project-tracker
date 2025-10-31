"""FastAPI application entrypoint."""

from fastapi import FastAPI

from .config import get_settings
from .routers import projects, tasks

app = FastAPI(title="Creagy Project Tracker")

app.include_router(projects.router)
app.include_router(tasks.router)


@app.on_event("startup")
def startup_event() -> None:
    """Load settings on startup to ensure configuration is valid."""

    get_settings()


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """Health check endpoint to confirm service availability."""

    return {"status": "ok"}
