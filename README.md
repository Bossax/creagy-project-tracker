# Creagy Project Tracker

Web-based tracker for Creagy projects, tasks, and project activities. The application allows employees to create projects, manage associated tasks, assign month-level activities, and view project progress through a Gantt timeline and manday analytics.

## Tech Stack

- Python 3.10+
- Flask + SQLAlchemy (SQLite storage by default)
- Bootstrap 5, Chart.js, and Frappe Gantt on the frontend

## Getting Started

1. **Install dependencies**

   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt  # or `pip install -e .` if you prefer pyproject usage
   ```

   If you are using the `pyproject.toml`, you can alternatively run:

   ```bash
   pip install .
   ```

2. **Seed the database**

   ```bash
    python -m backend.seed
   ```

   This populates teams, employees, months, and the default activity types.

3. **Run the web app**

   ```bash
   python -m backend.app
   ```

   The development server starts on `http://0.0.0.0:8000`. You can change the port by editing the `app.run` call at the bottom of `backend/app.py`.

## Key Features

- **Employee selection on entry**: Pick an existing employee profile or create one on the spot; selection persists in the session.
- **Project management**: Create projects with required metadata, linking clients, teams, and budget.
- **Task assignment**: Only the project manager can add tasks, specifying manday, budget, and per-month activity allocations.
- **Timeline & analytics**:
  - Gantt chart showing project span and task windows (derived from assigned months).
  - Monthly manday chart distributing task mandays evenly across the assigned months.
  - Summary stats covering duration, total manday, and aggregated budgets.

## Development Notes

- The SQLite database is stored under `instance/creagy.db`. Delete the file to start fresh.
- Adjust `DATABASE_URL` in `backend/database.py` to target PostgreSQL, MySQL, etc.
- Static assets live in `static/`; Jinja templates under `templates/`.

## Testing

Set up your test environment and run:

```bash
pytest
```

Test scaffolding is minimal; add coverage as the app grows.
