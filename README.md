# Creagy Project Tracker

Web app for managing Creagy projects, tasks, and activity schedules. Employees log in with their name, create projects, assign tasks with month-by-month activities, and review project health via a Gantt timeline, manday bar chart, and summary statistics.

## Tech Stack

- **Backend:** Python 3.10+, Flask, SQLAlchemy, SQLite (default)
- **Frontend:** React (Vite), Chart.js via `react-chartjs-2`, Frappe Gantt
- **Auth:** Cookie-based Flask session keyed by employee profile

## Backend Setup

```bash
python -m venv .venv
.\\.venv\\Scripts\\activate
pip install -r requirements.txt  # or `pip install .`
python -m backend.seed           # one-time seed (employees, teams, months, activities)
python -m backend.app            # serves JSON API at http://localhost:8000
```

Environment variables:

- `DATABASE_URL` – override SQLite path if needed
- `SECRET_KEY` – Flask session secret
- `CORS_ALLOWED_ORIGINS` – comma-separated list for dev origins (defaults allow localhost)

## Frontend Setup (Vite + React)

```bash
cd frontend
npm install
npm run dev     # http://localhost:5173 with proxy to the backend API
```

Build for production and let Flask serve the compiled assets:

```bash
npm run build           # outputs to frontend/dist
python -m backend.app   # now serves the React app + API on port 8000
```

## Core Features

- **Employee session:** Select or create an employee profile; session persists in cookies.
- **Project lifecycle:** Capture client, manager, team, budget, and schedule metadata.
- **Task planning:** Project manager only; assign manday/budget and map activities per month.
- **Visual analytics:**
  - Frappe Gantt timeline for project and tasks
  - Monthly manday bar chart with Chart.js
  - Summary box (duration, total manday, total budget)

## API Overview

- `GET /api/session` – current user; `POST /api/session` – login; `DELETE /api/session` – logout
- `GET/POST /api/employees` – list or create employees
- `GET /api/teams|clients|activities|months` – lookup metadata
- `GET /api/projects` – project summaries; `POST /api/projects` – create project
- `GET /api/projects/<id>` – detail with tasks and visualization payloads
- `POST /api/projects/<id>/tasks` – add task (+ month/activity assignments)

## Development Notes

- SQLite database lives in `instance/creagy.db`. Delete to reset.
- Update `backend/database.py` for alternative databases.
- Vite dev server proxies `/api` calls to `localhost:8000`; adjust `vite.config.js` as needed.

## Testing

```bash
pytest
```

Add additional tests alongside new features. Frontend tests can be added via Vite/Jest or Vitest if desired.
