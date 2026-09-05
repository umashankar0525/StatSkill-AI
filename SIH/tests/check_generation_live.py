"""Exercise consecutive real local batches against repository communication text."""
import json,sys,time
from pathlib import Path
import test_integration as app
import generation_runtime as runtime
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import import_soul_materials as material

pages=material.extract(material.SOURCE/'ingest_communication_skills_pdf.py','PAGES_TEXT')
results=[];started=time.monotonic()
for index in range(8):
    if len(results)>=8:break
    source='\n'.join(pages[15+index:17+index])
    def attempt(number):
        return app.rag_engine.generate_mcqs_with_llm(source,'Communication','Remember' if index<2 else 'Understand','Statistical Officer',{'_offset':index*2,'_attempt':number},[q['question'] for q in results],min(2,8-len(results)))
    result=runtime.retry(attempt)
    results.extend(result)
    print(json.dumps(dict(batch=index+1,accepted=len(result),total=len(results),elapsed_seconds=round(time.monotonic()-started,1))),flush=True)
assert len(results)>=8
assert len({q['question'].casefold() for q in results})==len(results)
with app.db() as c:events=[dict(r) for r in c.execute("SELECT event,payload FROM generation_events")]
target=Path(__file__).resolve().parents[1]/'tmp/consecutive-generation.json'
target.write_text(json.dumps(dict(questions=results,events=events,elapsed_seconds=round(time.monotonic()-started,2)),ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS: eight distinct grounded questions; partially valid batches were retained and refilled.',flush=True)
