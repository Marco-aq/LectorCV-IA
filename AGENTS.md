# AGENTS.md — equipoQsharp / Reclutador IA

## Project structure

- `backend/` — FastAPI server (`main.py`) using **CrewAI** with Google Gemini.
- `frontend/` — Streamlit UI (`app.py`) consuming the backend API.

## Quick start

### Backend
```bash
cd backend
pip install -r requirements.txt
# .env must have GOOGLE_API_KEY
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

## Architecture

### Backend endpoints

| Endpoint | Method | Input | Output |
|---|---|---|---|
| `/` | GET | — | Health check |
| `/generar-preguntas/` | POST | `descripcion_puesto` (form) + `cv` (PDF file) | JSON with `preguntas` array |
| `/evaluar-candidato/` | POST | `{ "respuestas": "..." }` (JSON body) | JSON with `veredicto`, feedback |

### CrewAI agents (3+1)

Defined in `backend/agents.py`. Pipeline:

1. **Fase 1** (`procesar_cv_y_generar_preguntas`): `analista_perfil` → `evaluador_cv` (uses `leer_pdf_tool`) → `entrevistador` → outputs 4 questions as JSON array.
2. **Fase 2** (`evaluar_respuestas_candidato`): `clasificador` → emits verdict (`APTO`|`NO APTO`|`EN OBSERVACIÓN`) with feedback.

- All agents share `gemini/gemini-3.1-flash-lite` (set via `LLM()`), temperature 0.2.
- No delegation (`allow_delegation=False`).

### Key helpers

- `backend/tools.py` — `leer_pdf_tool` wraps `pdfplumber` for PDF text extraction.
- `backend/main.py:extraer_json_de_texto()` — strips markdown code fences around JSON from LLM output (models often wrap JSON in `` ```json `` blocks).
- Telemetry disabled via `OTEL_SDK_DISABLED=true` and `CREWAI_DISABLE_TELEMETRY=true` in `agents.py`.

## Dependencies

| Layer | Key deps |
|---|---|
| Backend | `fastapi`, `uvicorn`, `crewai`, `langchain-google-genai`, `pdfplumber`, `python-dotenv`, `python-multipart` |
| Frontend | `streamlit==1.35.0`, `requests==2.32.3` |

## Important notes

- **No tests, no CI, no linters** configured. No `pyproject.toml`.
- The `.env` file is committed with a raw API key (`.gitignore` does not exist).
- CORS is wide open (`allow_origins=["*"]`).
- When deploying, update `API_URL` in `frontend/app.py` (line 12) from `http://localhost:8000` to the production backend URL.
- PDFs are saved to disk temporarily, parsed, then deleted in a `finally` block.
- No test fixtures or mock infrastructure exists.
