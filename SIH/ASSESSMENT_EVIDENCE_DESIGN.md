# Evidence schema and scoring

Proposed before implementation on 4 September 2026; implemented additively.

`assessment_items` already persists each served question's JSON payload, topic, Bloom depth, options, server answer key, issue time, selected option, correctness and answer time. Copying that data into two more writable tables would introduce consistency risks.

| Relation | Design |
| --- | --- |
| `questions` | SQL view over `assessment_items`: question ID, session, position, question text, topic ID/name, Bloom integer/name, options, answer key, sources, issue time |
| `user_responses` | SQL view joining issued items to their session owner; exposes submitted responses, correctness, skip flag and answer time |
| `topic_competency` | Materialized summary keyed by user/topic; latest session, current level, weighted score, sample count, confidence, per-Bloom breakdown, scoring version, update time |

Question records retain the actual question served rather than a pointer to an editable template. Responses are written once by the existing authenticated, idempotent answer endpoint. Full evidence and answer keys are exposed to the assessment owner only after completion. Historical records are not rescored by a new LLM run; their available summaries are backfilled with explicit legacy confidence.

The weighted topic score is `100 × Σ(Bloom depth × correct) / Σ(Bloom depth served)`. Depths are 1 through 6; incorrect and skipped questions earn zero. Each summary also exposes served, answered, correct and skipped counts separately at each depth. Equal accuracy at different depths can have equal percentages, so the weighted percentage alone is not the proficiency level.

For level estimation, L1 requires at least two correct answers and at least 50% accuracy across the completed topic. L2-L6 require at least two answered observations at that Bloom depth or above and at least 60% correctness across all served questions at those depths. A completed topic that does not meet the L1 threshold is assigned **L0 — No Demonstrated Foundation / Needs Foundational Support**. Incorrect and skipped questions remain in the denominator; a topic with no served questions remains unassessed. Llama assesses evidence only after it clears the L1 gate and receives the evidence ceiling and per-depth statistics. Its assigned level cannot exceed that ceiling. Small samples are marked low confidence. Correct Apply or Analyze answers therefore demonstrate foundational knowledge even when no introductory questions were served.

These thresholds are explicit project policies, not a calibrated psychometric or government certification standard. Bloom depth describes a cognitive task; a multiple-choice question cannot fully demonstrate workplace creation or leadership. Required role levels remain unchanged from the supplied PDFs. Scoring is committed atomically with assessment completion and competency history; retries do not duplicate responses or history.
