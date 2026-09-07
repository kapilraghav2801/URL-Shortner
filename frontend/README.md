# Smart Shortner Frontend

Simple React + Vite frontend for the Smart Shortner API.

## Run locally

From the repository root:

```bash
cd frontend
npm install
npm run dev
```

The Vite development server proxies `/api` requests to `http://127.0.0.1:8000`.

Make sure the FastAPI backend is running:

```bash
uvicorn app.main:app --reload
```

## Environment variables

For a deployed setup, create `frontend/.env`:

```env
VITE_API_BASE=https://your-api.example.com
VITE_SHORTENER_ORIGIN=https://your-short-domain.example.com
```

`VITE_API_BASE` is used for API calls. `VITE_SHORTENER_ORIGIN` is used when displaying/copying generated short links.
