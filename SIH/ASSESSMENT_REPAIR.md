# Assessment preparation and supplied study materials

## Evaluation recovery update

The completed-answer assessment was stuck after a local model HTTP 500, with six topic evaluations already cached. Evaluation now retries transient and invalid-output failures automatically, uses a JSON schema constrained to supported levels and actual evidence IDs, and preserves each successful topic evaluation. Evaluation uses Llama 3.1 8B with an 8,192-token context; quiz writing uses the smaller Llama 3.2 3B model with a 4,096-token context.

Progress is stored in `assessment_evaluation_progress` and returned only through the authenticated session view. The interface polls evaluation progress and displays completed topics while the remaining topics finish. Results show each topic's correct-answer count, assessed level with its label, and required role level. If a job fails after results were committed, the client retrieves those results instead of presenting another Retry loop.

The affected assessment was recovered from its original 32 saved answers: six cached topic evaluations were reused, two were evaluated by Llama, and all eight topic summaries were committed. No answers were changed. Backup: `.soul-integration/database-before-restart-20260904-232320` at the workspace root. The website server was not started for recovery.

Regression coverage includes the assessment topic schedule and evaluation result mapping for all 102 configured roles, partial evaluation recovery, HTTP 500 retries, invalid-output rejection, cached-result reuse and completed-result recovery in the UI. The shared workflow prefers assigned study content and uses an internally marked general-knowledge fallback for missing material or an unverifiable source quotation.

Implemented on 4 September 2026. Existing accounts, answers, completed assessments and required role levels are preserved. A consistent pre-import backup is in `.soul-integration/database-before-restart-20260904-202854` at the workspace root.

## Count and generation diagnosis

The affected assessment has **32 question slots**: four questions for each of eight required topics. The old preparation display counted **48 candidate questions**, including the difficulty alternatives needed for two-answer-delayed adaptation. Both learner-facing counters now use the saved assessment target. Preparation progress counts slots whose possible difficulty choices are ready.

Stored failures included repeated questions and incomplete model responses. The generator sent previous question stems, not the full answered conversation. It nevertheless made one sequential model request per candidate with excessive repetitive context. Errors were obscured by generic wrappers and invalid batches could discard otherwise valid results.

The updated generator uses structured batches of up to two questions by default, at most 3,600 source characters, four short avoidance stems and small role/difficulty fields. Retrieval runs once per topic, filtering assigned role **and** topic before vector ranking. Local inference is serialized to avoid competing model instances; batching reduces request overhead. Valid partial batches are saved immediately, and resumed preparation requests only missing candidates.

Transient failures retry up to four times with exponential backoff and jitter. HTTP status, timeout, connection, malformed output, duplication and truncation are distinguished. Logs record durations, token counts, model load time, queue time and system memory without prompts or user answers. Diagnostics are in `logs/generation.jsonl` and the bounded `generation_events` table. Missing material stops before any generation call and identifies the missing topics.

Two opening questions are prepared before the first timer starts. During the quiz, the server prepares one rolling draft while the current question is displayed, using the answer two questions earlier within the topic. Answer submission returns the saved draft directly when ready. There is no intermediate Continue button and no combinatorial preload.

## Imported materials

The 13 supplied study PDFs are copied byte-for-byte into the application's upload storage and indexed in SQLite: **1,887 original pages and 5,323 text passages**. SHA-256 checksums, original filenames, page references, topic mappings and applicable role assignments are retained. The five-page role matrix is excluded from teaching content; existing role requirements already match that source.

`data/study_material_manifest.json` documents each original file and mapping. `tools/import_supplied_study_materials.py` supports idempotent imports while the app is stopped. `tools/audit_study_import.py` checks original file hashes, page bounds, ready status, provenance and database integrity. Detailed import and coverage reports are in `tmp/study-material-import.json` and `tmp/study-import-audit.json`.

All eight topics of the affected price-statistics assessment have assigned source material. Across the complete role catalogue, 45 of 102 role entries have material assigned for every required topic. Remaining gaps include National Accounts, Metadata Standards, APIs, Cloud/Government Cloud, DPI, Stata, SPSS, Project Management and Change Management. Those roles need additional study sources before complete assessments can prepare. Price statistics coverage is introductory; the Python tutorial is version 3.7, and the privacy sources cover general confidentiality rather than later legislation.

## Evidence and models

The proposed and implemented evidence schema and scoring policy are in `ASSESSMENT_EVIDENCE_DESIGN.md`. Each served question retains its topic, Bloom level, sources, answer key and response. Queryable `questions` and `user_responses` views preserve one authoritative answer record. `topic_competency` stores the latest per-topic level, per-Bloom results, weighted score, sample size and confidence. Llama's assigned level is bounded by the evidence; it cannot invent a higher supported level or an unrelated evidence ID.

Llama 3.1 8B remains the grounded quiz and evaluation model. A real smaller-model comparison produced repeated/weak communication questions and failed the SQL batch after retries with invalid quotations/options, so it was not promoted to grounded question generation.

The earlier CUDA 13 backend reported `shared object initialization failed`, and the app subsequently forced `num_gpu=0`. GPU inference now succeeds on the normal installed Ollama service using a conservative 24-layer allocation. The forced-CPU default was removed; `.env` sets 24 layers for this RTX 4050 Laptop GPU with 6 GB VRAM, while `.env.example` documents automatic allocation. No driver installation or system-wide environment changes were required. The temporary alternative GPU service was stopped. Remaining model layers and application data still use RAM.

Eight real, source-grounded questions across Communication, SQL, Digital Signatures and Price Statistics completed in 60.96 seconds on the GPU, including model loading. GPU residency was approximately 3,945 MiB with the quiz's 6,144-token context. Real Llama evidence evaluation completed in 13.84 seconds with an 8,192-token context and about 4,144 MiB GPU residency. No rate-limit or out-of-memory error occurred in these GPU checks; they are not a long-duration leak certification. Raw timing records are in `tmp/gpu-generation.json` and `tmp/saved-assessment-verification.json`.

## Verification

All 26 isolated backend tests pass. They cover counts, every possible answer path for candidate capacities, two-question-delayed adaptation, fast handoff without inference, partial resume, backoff, role/topic retrieval, source quotation guards, permissions, evidence persistence, Llama evidence validation, recommendation validation and account/profile flows. Browser and frontend checks cover connected views, the two consistent 32-question displays, visible preparation errors, source links, timers and automatic answer handoff.

The affected assessment's complete 48-candidate bank was replayed in an isolated database along correct, incorrect and alternating answer paths. All 96 answers advanced successfully without a model call; average server handoff was 57.89 ms, maximum 184.04 ms. The original user's answers were not changed by these checks. Both public preparation progress and the sidebar now show 32 slots ready.
