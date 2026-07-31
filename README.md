# Job Tracker

## Backend (Django, port 3000)

```
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py runserver 3000
```

## Frontend (Vite + React + TS, port 3100)

```
cd frontend
cp .env.example .env
npm install
npm run dev
```
