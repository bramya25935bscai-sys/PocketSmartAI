# PocketSmart AI

Your smart budget and recommendation assistant for home interiors, parties and jewelry.

## Repository layout

```
PocketSmartAI/
├── code files/              # all source code, tests and generator scripts
│   ├── pocketsmart/         # Flask app (routes, services, templates, static, data)
│   ├── tests/               # pytest suite (22 tests)
│   ├── scripts/             # doc / screenshot / demo-video generators
│   ├── requirements.txt
│   ├── pytest.ini
│   └── .env.example         # copy to .env (git-ignored)
├── docs/                    # demo script, evidence logs, screenshots
├── media/                   # demo + testing videos and voice-over clips
├── Phase_Wise_Submission/   # phase-wise .docx / .xlsx / .pptx deliverables
└── README.md
```

Everything below runs from inside `code files/`.

## Problem statement

Choosing products across Amazon, Flipkart, IKEA, Swiggy, Zomato and OYO while staying inside an INR budget is tiring. PocketSmart AI returns a capped list. **Catalogs are mock JSON labelled “sample data” — nothing is scraped live.**

## Objectives

- Three planners: Home, Party, Jewelry  
- Never exceed the stated budget  
- Optional Google Gemini (`google-genai`); **Demo mode** if `GEMINI_API_KEY` is empty  
- pytest + Playwright evidence for an academic submission  

## Features

| Must-have | Nice-to-have |
|-----------|----------------|
| `/generate-home`, `/generate-party`, `/generate-jewelry` | Register / login session |
| Budget validation & cap | History page |
| Demo badge + AI fallback banner | Outfit image (Pillow sample) |
| `/health` | Testimonials |

## Tech stack

| Layer | Choice |
|-------|--------|
| Backend | Flask 3 + Flask-CORS, sessions |
| AI | google-genai, model from `GEMINI_MODEL` (default `gemini-2.0-flash`) |
| Frontend | HTML / CSS / JS |
| Images | Pillow |
| Tests | pytest, Playwright |

## Architecture

Browser → Flask `:5000` → `routes/api.py` → `services/recommend.py` → mock catalogs and/or Gemini → `enforce_budget()` → JSON cards.

## How it works

1. Validate input (zero/negative/too-small budget, bad event, non-image).  
2. Ask Gemini for JSON catalog ids **or** run deterministic pickers.  
3. Drop items until `sum(qty * price) ≤ budget`.  
4. Tag every item `sample data`. Store a short record in the Flask session.

## Setup

```bash
cd "code files"
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # leave GEMINI_API_KEY empty for Demo mode
PYTHONPATH=. python3 -m pocketsmart.app
# open http://127.0.0.1:5000
```

With a real key, set `GEMINI_API_KEY` and optionally `GEMINI_MODEL`. If the live call fails, the UI shows a fallback message instead of crashing.

## API / routes

| Method | Route | Notes |
|--------|-------|--------|
| GET | `/health` | `{ mode: demo\|live }` |
| POST | `/generate-home` | JSON budget, rooms, quantities |
| POST | `/generate-party` | JSON budget, guests, event_type, venue |
| POST | `/generate-jewelry` | JSON or multipart + outfit file |
| POST | `/auth/login` `/auth/register` | Session user |
| GET | `/api/history` | Session plans |
| GET | `/` `/home-planner` `/party-planner` `/jewelry-planner` | HTML |

## Testing

Run from inside `code files/`:

```bash
PYTHONPATH=. python3 -m pytest tests -q --cov=pocketsmart
# 22 passed, 82% coverage (see ../docs/evidence/)
```

Screenshots: `docs/screenshots/`. Videos: `media/Demo_Video.mp4` (1m35s), `media/Testing_Video.mp4` (1m02s). The generator scripts in `code files/scripts/` resolve `docs/`, `media/` and `Phase_Wise_Submission/` automatically, so run them from anywhere.

## Limitations

Mock prices only; no payments; videos shorter than a 3–4 minute classroom slot unless you re-run the record scripts with longer waits.

## Future enhancements

Live consented APIs, PDF export, multi-user database, GST.

## License

Academic / MIT-style use for coursework.
