"""Benchmark real source-grounded generation with the small local model in isolation."""
import json,os,sqlite3,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ['STATSKILL_QUIZ_REASONING_MODEL']='llama3.2:3b'
import test_integration as app
import generation_runtime as runtime

source=sqlite3.connect(f'file:{(ROOT/"igot_demo.db").as_posix()}?mode=ro',uri=True)
cases=[('C_COMMUNICATION','Communication','communication'),('C_SQL','SQL','SELECT'),('C_DIGITAL_SIGNATURES','Digital Signatures','digital signature'),('C_PRICE','Price Statistics','price')]
results=[];started=time.monotonic()
for cid,name,term in cases:
    rows=source.execute("SELECT c.chunk_text,c.doc_id,c.page_num FROM doc_chunks c JOIN document_topics t ON t.doc_id=c.doc_id WHERE t.competency_id=? AND lower(c.chunk_text) LIKE ? ORDER BY length(c.chunk_text) DESC LIMIT 3",(cid,'%'+term.lower()+'%')).fetchall()
    assert rows
    text='\n'.join(r[0] for r in rows)[:3600]
    accepted=[];batch=0
    while len(accepted)<2:
        batch+=1
        if batch>4:raise AssertionError('Too many invalid outputs')
        accepted.extend(runtime.retry(lambda attempt:app.rag_engine.generate_mcqs_with_llm(text,name,'Remember','Statistical Officer',{'_offset':batch,'_attempt':attempt},[q['question'] for q in accepted],2-len(accepted))))
    results.append({'topic':cid,'questions':accepted,'sources':[{'doc_id':r[1],'page':r[2]} for r in rows]})
    print(json.dumps({'topic':cid,'accepted':len(accepted),'elapsed':round(time.monotonic()-started,1)}),flush=True)
    with app.db() as c:events=[dict(r) for r in c.execute('SELECT event,payload FROM generation_events')]
    (ROOT/'tmp/small-model-generation.json').write_text(json.dumps({'results':results,'events':events,'seconds':round(time.monotonic()-started,2)},ensure_ascii=False,indent=2),encoding='utf-8')
source.close()
print('PASS: eight grounded questions from four supplied-document topics.',flush=True)
