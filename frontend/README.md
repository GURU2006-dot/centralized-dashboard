# NLAMP Command Center (Phase 4A)

React + Vite frontend for the SIH 26016 prototype. It talks to the existing FastAPI app through the Vite dev-server proxy (`/api` → `http://127.0.0.1:8000`). The browser never calls `localhost` directly.

All figures are **synthetic demonstration data**.

```bash
# terminal 1
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# terminal 2
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 and sign in with a demo directory account (password is not stored in this app).
