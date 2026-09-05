# Website flow

The frontend now uses the UI imported from the supplied GitHub repository, adapted to the existing local backend. This follows the later request to copy that UI and supersedes the earlier feature-reference-only styling direction. See UI_IMPORT.md for source provenance and integration details.

1. Opening or refreshing the site presents English and Hindi language choices.
2. After selection, signed-out visitors go directly to sign-in, with an option to
   register. A valid existing session returns to home after language selection.
3. Registration selects one of four supported ministries, its work area and a PDF-listed designation, then collects profile details, a unique username and a password. The profile and account are saved together.
4. Successful sign-in and registration both open the home page.
5. Home leads to skills, assessments, suggested learning, enrolled courses, goals,
   progress reports and the profile. Staff also see materials and workforce tools.

Assessment answers advance automatically with no Continue prompt. The server prepares two opening questions before starting, then prepares question n+1 while question n is displayed. Because question n+1 uses answers only through n−1, the question shown at n+1 still reflects the required two-question delayed adaptation. Timers begin only when questions are issued. Study material is preferred; a missing or unverifiable source quotation triggers a role/topic/Bloom-specific general-knowledge question instead of stopping the assessment. Evaluation runs after the last answer.

Framework and model names, adaptation/scoring internals, infrastructure status and
converter explanations are removed from normal interface copy. Role mapping, quiz
generation, document processing and goal calculations still run in the backend.
Development limitations remain in INTEGRATION_STATUS.md. Test OTP mode is labelled
honestly until a delivery gateway is configured.

English/Hindi translations cover the entry flow, home, navigation, work-role fields,
standard role/activity/skill labels and common learning controls. User-entered names,
uploaded source material and some existing catalogue/report details remain in their
original language. New assessments and assistant responses request the chosen
language; saved questions retain the language in which they were created.

Validation details and current limits are recorded in SOUL_INTEGRATION.md.
