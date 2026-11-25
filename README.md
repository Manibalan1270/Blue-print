# Blue-print (DevPulse AI)

Checks whether a code change actually matches its requirement, estimates effort and impact,
and flags team risks (bus factor, burnout, hotspots).

- **backend/**: FastAPI + sentence-transformers (`all-MiniLM-L6-v2`)
- **frontend/**: Next.js dashboard

## Run the backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000      # http://localhost:8000/docs
```

The embedding model (~90 MB) downloads on first start and is loaded **once**, then shared by all requests.

With Docker:

```bash
cd backend
docker build -t devpulse-api .
docker run -p 8000:8000 devpulse-api
```

Tests (fast, offline; they use a stand-in for the embedding model):

```bash
pip install -r requirements-dev.txt
pytest
```

## Run the frontend

```bash
cd frontend
cp .env.example .env.local     # change NEXT_PUBLIC_API_URL if the backend isn't on localhost
npm install
npm run dev                    # http://localhost:3000
```

## API

| Method | Path | Notes |
|---|---|---|
| GET | `/api/v1/health` | status, and whether the model is loaded |
| POST | `/api/v1/analyze` | `{ requirement, code_diff, commit_activity?, activity_timestamps?, bug_frequency? }` |
