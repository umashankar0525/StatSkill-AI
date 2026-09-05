"""Real local-model check against the ambiguous tool question caught in the browser."""
import json
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import rag_engine as rag
rag.QUIZ_MODEL='llama3.2:3b'
original=rag.chat
bad={'question':'What data visualization tool is commonly used for creating interactive dashboards?',
     'options':['Tableau','Power BI','D3.js','Excel'],'correct_answer':'Power BI','explanation':'Power BI creates dashboards.'}
calls=0
def generated_then_real_review(*args,**kwargs):
    global calls
    calls+=1
    return json.dumps(bad) if calls==1 else original(*args,**kwargs)
with patch.object(rag,'chat',side_effect=generated_then_real_review):
    result=rag.generate_mcq_with_llm('NONE','Data Visualization','Apply','Statistical Officer')
    assert calls>=3,'The ambiguous question passed the reviewer.'
    assert result['question']!=bad['question'],'The ambiguous question was served.'
    print('PASS: real reviewer rejected the ambiguous draft and the original model generated a replacement.')
