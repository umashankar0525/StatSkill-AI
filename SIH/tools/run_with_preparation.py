"""Run the local app while preparing an existing assessment without starting its timer."""
import argparse,json,sys,threading,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import server,quiz_buffer,generation_runtime
from storage import db

def prepare(sid):
    started=time.monotonic()
    try:
        with db() as c:row=c.execute("SELECT user_id FROM assessments WHERE id=? AND status='active'",(sid,)).fetchone()
        if not row:raise ValueError('Active assessment not found.')
        quiz_buffer.ensure(sid,{'id':row['user_id']})
        print(json.dumps({'preparation':'ready','session_id':sid,'seconds':round(time.monotonic()-started,2),'progress':quiz_buffer.status(sid)}),flush=True)
    except Exception as exc:
        generation_runtime.event('prewarm_failed',error=str(exc))
        print(json.dumps({'preparation':'failed','session_id':sid,'error':str(exc)}),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--session',required=True);args=parser.parse_args()
    threading.Thread(target=prepare,args=(args.session,),daemon=True).start()
    server.run_server()
