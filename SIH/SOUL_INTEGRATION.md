# SOUL integration and source review

Source: https://github.com/sivasankar-11/soul at commit `f99c5e454cd1fd60bcdf9ca84a0ba78c222fe378`.
The full checkout was inventoried, including both servers, UI files, ingestion utilities, framework documents and model clients. File hashes, functions and imports are recorded in `data/soul_source_inventory.json`.

## Model decisions

| Task | Upstream implementation | Active project implementation |
| --- | --- | --- |
| Ministry-based MCQs | Groq Llama 3.3 70B / Llama 3.1 8B Instant | Local Llama 3.2 3B with a 4K context and full GPU offload for every question |
| Document-based MCQs | `rag_quiz_client.py` actually defaults to Groq `openai/gpt-oss-120b`, despite older Llama wording | Adapted role/duties prompts, excerpt cleanup and substantive-question rules in `soul_quiz_engine.py`; local Ollama transport |
| Embeddings / retrieval | BAAI/bge-m3 and Chroma | Existing cached all-MiniLM-L6-v2 and sqlite-vec retained; no duplicate vector database |
| Current proficiency | Upstream demo scoring is not a validated evaluator | A deterministic L0 foundation gate runs first; Local Llama 3.1 8B assesses qualifying saved evidence against L1-L6 with strict output validation |
| Required proficiency | Framework seed/mapping scripts | Explicit supplied-PDF requirements, independent of Llama |
| Course recommendations | Upstream demo course lists | Local Llama 3.1 8B ranks only catalogue records with verified iGOT identifiers |
| Adaptive selection, timers, marking, OKR progress | Application logic | Deterministic backend code; no language model on the question transition path |

The upstream hosted clients were adapted, not deployed verbatim. No Groq key is configured. Neither its account database nor its fake question/confidence fallbacks are imported. Nine ingestion utilities include manually prepared content as well as local-file ingest scripts; they are not treated as authoritative study documents. The second Express demo server and mock frontend calculations are not used. Uploaded sources retain the current extraction and indexing path.

## Ministry and PDF scope

Only the user's four ministries are selectable: MoSPI (6 work areas), Agriculture (4), Labour (4), Commerce (3). Registration, profile edits, compatibility directory endpoints and account validation share one catalogue. Ministry changes reset work-area/role selections. Legacy users and historical database rows are preserved, but unsupported ministries cannot be selected for new or updated profiles.

`data/role_framework.json` contains 17 work areas and 102 role entries, with PDF filenames, page numbers and source hashes. The revised filtered PDF replaces the six matching domain tables. The other eleven All4one domain tables retain all their explicit requirements from the full 33-topic register, including National Accounts, Price Statistics, GIS and APIs. A dash means no requirement. Role grades and individual competency depths are separate. Existing officers select the appropriate work area in My profile before starting a new role assessment.

## Question transitions

Before issuing question 1, the server prepares two validated opening questions in one batch. It then maintains a one-question rolling draft while the learner reads and answers the current question. Question n is planned from the saved answer to question n−2, so adaptation remains causal without generating every possible branch. Answer submission saves the response and normally returns the existing draft directly from SQLite. There is no Continue prompt, and timers start only when questions are issued.

Assigned study material is retrieved first. Minor PDF/OCR punctuation or whitespace differences are reconciled to an exact stored source span. If Llama still cannot provide a valid source quotation, or a role topic has no assigned material, the backend immediately switches to a role/topic/Bloom-specific general-knowledge prompt and marks the saved question's grounding internally. This prevents one source-validation failure from blocking the assessment.

After the final answer, evaluation runs as a resumable background job. Mathematical correctness uses the saved server answer key. Llama assigns knowledge-level estimates using the saved evidence, with valid evidence IDs and bounded levels; it cannot change required role levels. All skipped responses produce no new level. MCQs do not certify workplace performance.

## Recommendations and material sources

The initial catalogue contains 11 attributable iGOT course identifiers from a published iGOT listing. Llama can rank these IDs and explain relevance; the server attaches course links. Unknown or repeated IDs and recommendations unrelated to assessed gaps are rejected. Skills with no catalogue match are explicitly listed. This is a limited catalogue, not a full iGOT search or account integration; availability and completion require iGOT itself. Saving a course is a local bookmark, not an external enrolment.

Trainer/admin material assignments scope assessment retrieval to the selected role and required topic before vector ranking. Course quizzes scope retrieval to their course document. Source-grounded questions require a supporting quotation from the assigned study text. Thirteen supplied PDFs are indexed with original-file hashes and page references. A missing or unverifiable quotation triggers the internally marked general-knowledge fallback.

## Verification

- 11 isolated HTTP integration tests: registration/profile persistence, role mapping, full assessment, Q(n−2) adaptation, source-scoped course quiz, answer-key privacy, timer, permissions, scoring idempotency, OKRs and failure recovery.
- 5 model-contract tests: exhaustive branch capacities through nine questions at all six starting levels, four-ministry catalogue, PDF depths, hallucinated evidence/course rejection, evaluation caching and model routing.
- Frontend regression checks: ten connected views, escaped user/model/source text, real null/zero scores, direct question handoff, username typing and stale availability responses.
- Real local inference passed for question generation, Llama 8B evaluation and Llama 8B course ranking in an isolated database. Results recorded in `tmp/local-model-smoke.json`.
- Browser checked language entry, four ministry choices, filtered work areas/designations, username availability, account creation, dashboard and profile ministry changes.

Reproduction: `python tests/test_integration.py`, `python tests/test_model_contracts.py`, `node tests/check_username.js`. Start the isolated `tests/preview_server.py` before `node tests/check_frontend.js`. `python tests/smoke_local_models.py` invokes installed local models.
