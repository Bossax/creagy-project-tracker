# Creagy Project Tracker

Prototype project tracker routine for internal use.

## Architecture overview

- **Backend:** FastAPI application exposing project, task, and reporting endpoints. SQLAlchemy
  is used for persistence and can point to SQLite (default) or PostgreSQL via environment
  configuration.
- **Dashboard:** Streamlit app with tailored views for different personas. The UI consumes
  the FastAPI service and surfaces summary metrics, CRUD helpers, and workload tracking.
- **Database:** PostgreSQL is recommended for production-like usage. SQLite is used by
  default for local development and automated tests.

## Prerequisites

- Python 3.11+
- Optional: Docker & Docker Compose for containerised workflow.

## Local development

Clone the repository and install dependencies (including developer tooling):

```bash
git clone https://github.com/creagy/creagy-project-tracker.git
cd creagy-project-tracker
python -m venv .venv
source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
pip install -e .[dev]
```

### Running the FastAPI backend

By default the backend uses a local SQLite database. To switch to PostgreSQL provide a
`DATABASE_URL`, e.g. `postgresql+psycopg://user:password@localhost:5432/tracker`.

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000/docs` for the interactive API documentation.

### Running the Streamlit dashboard

Start the Streamlit UI once the backend is online. Point `API_BASE_URL` to the FastAPI
instance if it differs from the default `http://localhost:8000`.

```bash
export API_BASE_URL=http://localhost:8000  # Optional
streamlit run dashboard/app.py
```

The dashboard provides three role-based views:

- **Team Member:** Focuses on personal workload, progress updates, and weekly notes.
- **Project Manager:** Provides CRUD helpers for projects/tasks and burndown style charts.
- **Company Manager:** Surfaces portfolio-level metrics, budget utilisation, and delivery
  health.

## Testing and linting

Run automated tests (including API, schema, and reporting coverage):

```bash
pytest
```

### Prototype smoke tests

The prototype ships with end-to-end API tests in `tests/test_api_endpoints.py` that spin up
an in-memory SQLite database and exercise the CRUD and reporting flows exposed by the
FastAPI service. Run them directly whenever you make changes to the backend models or
service wiring:

```bash
pytest tests/test_api_endpoints.py
```

Optional linting with Ruff:

```bash
ruff check .
```

## Containerised environment

The repository ships with a Dockerfile and Compose setup that runs PostgreSQL, the FastAPI
backend, and the Streamlit dashboard together:

```bash
docker compose up --build
```

Services exposed locally:

- Backend API: <http://localhost:8000>
- Streamlit dashboard: <http://localhost:8501>
- PostgreSQL database: exposed on port `5432` for local tooling (username/password `tracker`).

Shut down the stack with `docker compose down`. Persisted database data lives in the
`pgdata` volume.

## Continuous integration

GitHub Actions run the workflow defined in `.github/workflows/ci.yml` on pushes and pull
requests. The pipeline installs the project in a clean environment, executes `ruff check .`,
and runs the full `pytest` suite to guard regressions.

## Contributing

Contributions are welcome! Please open an issue describing the improvement you would like
to make before submitting a pull request so we can coordinate efforts. When sending a PR,
include a short summary of the change and any relevant screenshots or logs.

## License

This prototype is distributed under the MIT License. See the [LICENSE](LICENSE) file for
full details once it is added to the repository.
