# FitDesk Backend

FastAPI and SQLAlchemy API for FitDesk, using SQLite.

## Local setup

From the workspace root, create the environment and install dependencies:

```powershell
python -m venv backend\venv
backend\venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

Set `JWT_SECRET_KEY` in `backend/.env` to a random value of at least 32 characters. Keep it private. The configured business database is `backend/fitdesk.db`; credential hashes are stored in `backend/fitdesk-auth.db`. Do not point tests at either live database.

Provision a local account password from `backend/` using the project environment:

```powershell
.\venv\Scripts\python.exe -m app.cli set-password alex.morgan@fitdesk.io
```

Start the API from `backend/`:

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Interactive API docs are available at `http://127.0.0.1:8000/api/v1/docs`; health is at `/api/v1/health`.

## API areas

The versioned API includes authentication, role-specific dashboard metrics, classes/scheduling/weather, member bookings and cancellations, attendance, and Admin member management. Class creation, editing, and cancellation are Admin-only. Trainers can mark attendance only for their assigned classes.

## Tests

Tests are `unittest.TestCase` integration suites. They initialize and write to configured business and auth stores. Set `DATABASE_URL` and `AUTH_DATABASE_URL` to disposable database copies before running from the workspace root:

```powershell
backend\venv\Scripts\python.exe -m unittest discover -s tests/backend -p 'test*.py' -v
```

The frontend has no automated test runner configured; verify its production bundle with `npm run build` from `frontend/`.
