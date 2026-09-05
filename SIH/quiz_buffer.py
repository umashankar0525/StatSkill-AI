"""Rolling, source-grounded question preparation.

The opening two questions are generated before the timer starts. Thereafter the
next question is generated while the learner answers the current one. Because
Q(n) only uses answers through Q(n-2), its difficulty is known during Q(n-1).
"""
import json
import os

from storage import db, encode
import rag_engine as rag
import generation_runtime as runtime
import adaptive_quiz_engine as cat


def init():
    with db() as c:
        c.executescript('''CREATE TABLE IF NOT EXISTS quiz_pools(bank_id TEXT,competency_id TEXT,depth INTEGER,ordinal INTEGER,payload TEXT,PRIMARY KEY(bank_id,competency_id,depth,ordinal));
        CREATE TABLE IF NOT EXISTS assessment_buffers(session_id TEXT PRIMARY KEY,bank_id TEXT,status TEXT,total INTEGER,ready INTEGER,error TEXT);
        CREATE TABLE IF NOT EXISTS document_assignments(doc_id TEXT,role_id TEXT,PRIMARY KEY(doc_id,role_id));
        CREATE TABLE IF NOT EXISTS document_topics(doc_id TEXT,competency_id TEXT,PRIMARY KEY(doc_id,competency_id));
        CREATE TABLE IF NOT EXISTS document_provenance(doc_id TEXT PRIMARY KEY,source_uri TEXT,source_hash TEXT,source_kind TEXT);''')


def start_depth(comp, profile):
    return comp['required_level'] if profile.get('assessment_role_id') else 3


def status(sid):
    with db() as c:
        row = c.execute('SELECT * FROM assessment_buffers WHERE session_id=?', (sid,)).fetchone()
        session = c.execute('SELECT target FROM assessments WHERE id=?', (sid,)).fetchone()
        if not row or not session:
            return None
        issued = c.execute('SELECT count(*) FROM assessment_items WHERE session_id=?', (sid,)).fetchone()[0]
        drafts = c.execute('SELECT count(*) FROM question_drafts WHERE session_id=?', (sid,)).fetchone()[0]
    return dict(status=row['status'], total=session['target'], ready=min(session['target'], issued + drafts), error=row['error'])


def assigned_sources(comp, profile, doc_id):
    if doc_id:
        return rag.retrieve_context(comp['name'], doc_id=doc_id, top_k=6)
    with db() as c:
        assigned = [r[0] for r in c.execute('''SELECT a.doc_id FROM document_assignments a
          JOIN documents d ON d.id=a.doc_id JOIN document_topics t ON t.doc_id=d.id
          WHERE a.role_id=? AND t.competency_id=? AND d.status=?''',
          (profile['role_id'], comp['id'], 'ready'))]
    return rag.retrieve_context(comp['name'], top_k=6, doc_ids=assigned)


def _saved_questions(sid, competency_id):
    with db() as c:
        rows = c.execute('''SELECT position,payload FROM assessment_items WHERE session_id=?
          UNION ALL SELECT position,payload FROM question_drafts WHERE session_id=? ORDER BY position''', (sid, sid)).fetchall()
    same_topic,other_topics = [],[]
    for row in rows:
        value = json.loads(row['payload'])
        if value.get('competency_id') == competency_id:
            same_topic.append(value['question'])
        else:
            other_topics.append(value['question'])
    # Validation sees the entire assessment. Same-topic stems are last so the compact
    # prompt window always gives the model the most relevant examples to avoid.
    return other_topics + same_topic


