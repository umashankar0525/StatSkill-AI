# StatSkill AI

Local learning and competency assessment portal for statistical officers, trainers and administrators. The frontend uses the imported GitHub UI connected to the existing Python, RAG and Ollama backend. See [UI_IMPORT.md](UI_IMPORT.md).

## Run locally

After cloning, open PowerShell in this directory and run:

```powershell
.\setup.ps1
.\run.ps1
```

Then open http://127.0.0.1:8000. The setup command creates an isolated Python
environment, installs the backend dependencies, prepares a private working
database, restores the packaged study files, downloads the exact Ollama models,
and caches the embedding model. No cloud LLM API key is required.

Use `.\setup.ps1 -SkipModels` only when the models and embedding cache are
already installed. Use `.\setup.ps1 -ResetDatabase` to replace local application
data with a fresh contributor database.

The repository records the exact local model names and layer checksums in
`models/manifest.json`. Llama 3.2 3B writes quiz questions with a small
GPU-resident context; Llama 3.1 8B handles assessment evaluation, RAG responses,
and iGOT course ranking. Their approximately 6.9 GB of upstream Ollama weights
are downloaded by `setup.ps1` rather than stored as Git objects. See
`.env.example` for settings. Never commit `.env` or credentials.

Document search uses cached `all-MiniLM-L6-v2` embeddings and sqlite-vec. Tesseract enables OCR; LibreOffice handles legacy Office conversion; `python tests/setup_transcription.py` prepares offline speech transcription.

## Application

- English/Hindi entry and registration for the four selected ministries and their 17 work areas.
- Role profiles, evidence-based skill assessment and learning recommendations.
- Adaptive assessments with a rolling buffer: two opening questions are prepared together, then question n+1 is prepared while question n is displayed using evidence through n−1.
- Uploaded learning materials, source retrieval, grounded questions and chat.
- Courses, progress reports, personal objectives and measurable key results.
- Trainer and administrator material and workforce views.

The models and competency calculations run in the backend. Llama 3.2 3B is fully GPU-offloaded for quiz generation; Llama 3.1 8B uses a conservative 24-layer GPU allocation for evaluation and recommendations. Two opening questions are prepared in one batch, and evaluation runs after the final answer. Thirteen supplied study PDFs are indexed and mapped to role topics. See [ASSESSMENT_REPAIR.md](ASSESSMENT_REPAIR.md) for coverage, retry behavior and measured validation. External government-system connectivity requires real service credentials; it is not implied by the portal's course links or organization seed data.

## Source layout

| Location | Purpose |
| --- | --- |
| `server.py`, `live_api.py` | HTTP server, authentication and application APIs |
| `storage.py`, `db/` | Persistent schema, migrations and organization seeds |
| `data/starter/igot_demo.db` | Clean database with the complete role framework and prebuilt RAG index |
| `data/study_materials/` | Thirteen checksum-verified source PDFs used by RAG |
| `models/manifest.json`, `setup.ps1` | Exact local model versions and one-command contributor setup |
| `rag_engine.py` | Extraction, embeddings, vector search and local LLM generation |
| `quiz_service.py`, `adaptive_quiz_engine.py` | Assessment lifecycle and adaptation |
| `frac_engine.py`, `frac_seed.py` | Role requirements, scoring and provisional seed mappings |
| `okr_service.py` | Objectives, key results and progress calculation |
| `static/` | Connected browser application and accessibility controls |
| `tests/` | Isolated integration, real-model and converter checks |

`igot_demo.db`, `users.json`, `uploads/`, `.env`, logs and backups are private
runtime files and are excluded from Git. A clone receives clean replacements
from `data/starter/`, so personal accounts and assessment answers are never
shared with contributors. The organization seed generator is a maintenance
utility using Node's built-in modules; the running website does not require the
old Express demo or its npm packages.

## Verification and implementation notes

Run `python tests/test_integration.py` for isolated HTTP regressions. Run `python tests/check_local_ai.py` for real extraction, embedding, retrieval and Llama generation; it needs the local AI services. `tests/check_converters.py` checks optional file converters.

See [SOUL_INTEGRATION.md](SOUL_INTEGRATION.md) for the current repository review, model routing, supplied-PDF mappings and validation. See [USER_FLOW.md](USER_FLOW.md) for the current experience, [INTEGRATION_STATUS.md](INTEGRATION_STATUS.md) for implementation details and limitations, and [CLEANUP.md](CLEANUP.md) for the source cleanup and recovery location.
