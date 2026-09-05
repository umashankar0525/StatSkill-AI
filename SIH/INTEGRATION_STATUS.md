# Integration status

Current implementation and verification are documented in [SOUL_INTEGRATION.md](SOUL_INTEGRATION.md).

- Four selected ministries, 17 work areas and 102 role entries are shared across account forms and backend validation.
- Supplied PDF mappings retain six proficiency levels and all relevant competencies; model estimates never change required levels.
- SOUL question-generation logic is adapted to installed local Llama models and existing sqlite-vec RAG.
- Prepared pools cover every reachable question depth. Answer submission selects the next question without inference or a Continue prompt.
- Llama 3.1 8B evaluates saved evidence and ranks verified iGOT catalogue entries. Unsupported outputs fail visibly instead of fabricating results.
- Existing profiles, assessment history, uploads, local courses, permissions, source previews and OKRs remain connected.
- Eleven HTTP tests, five model-contract tests and frontend regressions passed. Local model inference and account/profile browser flows were checked with isolated records.

Initial preparation and post-assessment evaluation still take time. The iGOT catalogue is a limited public subset, and iGOT sign-in/enrolment/completion are external. Legacy accounts must select a supported work area before a new role assessment. MCQs estimate demonstrated knowledge; they do not certify workplace performance.

## File support

Native text extraction: PDF, DOCX, PPTX, XLSX, XLS, TXT, Markdown, CSV, TSV, JSON,
HTML, XML, SRT, VTT, RTF, ODT, ODS and ODP.

Scanned PDF and PNG/JPEG/TIFF/BMP/WebP use Tesseract. Legacy DOC/PPT uses LibreOffice
conversion. MP3/WAV/M4A/MP4/WebM/MOV uses the locally cached multilingual Whisper base
model and the bundled decoder in PyAV. Media extraction uses the audio track; slide
text without spoken narration is not transcribed. Password-protected, corrupt,
unrecognised files, files over 25 MB, or text exceeding two million characters return
explicit errors. “All file types” cannot mean arbitrary binary formats.

## External integrations still unavailable

| Service | Missing requirement |
| --- | --- |
| iGOT Karmayogi / SSO | Official API credentials, specifications and agreement |
| NSSTA / TPAC | Authorised programme/catalogue API |
| HRMS / service book | Government intranet access and authorised API |
| Parichay / JanParichay | Authorised SSO client and integration specification |
| SMS / email verification | A configured delivery gateway; otherwise clearly labelled local demo OTP |
| Nodal ticket routing | External ticketing/routing API; requests are saved locally |

No plugin is necessary for the local pipeline. These external integrations require
actual service access rather than a generic connector installation.

## Run

Run `./run.ps1` from this folder, then open `http://127.0.0.1:8000`.
Preserve `igot_demo.db`, `users.json`, uploads, configuration and backups when updating.
Model settings are in `.env.example`. Recovery snapshots for this integration are in the workspace's `.soul-integration` folder.
