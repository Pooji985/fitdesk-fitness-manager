# FitDesk Frontend

FitDesk's client is a React single-page app built with Vite and Tailwind CSS. API requests use `/api/v1`; Vite proxies `/api` to `http://127.0.0.1:8000` during development.

## Run

```powershell
cd frontend
npm install
npm run dev
```

Create a production bundle with `npm run build`. No frontend automated test runner is currently configured.
