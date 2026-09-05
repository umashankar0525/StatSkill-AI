# Source cleanup — 4 September 2026

Removed confirmed unused code from the active project. Original files remain in
`../../.cleanup-recovery/2026-09-04/` so this cleanup is reversible. No permanent
deletion of those source files or installers was performed.

## Removed from the active application

- Fifteen unused legacy components: adminDash, aiAssistant, aiGenerator, assessment,
  framework, igotHub, landing, learnerDash, learningPath, navbar, profile, quizPlayer,
  recommendations, reports and trainerDash. The connected implementations remain in
  `static/js/liveViews.js`, `portal.js` and `store.js`; `components/authModal.js` remains active.
- `mockData.js`, unused `orgDataService.js`, its script tag, unused emblem asset and
  unused Chart.js CDN import.
- Separate Express demo server, package manifests and demo page. Its schema, seed
  SQL and maintenance generator are retained under `db/`, with backend paths updated.
- Unused legacy CSS, obsolete modal/current-user state, unused helper functions,
  abandoned whole-assessment preparation flags and unused backend imports.
- Shadowed `/api/users` handler; the active authenticated handler remains in
  `live_api.py`. Organization-list responses now correctly handle JSON arrays.
- Duplicate commit and unused SMS provider variables with no implementation.
- Obsolete proposal content in README, replaced with current setup and architecture.

Moved 1,978,362,572 bytes of completed Ollama/LibreOffice installers and installation
logs into the recovery directory. This reduces the active project size, but does
not free disk space because the files are retained for recovery.

## Preserved

SHA-256 checks match the pre-cleanup versions of `rag_engine.py`, `quiz_service.py`,
`adaptive_quiz_engine.py`, `frac_engine.py`, `frac_seed.py`, `okr_service.py`,
`storage.py`, `requirements.txt`, `.env` and `users.json`.

The database, uploads, backups, installed Ollama models, embedding/transcription
caches and installed converters were not removed. Assessment timing and rolling
preparation remain intact. Active account APIs, organization APIs, accessibility,
language selection and all connected workspace views remain available. Existing
compatibility endpoints and setup/test utilities were retained because removing
them is not justified solely by their absence from current navigation.

## Verification

- Nine existing isolated integration tests passed, including question n-2 evidence,
  scoring, permissions, registration, uploads, courses and OKR progress.
- Added and passed a regression for fresh organization seeds, array responses and
  access control on `/api/users`.
- Real AI smoke check passed for 13 document formats, cached embeddings, sqlite-vec
  retrieval and source-grounded Llama generation.
- All remaining JavaScript files passed syntax checks; every local asset referenced
  by index.html exists, and removed identifiers have no remaining code references.
- Isolated browser checks passed for language choice, login, registration entry,
  sign-out, home and all nine other workspace sections. No visible application
  errors or horizontal overflow appeared in the desktop sections checked.
- Restarted the local application; `/api/health` reports healthy and `/api/states`
  returns 36 entries.

These checks cover the cleanup's affected behavior; they do not guarantee every
possible uploaded file or model-generated question.

## Recovery

`../../.cleanup-recovery/2026-09-04/source-before-cleanup.zip` contains the pre-cleanup
source snapshot, including earlier uncommitted edits. `unused-source/` retains
removed files in their original relative structure; `installers/` holds the moved
installation artifacts. `protected-hashes.json` records the protected file hashes.
Restore selected files or extract into a separate directory for comparison; avoid
overwriting later work wholesale. Restore `server.py` and the original seed paths
together if reverting the database-directory relocation.
