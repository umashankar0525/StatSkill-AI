"""A small real-model latency and source-grounding check; no learner data is used."""
import json
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import rag_engine as rag
source='Stratified sampling divides a population into non-overlapping groups and draws a sample from each group. It can improve precision when members of each group are similar.'
for model,language in ([(sys.argv[1],'en')] if len(sys.argv)>1 else [('llama3.1:8b','en'),('llama3.2:3b','en')]):
    rag.QUIZ_MODEL=model
    start=time.perf_counter()
    result=rag.generate_mcq_with_llm('NONE','Survey sampling','Apply','Statistical Officer',{'designation':'Statistical Officer','language':language})
    print(json.dumps({'model':model,'language':language,'seconds':round(time.perf_counter()-start,2),'question':result['question'],'answer':result['correct_answer']},ensure_ascii=True),flush=True)
