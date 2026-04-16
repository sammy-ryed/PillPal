# PillPal

Prescription OCR intelligence platform. Upload a doctor's prescription image, get a structured JSON of every medicine, dose, frequency, and reminder schedule.

---

## Architecture

```
index.html          — Single-file frontend (no build step)
backend/
  app/
    main.py         — FastAPI entry point
    config.py       — Settings from .env
    models/         — Pydantic schemas
    routers/        — HTTP endpoints
    services/       — OCR pipeline stages
      image_preprocessor.py   — OpenCV: deskew, CLAHE, adaptive threshold
      ocr_engine.py           — EasyOCR + Tesseract wrappers
      text_merger.py          — Confidence-weighted text merge
      prescription_parser.py  — Residual extraction: dosage, freq, duration, name
      medicine_corrector.py   — RapidFuzz fuzzy match against Supabase medicine DB
      frequency_parser.py     — OD/BD/TDS + Indian notation + natural language
      reminder_generator.py   — Day-by-day slot schedule
      supabase_service.py     — Data access layer (fallback to in-memory if no DB)
    utils/
      logger.py
  seed.py           — Populate Supabase with medicines + frequency codes
sample_prescriptions/   — Test images
```

---

## Setup

### 1. Clone

```bash
git clone <repo>
cd PillPal
```

### 2. Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

Install Tesseract OCR (required):
- **Windows**: Download from https://github.com/UB-Mannheim/tesseract/wiki, add to PATH
- **macOS**: `brew install tesseract`
- **Ubuntu**: `sudo apt install tesseract-ocr`

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

If you leave these blank, the backend falls back to a built-in medicine dataset — no database needed for local testing.

### 4. Seed Supabase (optional but recommended)

Create these tables in your Supabase project SQL editor first:

```sql
create table medicines_db (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  generic_name text,
  category text,
  common_dosages text[],
  created_at timestamptz default now()
);

create table frequency_codes (
  code text primary key,
  full_name text not null,
  times_per_day int not null,
  default_times text[]
);

create table prescriptions (
  id uuid primary key default gen_random_uuid(),
  raw_text text,
  doctor_name text,
  patient_name text,
  medicines jsonb,
  warnings text[],
  overall_confidence float,
  created_at timestamptz default now()
);

create table reminders (
  id uuid primary key default gen_random_uuid(),
  prescription_id uuid references prescriptions(id),
  medicine_name text,
  schedule jsonb,
  created_at timestamptz default now()
);
```

Then run:
```bash
python seed.py
```

### 5. Start backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

### 6. Open frontend

Open `index.html` directly in your browser. No build step.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/api/health` | Service health + DB status |
| `POST` | `/api/prescriptions/parse` | Upload image, get structured JSON |
| `POST` | `/api/prescriptions/reminders` | Generate reminder schedule |

### Parse response shape

```json
{
  "id": "uuid",
  "medicines": [
    {
      "name": "Dolo 650",
      "corrected_name": "Dolo 650",
      "dosage": "650mg",
      "frequency": "Twice Daily",
      "frequency_code": "BD",
      "times_per_day": 2,
      "duration_days": 5,
      "timing_notes": "After food",
      "reminder_times": ["08:00", "20:00"],
      "confidence": 0.91,
      "is_uncertain": false
    }
  ],
  "doctor_name": "Dr. Krishnan",
  "patient_name": "Rajesh Kumar",
  "raw_text": "...",
  "warnings": [],
  "overall_confidence": 0.87,
  "processing_metadata": { ... }
}
```

---

## OCR Pipeline Stages

1. **Image preprocessing** — deskew (Hough), CLAHE, adaptive threshold, bilateral sharpen, Otsu fallback
2. **Dual OCR** — EasyOCR (handwriting) + Tesseract PSM 6 (printed), both run in parallel
3. **Confidence merge** — line-level Levenshtein comparison, keep higher-confidence version per line
4. **Prescription parsing** — residual extraction: strip dosage, frequency, duration, timing from each line, leaving the name
5. **Medicine correction** — OCR character substitution (0→O, 1→l) + RapidFuzz `token_set_ratio` against medicine DB
6. **Frequency parsing** — Indian notation (1-0-1), medical abbreviations (OD/BD/TDS), natural language
7. **Reminder generation** — day-by-day slot schedule with calendar/SMS integration hooks

---

## Sample Test Images

Place prescription images in `sample_prescriptions/`. The pipeline handles:
- Printed prescriptions (typed, computer-generated)
- Handwritten prescriptions
- Photos taken on phones (JPEG, PNG, HEIC via PIL)
- Scanned documents

For best results: good lighting, flat surface, full prescription visible in frame.

---

## Future Roadmap

- [ ] Google Calendar event creation
- [ ] Twilio SMS reminders
- [ ] WhatsApp via Twilio
- [ ] Guardian dashboard with adherence analytics
- [ ] ESP32 smart pillbox sync
- [ ] Doctor portal (prescription verification)
- [ ] Voice reminders (Tamil / Hindi / English via TTS)
- [ ] Elderly mode frontend
- [ ] Multi-language prescription OCR (Hindi, Tamil)
- [ ] Adherence analytics and graphing
- [ ] Mobile app (React Native)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML + Vanilla CSS + JS (no build step) |
| Backend | Python 3.11+, FastAPI, Uvicorn |
| OCR | EasyOCR, Tesseract (pytesseract) |
| Image processing | OpenCV, Pillow, NumPy |
| Fuzzy matching | RapidFuzz |
| Database | Supabase (PostgreSQL) |
| Config | pydantic-settings, python-dotenv |
