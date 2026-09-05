from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'README.md';s=p.read_text(encoding='utf-8')
s=s.replace('The optional `llama3.2:3b` model accelerates English initial-assessment drafts when configured with `STATSKILL_QUIZ_MODEL`.','`llama3.2:3b` handles simpler English questions; Llama 3.1 8B handles advanced, Hindi and document-grounded questions, assessment evaluation and iGOT course ranking.')
s=s.replace('- English/Hindi language choice, registration and sign-in.','- English/Hindi entry and registration for the four selected ministries and their 17 work areas.')
s=s.replace('- Adaptive assessments with background preparation: question n uses evidence through question n-2 within the same competency. No whole-assessment preload.','- Adaptive assessments with prepared alternative pools: question n depends on answer n−2 within the same competency; no model call occurs between questions.')
s=s.replace('Model generation can still take time when a prepared question is not ready.','The initial pool preparation can take several minutes on CPU, and results evaluation runs after the final answer.')
s=s.replace('See [USER_FLOW.md]', 'See [SOUL_INTEGRATION.md](SOUL_INTEGRATION.md) for the current repository review, model routing, supplied-PDF mappings and validation. See [USER_FLOW.md]')
p.write_text(s,encoding='utf-8')
p=ROOT/'INTEGRATION_STATUS.md';s=p.read_text(encoding='utf-8');file_support=s[s.index('## File support'):s.index('## Validation',s.index('## File support'))]
p.write_text('''# Integration status

Current implementation and verification are documented in [SOUL_INTEGRATION.md](SOUL_INTEGRATION.md).

- Four selected ministries, 17 work areas and 102 role entries are shared across account forms and backend validation.
- Supplied PDF mappings retain six proficiency levels and all relevant competencies; model estimates never change required levels.
- SOUL question-generation logic is adapted to installed local Llama models and existing sqlite-vec RAG.
- Prepared pools cover every reachable question depth. Answer submission selects the next question without inference or a Continue prompt.
- Llama 3.1 8B evaluates saved evidence and ranks verified iGOT catalogue entries. Unsupported outputs fail visibly instead of fabricating results.
- Existing profiles, assessment history, uploads, local courses, permissions, source previews and OKRs remain connected.
- Eleven HTTP tests, five model-contract tests and frontend regressions passed. Local model inference and account/profile browser flows were checked with isolated records.

Initial preparation and post-assessment evaluation still take time. The iGOT catalogue is a limited public subset, and iGOT sign-in/enrolment/completion are external. Legacy accounts must select a supported work area before a new role assessment. MCQs estimate demonstrated knowledge; they do not certify workplace performance.

'''+file_support+'''## Run

Run `./run.ps1` from this folder, then open `http://127.0.0.1:8000`.
Preserve `igot_demo.db`, `users.json`, uploads, configuration and backups when updating.
Model settings are in `.env.example`. Recovery snapshots for this integration are in the workspace's `.soul-integration` folder.
''',encoding='utf-8')
p=ROOT/'USER_FLOW.md';s=p.read_text(encoding='utf-8')
a=s.index('3. Registration');b=s.index('4. Successful',a)
s=s[:a]+'''3. Registration selects one of four supported ministries, its work area and a PDF-listed designation, then collects profile details, a unique username and a password. The profile and account are saved together.
'''+s[b:]
a=s.index('Assessment answers advance');b=s.index('Framework and model',a)
s=s[:a]+'''Assessment answers advance automatically with no Continue prompt. Before the first question, validated alternative questions are prepared for every reachable difficulty. The answer to question n−2 determines which alternative appears at question n. Once preparation finishes, no model generation runs between questions. Preparation can take several minutes; timers begin only when questions are issued. Evaluation runs after the last answer.

'''+s[b:]
a=s.index('Validation:');s=s[:a]+'Validation details and current limits are recorded in SOUL_INTEGRATION.md.\n'
p.write_text(s,encoding='utf-8')
