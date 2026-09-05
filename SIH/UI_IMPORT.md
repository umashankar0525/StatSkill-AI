# GitHub UI integration

Source: https://github.com/varshasrikadapa-a11y/statskill-ai-v/

Imported from the `main` snapshot identified by `56477c9` on 4 September 2026.
This instruction supersedes the earlier feature-reference-only visual direction.

## Presentation and application wiring

The source index/head configuration, fonts, navy/teal stylesheet, navigation,
dashboard, learning timeline and assistant presentation were copied into the local
frontend and adapted. The course cards, skills cards/matrix, examination card,
question palette and account container use layouts from the corresponding source
components. Registration now uses the source three-step personal details, username,
and password screens. The source profile cards and edit dialog save extended fields
through authenticated APIs. The existing material-management, workforce, reports and goals
forms use the imported styling and retain their authenticated API actions.

`static/js/uiIntegration.js` maps real overview/profile/course/assessment data into
the imported templates. `static/js/store.js` keeps the existing authenticated API
and background-job lifecycle. The browser never computes competency scores or
trusts an imported client-side answer key.

| UI feature | Existing backend |
| --- | --- |
| Language-first entry, sign-in, registration | `/api/auth/*`, `/api/framework` |
| Dashboard, skills, profile and recommendations | `/api/overview`, `/api/profile`, `/api/profile/update` |
| Username availability and account creation | `/api/auth/check-username`, `/api/auth/register-username` |
| Assessment start/resume, answer and results | `/api/quiz/*`, `/api/jobs/*` |
| Upload, extraction, indexing and source inspection | `/api/documents/*` |
| Course publishing and enrolment | `/api/courses`, `/api/courses/enrol` |
| Question generation and review | `/api/ai/generate-questions`, `/api/questions/review` |
| Assistant with source links | `/api/ai/chat`, `/api/documents/{id}` |
| Objectives, check-ins and progress | `/api/okrs*` |
| Workforce and role administration | `/api/admin*`, `/api/framework/mapping` |

The original repo's mock personas, fabricated scores, fixed competency boosts,
fake synchronization, hardcoded radar values and Groq service calls were not enabled.
Installed Ollama models and the existing RAG/LLM implementation remain in use.
No downloaded accounts, database, avatars, credentials or Node demo dependencies
were copied into the application. Unassessed levels remain unassessed; a real zero
is displayed as zero. User and model text are escaped before HTML rendering.

Opening the website still asks for English or Hindi, then shows sign-in/registration,
and leads to home after authentication. Staff-only material/workforce actions remain
permission protected. Model names and scoring internals stay out of learner screens.
Additional Hindi labels cover the imported dashboard and learning controls; source
content and some catalogue details retain their original language.

## Assessment behavior

Question n continues to use evidence through question n-2 within its competency.
The next question is prepared in the background. Submitting an answer automatically
advances; there is no intermediate Continue assessment prompt. The palette displays
saved/current/upcoming positions without exposing future questions or allowing edits
to already submitted answers. The server supplies each three-minute deadline and
evaluates results; course completion still requires a passing assessment.

CPU inference can still take time when the buffer is empty. Source-quote validation
does not prove the entire question is factually supported: a live smoke-check
question introduced details absent from the short uploaded source. Human review
remains necessary, as documented in INTEGRATION_STATUS.md; this UI import does not
change or claim to solve the existing model's accuracy limits.

## Verification

- All 11 isolated backend integration tests passed, including username uniqueness,
  authenticated profile persistence, photo validation, and prevention of role escalation.
- `tests/check_username.js` verifies uninterrupted typing, accurate availability,
  server-error handling and rejection of stale lookup responses. Username feedback
  updates in place without replacing the input. The local server was restarted to
  activate the username endpoint.
- Browser registration completed through all three steps. Edited location, experience,
  tools, statistical domains and training persisted after reloading the profile.
- `tests/check_frontend.js` passed for all 10 connected views, real zero/unassessed
  values, escaped user/model/source text, source links, question timer and direct
  answer-to-next-question handoff with one following background preparation.
- Browser checks covered language entry, login, every workspace section, profile
  persistence, objective creation, course publishing/enrolment and the learning
  timeline. A real local Llama course question was displayed; answer submission
  saved progress and advanced to question two.
- A temporary uploaded text document was extracted, embedded and indexed by the
  real backend. UI source links and assistant generation were checked against it.
- RAG and quiz generation modules remain unchanged by the account integration. Tests used a
  temporary database rather than the user's accounts, courses or evidence.

For frontend regression checks, start `python tests/preview_server.py` and run
`node tests/check_frontend.js`. The preview creates an isolated test account and
database. `STATSKILL_PREVIEW_STATIC` can point the preview at a staged frontend.

## Recovery

`../../.ui-integration-recovery/2026-09-04/ui-before-import.zip` contains the UI before
this change. `previous-static/` preserves the previous active frontend directory.
The downloaded upstream archive is retained in the same recovery area. Restore the
old UI separately from data; no database or model restoration is needed for a UI
rollback. Earlier cleanup recovery remains available in `.cleanup-recovery/`.
