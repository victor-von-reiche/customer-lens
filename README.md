# CustomerLens

CustomerLens is an AI-assisted customer support application for **AURON**, a fictional road-bike shop. It analyzes customer feedback and helps support staff prepare a response based on company guidelines.

## How it works

1. Open the AURON landing page and choose **Contact us** in the top navigation to submit feedback.
2. Switch to **Dashboard** to view the message as a support employee. Feedback is classified by sentiment, category, and urgency.
3. Open the ticket to review and edit the suggested reply before saving it to the conversation. Critical feedback is also flagged for review.

A retrieval-augmented generation (RAG) system indexes company policies from [`policies/support.json`](policies/support.json). It retrieves relevant sections for each message and provides them to Gemini when generating a reply. The dashboard can show the sources used. Replies are saved in the application; they are not sent as external emails.

## Getting started

**Requirements:** Python 3.12, Node.js 22, and a Gemini API key for live analysis.

1. Clone the repository and open its directory:

   ```bash
   git clone https://github.com/victor-von-reiche/customer-lens.git
   cd customer-lens
   ```

2. Copy `backend/.env.example` to `backend/.env` and add your key as `GEMINI_API_KEY`. An existing `GOOGLE_API_KEY` is also supported. Keep an existing `.env` file instead of overwriting it.

3. Start the frontend and backend:

   ```bash
   python3 scripts/dev.py
   ```

4. Open [http://localhost:5173](http://localhost:5173), select **Contact us**, and then visit **Dashboard** to review the feedback. The first start installs the required dependencies. Stop both servers with `Ctrl+C`.

Classification and reply drafts use `gemini-3.5-flash-lite` by default, configured with `GEMINI_MODEL` in `backend/.env`. Gemini usage is subject to the configured project's quota and pricing. If analysis is unavailable, the ticket remains available for manual review.

For Docker, copy `.env.docker.example` to `.env.docker`, add your Gemini key,
and run `docker compose --env-file .env.docker up --build`. Open the same URL;
stop with `Ctrl+C`. Ticket data persists in a named Docker volume.

## Demo mode

To explore the workflow without an API key, run:

```bash
python3 scripts/dev.py --demo
```

Demo mode uses a separate database, synthetic feedback, and simulated English-language analysis and replies. It does not call Gemini.

## Technology

- **Frontend:** React, TypeScript, Vite, and Tailwind CSS
- **Backend:** Python, FastAPI, SQLAlchemy, and SQLite
- **AI and retrieval:** Gemini for classification and drafts; a local lexical index for RAG, with optional Chroma semantic retrieval

The API documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs) while the backend is running. For evaluation details, see [evaluation/README.md](evaluation/README.md).

## Development

```bash
backend/.venv/bin/python -m pip install -r backend/requirements-dev.txt
backend/.venv/bin/ruff check backend scripts
backend/.venv/bin/pytest -q
cd frontend
npm run lint
npm run build
```

Author: Victor von Reiche
