# Job Tracker

## Backend (Django, port 20001)

```
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py runserver 20001
```

## Frontend (Vite + React + TS, port 20002)

```
cd frontend
cp .env.example .env
npm install
npm run dev
```
