"""Real GPU-backed quiz batches from the supplied, indexed PDFs; isolated test writes."""
import json,os,sqlite3,time,urllib.request
from pathlib import Path
os.environ['STATSKILL_GPU_LAYERS']='24'
import test_integration as app
import generation_runtime as runtime
ROOT=Path(__file__).resolve().parents[1]
source=sqlite3.connect(f'file:{(ROOT/"igot_demo.db").as_posix()}?mode=ro',uri=True)
sid='d9a6b30db8844828d75d11a199ac665b';started=time.monotonic();results=[]
bank=source.execute('SELECT bank_id FROM assessment_buffers WHERE session_id=?',(sid,)).fetchone()[0]
for cid in ['C_COMMUNICATION','C_SQL','C_DIGITAL_SIGNATURES','C_PRICE']:
    samples=[json.loads(r[0]) for r in source.execute('SELECT payload FROM quiz_pools WHERE bank_id=? AND competency_id=? ORDER BY depth,ordinal',(bank,cid))]
    accepted=[]
    for batch in range(4):
        if len(accepted)>=2:break
        def generate(attempt):
            example=samples[(batch+attempt-1)%len(samples)]
            passages=[source.execute('SELECT chunk_text FROM doc_chunks WHERE rowid=?',(item['id'],)).fetchone()[0] for item in example['sources']]
            material='\n\n[Next source passage]\n\n'.join(passages)[:3600]
            return app.rag_engine.generate_mcqs_with_llm(material,example['competency'],'Understand','Statistical Officer',{'_offset':batch+3,'_attempt':attempt},[q['question'] for q in accepted],2-len(accepted))
        accepted.extend(runtime.retry(generate))
    assert len(accepted)==2
    results.append({'topic':cid,'questions':accepted})
    with app.db() as c:events=[dict(r) for r in c.execute('SELECT event,payload FROM generation_events')]
    with urllib.request.urlopen('http://127.0.0.1:11434/api/ps') as r:models=json.load(r)['models']
    gpu=next(m for m in models if m['name']=='llama3.1:8b');assert gpu['size_vram']>0
    report={'results':results,'events':events,'elapsed_seconds':round(time.monotonic()-started,2),'gpu_bytes':gpu['size_vram'],'context_length':gpu['context_length']}
    (ROOT/'tmp/gpu-generation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'topic':cid,'accepted':2,'elapsed':report['elapsed_seconds'],'gpu_mb':round(gpu['size_vram']/1048576)}),flush=True)
source.close()
print('PASS: eight grounded quiz questions, four topics, GPU residency verified.',flush=True)
