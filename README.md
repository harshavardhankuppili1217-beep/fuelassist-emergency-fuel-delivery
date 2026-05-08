# FuelAssist

FuelAssist is a full-stack emergency fuel delivery platform for travelers. It has two user roles:

- Travelers (`USER`) create emergency fuel requests.
- Petrol bunks (`BUNK`) receive, accept, and complete requests.

## Tech Stack

- Frontend: React + TypeScript + CSS (Vite)
- Backend: Django + Django REST Framework + Token Authentication
- Database: SQLite

## Run Backend

```bash
cd backend
python -m pip install django djangorestframework django-cors-headers
python manage.py migrate
python manage.py runserver
```

Backend API base URL: `http://127.0.0.1:8000/api`

## Run Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend URL: `http://127.0.0.1:5173`

## Main Features

- Separate registration/login for Traveler and Petrol Bunk
- Fuel request creation with fuel type, liters, and live coordinates
- Automatic nearest bunk assignment using distance calculation
- Bunks can accept and complete requests
- Real-time request status updates via WebSocket events
- Map links for every request location (OpenStreetMap)
- Payment completion flow for delivered requests
- Responsive UI for mobile and desktop usage
