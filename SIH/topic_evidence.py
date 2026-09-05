"""Normalized evidence views and versioned per-topic performance summaries."""
import json,time
from storage import db,encode

VERSION='bloom-evidence-v2-l0'
L0_LABEL='No Demonstrated Foundation / Needs Foundational Support'

def init():
    with db() as c:c.executescript('''
      CREATE VIEW IF NOT EXISTS questions AS
      SELECT i.id,i.session_id,i.position,json_extract(i.payload,'$.question') AS question_text,
        json_extract(i.payload,'$.competency_id') AS topic_id,json_extract(i.payload,'$.competency') AS topic,
        json_extract(i.payload,'$.bloom_level') AS bloom_level,json_extract(i.payload,'$.bloom_name') AS bloom_name,
        json_extract(i.payload,'$.options') AS options,json_extract(i.payload,'$.correct_answer') AS answer_key,
        json_extract(i.payload,'$.sources') AS sources,i.issued FROM assessment_items i;
      CREATE VIEW IF NOT EXISTS user_responses AS
      SELECT i.id AS question_id,i.session_id,a.user_id,i.answer AS selected_option,i.correct,i.answered,
        CASE WHEN i.answer IS NULL THEN 1 ELSE 0 END AS skipped
      FROM assessment_items i JOIN assessments a ON a.id=i.session_id WHERE i.answered IS NOT NULL;
      CREATE TABLE IF NOT EXISTS topic_competency(user_id TEXT,topic_id TEXT,session_id TEXT,current_level INTEGER,
        weighted_score REAL,evidence_count INTEGER,confidence TEXT,performance TEXT,scoring_version TEXT,updated REAL,
        PRIMARY KEY(user_id,topic_id));
      CREATE TABLE IF NOT EXISTS evidence_migrations(name TEXT PRIMARY KEY,applied REAL NOT NULL);
      CREATE INDEX IF NOT EXISTS topic_competency_session ON topic_competency(session_id);
    ''')
    # Only backfill already evaluated historical attempts; never run a new LLM job here.
    with db() as c:
        sessions=c.execute("SELECT id,user_id,result FROM assessments WHERE status='complete' ORDER BY created DESC").fetchall()
        for session in sessions:
            result=json.loads(session['result'] or '{}')
            for change in result.get('changes',[]):
                rows=c.execute("SELECT * FROM assessment_items WHERE session_id=? AND json_extract(payload,'$.competency_id')=?",(session['id'],change['competency_id'])).fetchall()
                if not rows or c.execute('SELECT 1 FROM topic_competency WHERE user_id=? AND topic_id=?',(session['user_id'],change['competency_id'])).fetchone():continue
                save(c,session['user_id'],session['id'],change['competency_id'],rows,change.get('evaluation') or dict(current_level=change.get('new_level'),confidence='legacy'))
    migrate_l0()
    migrate_foundation_floor()

def performance(rows):
    levels={str(i):dict(served=0,answered=0,correct=0,skipped=0) for i in range(1,7)}
    earned=possible=attempted=0
    for row in rows:
        q=json.loads(row['payload']);depth=max(1,min(6,int(q['bloom_level'])))
        level=levels[str(depth)];level['served']+=1;possible+=depth
        if row['answer'] is None:level['skipped']+=1
        else:level['answered']+=1;attempted+=1
        if row['correct']:level['correct']+=1;earned+=depth
    # L0 means the completed evidence did not demonstrate a repeatable foundation.
    supported=0 if rows else None
    if rows:
        correct_total=sum(v['correct'] for v in levels.values())
        if correct_total>=2 and correct_total/len(rows)>=.5:
            supported=1
    for depth in range(2,7):
        group=[levels[str(i)] for i in range(depth,7)]
        # Skips remain in the denominator; two observations prevent a single lucky answer establishing mastery.
        shown=sum(v['served'] for v in group);answers=sum(v['answered'] for v in group);correct=sum(v['correct'] for v in group)
        if answers>=2 and shown and correct/shown>=.6:supported=depth
    return dict(by_bloom=levels,weighted_score=round(100*earned/possible,2) if possible else None,
                evidence_count=len(rows),answered=attempted,maximum_supported_level=supported,version=VERSION)

