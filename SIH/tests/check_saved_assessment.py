"""Replay the real prepared bank in an isolated DB, then verify real GPU evaluation."""
import json,sqlite3,time,urllib.request
from pathlib import Path
from unittest.mock import patch
import test_integration as app
ROOT=Path(__file__).resolve().parents[1]
source=sqlite3.connect(f'file:{(ROOT/"igot_demo.db").as_posix()}?mode=ro',uri=True);source.row_factory=sqlite3.Row
original='d9a6b30db8844828d75d11a199ac665b'
session=dict(source.execute('SELECT * FROM assessments WHERE id=?',(original,)).fetchone())
buffer=dict(source.execute('SELECT * FROM assessment_buffers WHERE session_id=?',(original,)).fetchone())
pool=[tuple(r) for r in source.execute('SELECT * FROM quiz_pools WHERE bank_id=?',(buffer['bank_id'],))]
source.close();assert len(pool)==48 and buffer['status']=='ready' and session['target']==32
with app.db() as c:c.executemany('INSERT INTO quiz_pools VALUES(?,?,?,?,?)',pool)
durations=[];evidence=[]
for mode in ('correct','incorrect','alternating'):
    sid='gpu-replay-'+mode;user={'id':sid};record={**session,'id':sid,'user_id':sid,'result':None,'status':'active'}
    with app.db() as c:
        c.execute('INSERT INTO assessments('+','.join(record)+') VALUES('+','.join('?' for _ in record)+')',list(record.values()))
        c.execute('INSERT INTO assessment_buffers VALUES(?,?,?,?,?,?)',(sid,buffer['bank_id'],'ready',48,48,None))
    with patch.object(app.rag_engine,'chat',side_effect=AssertionError('A question transition must not invoke the model.')):
        current=app.quiz_service.next_question(sid,user);seen=set()
        for position in range(1,33):
            q=current['question'];assert q['position']==position and q['question'] not in seen;seen.add(q['question'])
            assert current['preparation']['total']==32 and current['preparation']['ready']==32
            with app.db() as c:private=json.loads(c.execute('SELECT payload FROM assessment_items WHERE id=?',(q['id'],)).fetchone()[0])
            answer=private['options'].index(private['correct_answer'])
            if mode=='incorrect' or mode=='alternating' and position%2:answer=(answer+1)%4
            start=time.perf_counter();current=app.quiz_service.answer(user,{'session_id':sid,'question_id':q['id'],'answer':answer})['session'];durations.append(time.perf_counter()-start)
        assert current['answered']==32 and current['question'] is None
    if mode=='correct':
        with app.db() as c:evidence=[dict(r) for r in c.execute("SELECT * FROM assessment_items WHERE session_id=? AND json_extract(payload,'$.competency_id')='C_COMMUNICATION'",(sid,))]
assert max(durations)<1
started=time.monotonic();evaluation=app.assessment_evaluator.evaluate('gpu-evaluation','C_COMMUNICATION',evidence)
with urllib.request.urlopen('http://127.0.0.1:11434/api/ps') as r:models=json.load(r)['models']
model=next(m for m in models if m['name']=='llama3.1:8b');assert model['size_vram']>0
report={'replayed_questions':96,'max_handoff_ms':round(max(durations)*1000,2),'mean_handoff_ms':round(sum(durations)/len(durations)*1000,2),'evaluation_seconds':round(time.monotonic()-started,2),'evaluation':evaluation,'evaluation_gpu_bytes':model['size_vram'],'evaluation_context':model['context_length']}
(ROOT/'tmp/saved-assessment-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
