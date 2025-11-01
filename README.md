# Creagy Project Tracker

The Creagy Project Tracker replaces spreadsheet-based project tracking with a modular FastAPI backend and Streamlit dashboard. The platform supports role-based workflows for consultants, project managers, and company leadership while keeping a single source of truth in PostgreSQL.

## Architecture

- **Backend:** FastAPI + SQLAlchemy ORM, PostgreSQL persistence, REST endpoints for projects, tasks, and metrics.
- **Frontend:** Streamlit dashboard with dedicated views for each role.
- **Data:** Demo dataset stored in `backend/data/sample_data.json`; seeded via `python -m backend.seed`.
- **Containerization:** Docker Compose orchestrates the PostgreSQL database, backend API, and dashboard UI.

## Prerequisites

- Python 3.11+
- PostgreSQL 14+ (for local development)
- Node dependencies are not required.

Recommended optional tools:

- `pipx` or virtual environments for dependency isolation
- Docker Desktop (or compatible engine) for containerized workflows

## Getting Started (Local)

1. **Clone & install**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # macOS/Linux
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **Configure environment variables**
   ```bash
   copy .env.example .env  # adjust DATABASE_URL / API_BASE_URL as needed
   ```

3. **Prepare the database**
   - Ensure PostgreSQL is running and matches `DATABASE_URL`.
   - Seed demo data:
     ```bash
     python -m backend.seed
     ```

4. **Run the services**
   ```bash
   uvicorn backend.main:app --reload
   streamlit run dashboard/app.py
   ```

5. **Open the tools**
   - API docs: http://localhost:8000/docs
   - Dashboard: http://localhost:8501

## Role-Based Features

- **Team Member**
  - Review assigned tasks, update progress and status, submit remarks.
  - Workload view highlights total man-days and deadlines.

- **Project Manager**
  - Create and edit projects, manage task backlogs, assign team members.
  - Monitor project pipelines and task progress in real time.

- **Company Manager**
  - Portfolio dashboard summarizing project status, resource utilization, and completion KPIs.
  - Visual charts support planning and performance conversations.

## API Overview

| Endpoint           | Method | Description                      |
|-------------------|--------|----------------------------------|
| `/health`          | GET    | Service readiness check          |
| `/projects`        | CRUD   | Manage projects                  |
| `/projects/{id}`   | CRUD   | Single project operations        |
| `/tasks`           | CRUD   | Manage tasks                     |
| `/tasks/{id}`      | CRUD   | Single task operations           |
| `/tasks/assignees/list` | GET | Distinct list of task assignees |
| `/metrics/portfolio` | GET | Portfolio-level KPIs             |
| `/metrics/team`    | GET    | Resource utilization by assignee |

All endpoints return JSON responses. See the automatically generated OpenAPI docs at `/docs` for request/response schemas.

## Docker Workflow

1. **Build and start**
   ```bash
   docker compose up --build
   ```

2. **Seed demo data inside the backend container**
   ```bash
   docker compose exec backend python -m backend.seed
   ```

3. **Access**
   - API: http://localhost:8000
   - Dashboard: http://localhost:8501

The compose file provisions three services:

- `db`: PostgreSQL database with persistent volume `db-data`.
- `backend`: FastAPI application served by Uvicorn.
- `dashboard`: Streamlit frontend connected to the API.

## Testing

Basic smoke tests live under `tests/`. Run them with:

```bash
pytest
```

## Project Layout

```
backend/
  config.py        # App configuration via pydantic-settings
  crud.py          # Database operations
  data/            # Sample JSON dataset for seeding
  main.py          # FastAPI application entry point
  models.py        # SQLAlchemy ORM models
  routers/         # Route modules for projects, tasks, metrics
  schemas.py       # Pydantic schemas for request/response
  seed.py          # Demo data loader
dashboard/
  app.py           # Streamlit dashboard with role-based tabs
tests/
  test_health.py   # Example API test
```

## Next Steps

- Add authentication & authorization for production use.
- Expand automated test coverage for CRUD and dashboard interactions.
- Integrate background jobs (e.g., nightly summary emails) as future enhancements.
