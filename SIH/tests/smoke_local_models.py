"""Optional live Ollama smoke test, isolated from learner records."""
import json,time,urllib.request
from pathlib import Path
import test_integration as app

start=time.perf_counter()
tags=json.load(urllib.request.urlopen('http://127.0.0.1:11434/api/tags'))
names={m['name'] for m in tags['models']}
assert {'llama3.1:8b','llama3.2:3b'}<=names
print('Both local model manifests are available.',flush=True)
source='Stratified sampling divides the population into non-overlapping strata and draws a sample from every stratum. This ensures that every stratum is represented in the sample.'
p=dict(role_id='PDF_A01_L3',assessment_role_id='PDF_A01_L3',ministry=app.role_catalog.ROLES['PDF_A01_L3']['ministry'],department='Survey Methodology & Sampling',designation='Assistant Director',language='en')
q=app.rag_engine.generate_mcq_with_llm(source,'Sampling','Apply','Assistant Director',p,[])
q.update(bloom_level=3)
print('Local quiz generation and exact source-quote validation passed.',flush=True)
rows=[dict(id='smoke-evidence-1',payload=json.dumps(q),answer=q['options'].index(q['correct_answer']),correct=1)]
evaluated=app.assessment_evaluator.evaluate('live-smoke','C_SAMPLING',rows)
print('Local 8B assessment evaluation passed.',flush=True)
gaps=[dict(competency_id='C_CYBER',competency_name='Cybersecurity',current_level=1,required_level=4,gap=3)]
recommended=app.recommendation_service.recommend({'id':'live-smoke'},p,gaps)
print('Local 8B course recommendation passed.',flush=True)
result=dict(models=sorted(names),question=q,evaluation=evaluated,recommendations=recommended,elapsed_seconds=round(time.perf_counter()-start,2))
path=Path(__file__).resolve().parents[1]/'tmp/local-model-smoke.json'
path.parent.mkdir(exist_ok=True)
path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(quiz_model=q['generation_model'],evaluation_model=evaluated['model'],recommendation_model=recommended['model'],elapsed_seconds=result['elapsed_seconds'])),flush=True)
