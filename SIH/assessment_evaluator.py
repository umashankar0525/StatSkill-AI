"""Apply the L0 evidence gate, then let Llama interpret evidence against levels L1-L6."""
import hashlib,json
from storage import db,encode
from role_catalog import LEVELS
import model_tasks
import topic_evidence
import generation_runtime as runtime

RUBRIC_VERSION='pdf-depth-llama-v4-l0'
def init():
    with db() as c:
        c.execute('CREATE TABLE IF NOT EXISTS assessment_evaluations(session_id TEXT,competency_id TEXT,fingerprint TEXT,payload TEXT,PRIMARY KEY(session_id,competency_id))')
        c.execute('CREATE TABLE IF NOT EXISTS assessment_evaluation_progress(session_id TEXT PRIMARY KEY,payload TEXT NOT NULL)')

def progress(sid):
    with db() as c:row=c.execute('SELECT payload FROM assessment_evaluation_progress WHERE session_id=?',(sid,)).fetchone()
    return json.loads(row[0]) if row else None

def save_progress(sid,value):
    with db() as c:c.execute('INSERT OR REPLACE INTO assessment_evaluation_progress VALUES(?,?)',(sid,encode(value)))

def evaluate(sid,competency,rows):
    evidence=[]
    for row in rows:
        q=json.loads(row['payload'])
        evidence.append(dict(id=row['id'],question=q['question'],options=q['options'],answer=None if row['answer'] is None else q['options'][row['answer']],
                             expected=q['correct_answer'],correct=bool(row['correct']),depth=q.get('proficiency_level',q['bloom_level'])))
    stats=topic_evidence.performance(rows)
    attempted=[e for e in evidence if e['answer'] is not None]
    if stats['maximum_supported_level'] is None:
        return dict(current_level=None,confidence='insufficient',reason='No assessment evidence exists for this skill.',evidence_ids=[],model=None,rubric=RUBRIC_VERSION,performance=stats)
    if stats['maximum_supported_level']==0:
        return dict(current_level=0,confidence='high' if len(evidence)>=3 else 'low',
                    reason='The completed responses did not demonstrate the foundational accuracy required for L1.',
                    evidence_ids=[e['id'] for e in evidence],model=None,rubric=RUBRIC_VERSION,performance=stats)
    request={'competency':competency,'levels':LEVELS,'evidence':evidence,'performance_by_depth':stats,'maximum_supported_level':min(stats['maximum_supported_level'],max([e['depth'] for e in attempted if e['correct']] or [0]))}
    fingerprint=hashlib.sha256(encode(dict(request=request,rubric=RUBRIC_VERSION,model=model_tasks.EVALUATION_MODEL)).encode()).hexdigest()
    with db() as c:cached=c.execute('SELECT payload FROM assessment_evaluations WHERE session_id=? AND competency_id=? AND fingerprint=?',(sid,competency,fingerprint)).fetchone()
    if cached:return json.loads(cached['payload'])
    system='''Assess demonstrated current proficiency from the saved MCQ responses and six-level rubric.
The supplied correctness flags and expected answers are the server's answer key; do not rewrite them.
Required job level is not evidence of ability. Consider every correct, incorrect and skipped question.
Assign an integer level 1–6, never above maximum_supported_level. Level 1 means foundational;
multiple failures must reduce confidence and the estimate. MCQs estimate knowledge, not certified
workplace performance. Cite only provided evidence IDs. Do not invent a score or achieved skill.
Return {"current_level":1,"confidence":"low|medium|high","reason":"short evidence-based explanation",
"evidence_ids":["id"]}. Keep the explanation under 70 words.'''
    properties={'current_level':{'type':'integer','minimum':1,'maximum':request['maximum_supported_level']},
                'confidence':{'type':'string','enum':['low','medium','high']},'reason':{'type':'string','minLength':5,'maxLength':1500},
                'evidence_ids':{'type':'array','minItems':1,'uniqueItems':True,'items':{'type':'string','enum':[e['id'] for e in evidence]}}}
    schema={'type':'object','properties':properties,'required':list(properties),'additionalProperties':False}
    def infer(attempt):
        runtime.event('evaluation_attempt',topic=competency,attempt=attempt)
        value,model=model_tasks.json_task('evaluation',system,request,tokens=650,schema=schema)
        level=value.get('current_level');ids=value.get('evidence_ids');reason=value.get('reason')
        if type(level) is not int or not 1<=level<=min(6,request['maximum_supported_level']):raise ValueError('Assessment evaluator returned an unsupported proficiency level.')
        if not isinstance(ids,list) or not ids or any(not isinstance(i,str) or i not in {e['id'] for e in evidence} for i in ids):raise ValueError('Assessment evaluator cited invalid evidence.')
        if not isinstance(reason,str) or not 5<=len(reason)<=1500 or value.get('confidence') not in ('low','medium','high'):raise ValueError('Assessment evaluator returned an invalid explanation.')
        return value,model
    token=runtime.context.set({**runtime.context.get(),'session_id':sid,'topic':competency})
    try:value,model=runtime.retry(infer)
    finally:runtime.context.reset(token)
    level=value['current_level'];ids=value['evidence_ids'];reason=value['reason']
    result=dict(current_level=level,confidence='low' if len(attempted)<3 else value['confidence'],reason=reason,evidence_ids=ids,model=model,rubric=RUBRIC_VERSION,performance=stats)
    with db() as c:c.execute('INSERT OR REPLACE INTO assessment_evaluations VALUES(?,?,?,?)',(sid,competency,fingerprint,encode(result)))
    return result
