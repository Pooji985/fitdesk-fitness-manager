# FitDesk Fitness Manager

FitDesk is a React/Vite frontend with a FastAPI/SQLAlchemy backend and SQLite storage. It supports JWT sign-in, role-based access, class scheduling, outdoor forecasts, member bookings/cancellations, attendance, and Admin member management.

## Run locally

1. Configure `JWT_SECRET_KEY` in `backend/.env` with a random value of at least 32 characters. Keep `.env` private.
2. Start the API from `backend/` using the project Python environment:

	```powershell
	.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
	```

3. In another terminal, start the frontend:

	```powershell
	cd frontend
	npm install
	npm run dev
	```

The API uses `backend/fitdesk.db`; password hashes use the separate `backend/fitdesk-auth.db`. Existing seed accounts have no documented default passwords; provision a local demo password with `python -m app.cli set-password <email>` from `backend/`.

## Tests and build

Backend tests are `unittest` integration tests. They initialize and write to their configured databases, so set `DATABASE_URL` and `AUTH_DATABASE_URL` to disposable copies before running:

```powershell
backend\venv\Scripts\python.exe -m unittest discover -s tests/backend -p 'test*.py' -v
```

Build the frontend with `cd frontend; npm run build`. No frontend automated test runner is currently configured.

See [docs/USER_GUIDE.md](docs/USER_GUIDE.md) for role workflows and known scope limits. API docs are at `/api/v1/docs` while the backend is running.
