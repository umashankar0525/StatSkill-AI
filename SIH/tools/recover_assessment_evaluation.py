"""Finish an answered assessment from saved evidence, without starting the website."""
import argparse,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import server,quiz_service
from storage import db
parser=argparse.ArgumentParser();parser.add_argument('session_id');args=parser.parse_args()
with db() as c:
    row=c.execute('SELECT user_id FROM assessments WHERE id=?',(args.session_id,)).fetchone()
    if not row:raise ValueError('Assessment not found.')
    cached=c.execute('SELECT count(*) FROM assessment_evaluations WHERE session_id=?',(args.session_id,)).fetchone()[0]
started=time.monotonic()
result=quiz_service.submit({'id':row['user_id']},{'session_id':args.session_id})['result']
summary={'session_id':args.session_id,'status':'complete','previously_cached_topics':cached,'seconds':round(time.monotonic()-started,2),'topics':[{k:r.get(k) for k in ('competency_name','new_level','required_level','correct_count','evidence_count')} for r in result['changes']]}
(ROOT/'tmp/evaluation-recovery.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2),flush=True)
