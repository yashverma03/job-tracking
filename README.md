# Job Tracker

A personal job application tracker. Log jobs you've applied to, track status
(To Apply / Applied / In Progress / Rejected / ...) and referral status, and
manage everything from a single table-based UI.

- **Backend**: Django + Django REST Framework, PostgreSQL
- **Frontend**: React + TypeScript + Vite, TanStack Query, Tailwind CSS

## Project structure

```
job-tracker/
├── backend/                   # Django REST API
│   ├── config/                 # Django settings, URLs, WSGI/ASGI entrypoints
│   ├── common/                  # Shared constants, exceptions, types, utils
│   ├── modules/
│   │   └── jobs/                # Jobs domain module
│   │       ├── models/           # Job model
│   │       ├── dto/              # Request/response serializers
│   │       ├── enums/            # Job status / referral status choices
│   │       ├── service/          # Business logic
│   │       ├── migrations/
│   │       ├── views.py
│   │       └── urls.py
│   ├── docker-compose.yml       # Local Postgres container
│   ├── requirements.txt
│   └── manage.py
│
└── frontend/                   # React SPA
    └── src/
        ├── common/               # Shared components, hooks, types
        └── modules/
            └── jobs/               # Jobs feature (components, hooks, types, utils)
```

## Requirements

- Python 3.12+
- Node.js 20+
- Docker (for local Postgres)

## Setup & running

### 1. Database (Postgres via Docker)

```bash
cd backend
cp .env.example .env
docker compose up -d
```

### 2. Backend (Django, port 20001)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 20001
```

### 3. Frontend (Vite + React, port 20002)

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

The app is then available at `http://localhost:20002`, calling the API at
`http://localhost:20001`.
