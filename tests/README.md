# FitDesk Tests

Backend integration tests are `unittest.TestCase` suites under `tests/backend`. They initialize the configured business database and create/update test data, so never point them at the live stores.

Set `DATABASE_URL` and `AUTH_DATABASE_URL` to disposable copies of `backend/fitdesk.db` and `backend/fitdesk-auth.db`, then run from the workspace root:

```powershell
backend\venv\Scripts\python.exe -m unittest discover -s tests/backend -p 'test*.py' -v
```

The frontend has no automated test runner configured. Run `npm run build` from `frontend/` for a production bundle check.
