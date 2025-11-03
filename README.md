# Creagy Project Tracker

Web app for managing Creagy projects, tasks, and activity schedules. Employees log in with their name, create projects, assign tasks with month-by-month activities, and review project health via a Gantt timeline, manday bar chart, and summary statistics.

## Tech Stack

- **Backend:** Python 3.10+, Flask, SQLAlchemy, SQLite (default)
- **Frontend:** React (Vite), Chart.js via `react-chartjs-2`, Frappe Gantt
- **Auth:** Cookie-based Flask session keyed by employee profile

## Backend Setup

> Commands below assume Windows PowerShell. Swap in your shell’s activation command if you use something else.

```powershell
py -3 -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt    # or: pip install .
python -m backend.seed             # seeds teams, employees, months, activities
python -m backend.app              # runs API server on http://localhost:8000
```

If `python` resolves to Python 2 for you, stick with `py -3` in the commands above.

Environment variables:

- `DATABASE_URL` – override SQLite path if needed
- `SECRET_KEY` – Flask session secret
- `CORS_ALLOWED_ORIGINS` – comma-separated list for dev origins (defaults allow localhost)

## Frontend Setup (Vite + React)

```powershell
cd frontend
npm install
npm run dev    # launches http://localhost:5173 with proxy to Flask API
```

### Windows tips

- If you use `cmd.exe`, swap the activation step for `.\.venv\Scripts\activate.bat`.
- To set temporary environment variables in PowerShell (for example when pointing to a cloud DB), use:
  ```powershell
  $env:DATABASE_URL = "postgresql://user:pass@host/db"
  $env:SECRET_KEY = "dev-secret"
  ```
  For persistent values use `setx` (requires a new shell to pick up the change).
- When you’re ready for production, build the SPA and serve it from Flask:
  ```powershell
  cd frontend
  npm run build         # emits frontend/dist
  cd ..
  python -m backend.app # Flask now serves both API and built assets on port 8000
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