def _generate(sid, user, plans):
    """Generate one homogeneous group; valid partial batches are returned."""
    first = plans[0]
    session = first['session']
    profile = json.loads(session['profile'])
    comp = first['comp']
    sources = assigned_sources(comp, profile, session['doc_id'])
    previous = _saved_questions(sid, comp['id'])
    rejected = []
    count = len(plans)
    batch_id = f"{comp['id']}:{first['bloom']}:{first['position']}"

    def request(attempt, general=False):
        runtime.event('batch_started', batch_id=batch_id, topic=comp['id'], depth=first['bloom'], count=count, attempt=attempt, grounding='general knowledge' if general else 'study material')
        offset = (first['position'] + first['bloom'] + attempt - 1) % max(1, len(sources))
        selected = [] if general else (sources[offset:] + sources[:offset])[:3]
        material = 'NONE' if general else '\n\n[Next source passage]\n\n'.join(x['text'] for x in selected)[:3600]
        # A single upcoming slot asks the fast model for three alternatives. The
        # first unique candidate wins, avoiding serial one-candidate retries.
        requested=count if count>1 else 3
        try:
            args=(
                material, comp['name'], cat.BLOOMS_LEVELS[first['bloom']], profile['designation'],
                {**profile, '_offset': first['position'] + first['bloom'], '_attempt': attempt},
                previous + rejected, requested,
            )
            batch = rag.generate_mcqs_with_llm(*args)
        except runtime.GenerationError as exc:
            candidate=getattr(exc,'candidate',None)
            if exc.code=='duplicate' and candidate and candidate not in rejected:
                rejected.append(candidate)
                runtime.event('duplicate_reprompted',batch_id=batch_id,topic=comp['id'],attempt=attempt)
            raise
        if not batch:
            raise runtime.GenerationError('invalid_output', 'The model returned no usable questions.')
        for question in batch:
            question.update(
                competency_id=comp['id'], competency=comp['name'], bloom_level=first['bloom'],
                bloom_name=cat.BLOOMS_LEVELS[first['bloom']], proficiency_level=first['bloom'],
                sources=[{k: v for k, v in x.items() if k not in ('text', 'score')} for x in selected],
                grounding='model knowledge' if general else 'study material',
            )
        return batch

    def generate(general):
        return runtime.retry(lambda attempt:request(attempt,general),attempts=3)

    if not sources:
        runtime.event('general_knowledge_fallback', batch_id=batch_id, topic=comp['id'], reason='no assigned study material')
        return generate(True)
    try:
        return generate(False)
    except runtime.GenerationError as exc:
        if exc.code!='quotation_missing' and (exc.code!='invalid_output' or 'quotation' not in str(exc).casefold()):
            raise
        runtime.event('general_knowledge_fallback', batch_id=batch_id, topic=comp['id'], reason=str(exc))
        return generate(True)


def ensure(sid, user):
    """Fill only the opening pair or the single question following the current one."""
    import quiz_service as quiz
    session = quiz.session_row(sid, user)
    with quiz.lock('drafts-' + sid):
        with db() as c:
            issued = c.execute('SELECT count(*) FROM assessment_items WHERE session_id=?', (sid,)).fetchone()[0]
            pending = c.execute('SELECT 1 FROM assessment_items WHERE session_id=? AND answered IS NULL', (sid,)).fetchone()
            existing = {r[0] for r in c.execute('SELECT position FROM question_drafts WHERE session_id=?', (sid,))}
        if issued == 0:
            wanted = list(range(1, min(2, session['target']) + 1))
        else:
            wanted = [issued + 1] if issued < session['target'] else []
        wanted = [position for position in wanted if position not in existing]
        with db() as c:
            c.execute('''INSERT INTO assessment_buffers VALUES(?,?,?,?,?,?)
              ON CONFLICT(session_id) DO UPDATE SET status='preparing',total=excluded.total,ready=excluded.ready,error=NULL''',
              (sid, 'rolling-v1', 'preparing', session['target'], issued + len(existing), None))
        token = runtime.context.set({'session_id': sid, 'buffer': 'rolling-v1'})
        try:
            while wanted:
                plans = [quiz.question_plan(sid, user, position=p) for p in wanted]
                plans = [p for p in plans if p]
                if not plans:
                    break
                first = plans[0]
                group = [p for p in plans if p['comp']['id'] == first['comp']['id'] and p['bloom'] == first['bloom']]
                limit = max(1, min(3, int(os.environ.get('STATSKILL_QUIZ_BATCH_SIZE', '2'))))
                group = group[:limit]
                batch = _generate(sid, user, group)
                for plan, question in zip(group, batch):
                    with db() as c:
                        c.execute('INSERT OR IGNORE INTO question_drafts VALUES(?,?,?,?)',
                                  (sid, plan['position'], plan['bloom'], encode(question)))
                    wanted.remove(plan['position'])
            with db() as c:
                drafts = c.execute('SELECT count(*) FROM question_drafts WHERE session_id=?', (sid,)).fetchone()[0]
                c.execute("UPDATE assessment_buffers SET status='ready',ready=?,error=NULL WHERE session_id=?", (issued + drafts, sid))
            return {}
        except Exception as exc:
            state = 'blocked' if getattr(exc, 'code', None) == 'missing_material' else 'failed'
            with db() as c:
                c.execute('UPDATE assessment_buffers SET status=?,error=? WHERE session_id=?', (state, str(exc), sid))
            raise
        finally:
            runtime.context.reset(token)


def select(plan):
    with db() as c:
        row = c.execute('SELECT payload FROM question_drafts WHERE session_id=? AND position=? AND bloom=?',
                        (plan['sid'], plan['position'], plan['bloom'])).fetchone()
    if not row:
        raise ValueError('The next question is still being prepared.')
    return json.loads(row[0])
