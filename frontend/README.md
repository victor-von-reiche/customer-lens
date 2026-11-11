# CustomerLens frontend

React and TypeScript support workspace using Vite and the existing AURON design.

```bash
npm ci
npm run dev
```

Start the backend on port 8000 first, or use `python3 backend/scripts/dev.py` from the
repository root. Select the optional keyless demo with `--demo`. The development server runs on http://localhost:5173 and proxies
`/api` to the backend. Build with `npm run build`; check with `npm run lint`.

Routes: `/` brand context, `/feedback` customer submission, `/dashboard` support
workspace. `/dashboard?ticket=1` links directly to a ticket. An optional API token
is held in session storage for the current browser tab. It is never a provider key.

See the root README for live/demo setup and Docker startup.