def migrate_l0():
    """Correct completed results that received the former automatic L1 floor."""
    with db() as c:
        if c.execute("SELECT 1 FROM evidence_migrations WHERE name='l0-foundation-gate-v1'").fetchone():
            return
        sessions=c.execute("SELECT id,user_id,result,created FROM assessments WHERE status='complete' ORDER BY created").fetchall()
        for session in sessions:
            result=json.loads(session['result'] or '{}');changed=False
            result.setdefault('levels',{})['0']=L0_LABEL
            for change in result.get('changes',[]):
                rows=c.execute("SELECT * FROM assessment_items WHERE session_id=? AND json_extract(payload,'$.competency_id')=?",(session['id'],change['competency_id'])).fetchall()
                stats=performance(rows)
                if stats['maximum_supported_level']!=0:
                    continue
                evaluation=dict(current_level=0,confidence='high' if len(rows)>=3 else 'low',
                    reason='The completed responses did not demonstrate the foundational accuracy required for L1.',
                    evidence_ids=[row['id'] for row in rows],model=None,rubric='pdf-depth-llama-v3-l0',performance=stats)
                change.update(new_level=0,evaluation=evaluation)
                save(c,session['user_id'],session['id'],change['competency_id'],rows,evaluation)
                c.execute('''INSERT INTO competency_history(user_id,competency_id,old_level,new_level,session_id,created)
                  VALUES(?,?,?,?,?,?) ON CONFLICT(session_id,competency_id) DO UPDATE SET new_level=excluded.new_level''',
                  (str(session['user_id']),change['competency_id'],change.get('old_level') or 0,0,session['id'],session['created']))
                changed=True
            if changed:
                c.execute('UPDATE assessments SET result=? WHERE id=?',(encode(result),session['id']))
        latest=c.execute('''SELECT h.user_id,h.competency_id,h.new_level FROM competency_history h
          WHERE h.id=(SELECT h2.id FROM competency_history h2 WHERE h2.user_id=h.user_id AND h2.competency_id=h.competency_id ORDER BY h2.created DESC,h2.id DESC LIMIT 1)''').fetchall()
        for row in latest:
            c.execute('''INSERT INTO competency_profiles VALUES(?,?,?) ON CONFLICT(user_id,competency_id)
              DO UPDATE SET current_level=excluded.current_level''',(row['user_id'],row['competency_id'],row['new_level']))
        c.execute("INSERT INTO evidence_migrations VALUES('l0-foundation-gate-v1',?)",(time.time(),))

def migrate_foundation_floor():
    """Restore L1 where completed historical evidence meets the revised foundation gate."""
    with db() as c:
        name='l0-foundation-gate-v2'
        if c.execute('SELECT 1 FROM evidence_migrations WHERE name=?',(name,)).fetchone():
            return
        sessions=c.execute("SELECT id,user_id,result,created FROM assessments WHERE status='complete' ORDER BY created").fetchall()
        for session in sessions:
            result=json.loads(session['result'] or '{}');changed=False
            result.setdefault('levels',{})['0']=L0_LABEL
            for change in result.get('changes',[]):
                if change.get('new_level')!=0:
                    continue
                rows=c.execute("SELECT * FROM assessment_items WHERE session_id=? AND json_extract(payload,'$.competency_id')=?",(session['id'],change['competency_id'])).fetchall()
                stats=performance(rows);ceiling=stats['maximum_supported_level']
                if ceiling is None or ceiling<1:
                    continue
                cached=c.execute('SELECT payload FROM assessment_evaluations WHERE session_id=? AND competency_id=?',(session['id'],change['competency_id'])).fetchone()
                prior=json.loads(cached['payload']) if cached else {}
                prior_level=prior.get('current_level')
                level=prior_level if type(prior_level) is int and 1<=prior_level<=ceiling else 1
                correct=sum(bool(row['correct']) for row in rows)
                depths=sorted({int(json.loads(row['payload']).get('bloom_level',1)) for row in rows if row['correct']})
                evaluation=dict(current_level=level,confidence='medium' if len(rows)>=4 else 'low',
                    reason=f'{correct} of {len(rows)} saved answers were correct at Bloom depths {depths}; this demonstrates an L1 foundation.',
                    evidence_ids=[row['id'] for row in rows if row['correct']],model=prior.get('model'),
                    rubric='pdf-depth-llama-v4-l0',performance=stats)
                change.update(new_level=level,evaluation=evaluation)
                save(c,session['user_id'],session['id'],change['competency_id'],rows,evaluation)
                c.execute('''INSERT INTO competency_history(user_id,competency_id,old_level,new_level,session_id,created)
                  VALUES(?,?,?,?,?,?) ON CONFLICT(session_id,competency_id) DO UPDATE SET new_level=excluded.new_level''',
                  (str(session['user_id']),change['competency_id'],change.get('old_level') or 0,level,session['id'],session['created']))
                changed=True
            if changed:
                c.execute('UPDATE assessments SET result=? WHERE id=?',(encode(result),session['id']))
        latest=c.execute('''SELECT h.user_id,h.competency_id,h.new_level FROM competency_history h
          WHERE h.id=(SELECT h2.id FROM competency_history h2 WHERE h2.user_id=h.user_id AND h2.competency_id=h.competency_id ORDER BY h2.created DESC,h2.id DESC LIMIT 1)''').fetchall()
        for row in latest:
            c.execute('''INSERT INTO competency_profiles VALUES(?,?,?) ON CONFLICT(user_id,competency_id)
              DO UPDATE SET current_level=excluded.current_level''',(row['user_id'],row['competency_id'],row['new_level']))
        c.execute('INSERT INTO evidence_migrations VALUES(?,?)',(name,time.time()))

def save(c,user_id,sid,topic,rows,evaluation):
    stats=performance(rows)
    c.execute('''INSERT INTO topic_competency VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(user_id,topic_id) DO UPDATE SET
      session_id=excluded.session_id,current_level=excluded.current_level,weighted_score=excluded.weighted_score,
      evidence_count=excluded.evidence_count,confidence=excluded.confidence,performance=excluded.performance,scoring_version=excluded.scoring_version,updated=excluded.updated''',
      (str(user_id),topic,sid,evaluation.get('current_level'),stats['weighted_score'],len(rows),evaluation.get('confidence','low'),encode(stats),VERSION,time.time()))

def for_user(user_id):
    with db() as c:rows=c.execute('SELECT * FROM topic_competency WHERE user_id=?',(str(user_id),)).fetchall()
    return [dict(r,performance=json.loads(r['performance'])) for r in rows]
