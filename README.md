# CustomerLens

**AI-Powered Customer Feedback Intelligence Platform**

## Overview

CustomerLens is a fullstack AI application for analyzing customer feedback. It combines a FastAPI backend with a frontend interface to classify sentiment, categorize feedback, and generate AI-assisted customer service responses using company guidelines.

## Project Structure

```text
customer-lens/
├── backend/
│   ├── app/
│   ├── requirements.txt
│   └── company_guidelines.txt
├── frontend/
├── README.md
└── .gitignore
````

## Tech Stack

### Backend

* Python 3.12
* FastAPI
* SQLite
* SQLAlchemy
* OpenAI API
* Google Gemini API
* ChromaDB

### Frontend

* React
* Vite
* TypeScript

## Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Run Backend

```bash
uvicorn app.main:app --reload
```

API docs:

```text
http://localhost:8000/docs
```

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## Current API Endpoints

* `GET /` - Welcome endpoint
* `GET /health` - Health check
* `POST /feedback/` - Submit feedback and run AI analysis
* `GET /feedback/{feedback_id}` - Get feedback by ID
* `GET /feedback/customer/{email}` - Get feedback by customer email

## Author

Victor von Reiche - AI Engineering Student at Masterschool
