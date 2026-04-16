# PillPal — QUICKSTART

Everything you need to go 0 → running in one doc.

---

## Prerequisites

| Tool | Version | Check |
|------|---------|-------|
| Python | 3.10+ | `python --version` |
| Node.js | 18+ | `node --version` |
| Tesseract OCR | any | `tesseract --version` |

> **Tesseract install**
> - **Windows**: [Download installer](https://github.com/UB-Mannheim/tesseract/wiki) → add install folder to `PATH`
> - **macOS**: `brew install tesseract`
> - **Ubuntu/Debian**: `sudo apt install tesseract-ocr`

---

## Step 1 — Backend

Open a terminal in `PillPal/backend/`.

```bash
# Create virtual env
python -m venv venv

# Activate — Windows
venv\Scripts\activate

# Activate — macOS/Linux
source venv/bin/activate

# Install Python deps
pip install -r requirements.txt
```

### Configure environment

```bash
copy .env.example .env        # Windows
# or
cp .env.example .env          # macOS/Linux
```

Open `.env` and fill in **your** Supabase project URL and anon key:

```
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your-supabase-key-here
```

> **No Supabase?** Leave both blank. The backend falls back to a built-in dataset of 200+ Indian medicines. OCR still works fully.

### Seed the database (optional, one-time)

Only needed if you configured Supabase. Run this **once**:

```bash
python seed.py
```

### Start the API server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO  PillPal API starting up…
INFO  Supabase connected — medicine DB loaded.
INFO  PillPal API ready.
INFO  Uvicorn running on http://0.0.0.0:8000
```

Verify it works: http://localhost:8000/api/health

---

## Step 2 — Frontend (pick one)

### Option A: Plain HTML (no install)

Open `PillPal/index.html` directly in your browser.  
Backend must be running on port 8000.

### Option B: Next.js

Open a **second** terminal in `PillPal/frontend/`.

```bash
npm run dev
```

Open http://localhost:3000

---

## Step 3 — Try it

1. Go to **Upload** page
2. Drop or browse to a prescription image (JPG/PNG)
3. Click **Extract Medicines**
4. Wait 3–8 seconds while the OCR pipeline runs
5. Review and edit the extracted results
6. Click **Confirm & Set Reminders**
7. Check the **Dashboard** for today's schedule

---

## API docs

FastAPI auto-generates interactive docs at:  
http://localhost:8000/docs

---

## Useful commands

```bash
# Check Tesseract is on PATH
tesseract --version

# Run a quick parse test via curl
curl -X POST http://localhost:8000/api/prescriptions/parse \
  -F "file=@sample_prescriptions/your_rx.jpg"

# Lint the Next.js frontend
cd frontend && npm run lint

# Kill a process on port 8000 (Windows)
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `tesseract is not installed or it's not in your PATH` | Install Tesseract and add its folder to PATH, then restart terminal |
| `Connection refused` in browser | Backend isn't running — start uvicorn first |
| `CORS error` | CORS is set to `*` by default — check `backend/app/config.py` → `allowed_origins` |
| EasyOCR first run takes 2–3 min | It's downloading model weights. Happens only once. |
| Low OCR confidence warnings | Better lighting + flat surface + full prescription in frame |
| `Module not found` on Next.js | Run `npm install` inside `frontend/` |
| Supabase 401 error | Check that `SUPABASE_KEY` is the **anon** key, not the password |

---

## Environment files

| File | Purpose |
|------|---------|
| `backend/.env` | Supabase URL + key, OCR toggles |
| `frontend/.env.local` | `NEXT_PUBLIC_API_URL` — defaults to `http://localhost:8000` |

---

## Project structure

```
PillPal/
├── index.html              ← Standalone HTML+JS frontend (no Node)
├── README.md               ← Full architecture docs
├── QUICKSTART.md           ← This file
├── sample_prescriptions/   ← Drop test images here
├── backend/
│   ├── .env.example        ← Copy to .env
│   ├── requirements.txt
│   ├── seed.py             ← Populate Supabase (run once)
│   └── app/
│       ├── main.py         ← FastAPI entry
│       ├── config.py       ← Settings
│       ├── models/         ← Pydantic types
│       ├── routers/        ← HTTP endpoints
│       └── services/       ← OCR pipeline
└── frontend/               ← Next.js app
    ├── .env.local          ← API URL
    └── src/
        ├── app/            ← Pages (App Router)
        ├── components/     ← Shared UI
        ├── lib/            ← types.ts, api.ts
        └── store/          ← prescription-context.tsx
```
