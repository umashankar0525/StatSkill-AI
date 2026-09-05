"""Objectives with evidence-linked key results and auditable manual check-ins."""
import secrets
import time
from datetime import date
from storage import db
from frac_engine import get_user_competency_profile

def require(condition,message):
    if not condition:
        raise ValueError(message)

def list_objectives(user_id):
    current=get_user_competency_profile(str(user_id))
    with db() as c:
        count=c.execute("SELECT count(*) FROM learning_enrolments WHERE user_id=? AND status='completed'",(str(user_id),)).fetchone()[0]
        objectives=[dict(r) for r in c.execute('SELECT * FROM objectives WHERE user_id=? ORDER BY due_date',(str(user_id),))]
        for objective in objectives:
            results=[dict(r) for r in c.execute('SELECT * FROM key_results WHERE objective_id=?',(objective['id'],))]
            for kr in results:
                kr['current']=current.get(kr['competency_id'],0) if kr['metric']=='competency' else count if kr['metric']=='courses' else kr['current']
                kr['progress']=round(max(0,min(1,(kr['current']-kr['baseline'])/(kr['target']-kr['baseline'])))*100,1)
                kr['checkins']=[dict(r) for r in c.execute('SELECT value,note,created FROM okr_checkins WHERE key_result_id=? ORDER BY id DESC',(kr['id'],))]
            objective['key_results']=results
            objective['progress']=round(sum(r['progress'] for r in results)/len(results),1) if results else 0
    return objectives

def create(user,data):
    user_id=str(user['id'])
    owner=str(data.get('user_id') or user_id)
    require(owner==user_id or user['role'] in ('admin','superadmin'),'Only administrators can assign objectives to another officer.')
    title=str(data.get('title','')).strip()
    require(3<=len(title)<=250,'Objective title must be 3–250 characters.')
    due=date.fromisoformat(data.get('due_date',''))
    require(due>=date.today(),'Due date must be today or later.')
    results=data.get('key_results',[])
    require(isinstance(results,list) and 1<=len(results)<=8,'Add 1–8 key results.')
    oid=secrets.token_hex(16)
    current=get_user_competency_profile(owner)
    with db() as c:
        require(c.execute('SELECT 1 FROM users WHERE id=?',(owner,)).fetchone(),'Objective owner not found.')
        c.execute('INSERT INTO objectives(id,user_id,title,due_date,created_by) VALUES(?,?,?,?,?)',(oid,owner,title,due.isoformat(),user_id))
        for kr in results:
            metric=kr.get('metric')
            require(metric in ('competency','courses','manual'),'Invalid key-result metric.')
            target=float(kr.get('target',0))
            cid=kr.get('competency_id') if metric=='competency' else None
            if metric=='competency':
                require(c.execute('SELECT 1 FROM frac_competencies WHERE id=?',(cid,)).fetchone(),'Choose a competency.')
                baseline=current.get(cid,0)
                require(target.is_integer() and 1<=target<=6,'Competency target must be a level from 1 to 6.')
            elif metric=='courses':
                baseline=c.execute("SELECT count(*) FROM learning_enrolments WHERE user_id=? AND status='completed'",(owner,)).fetchone()[0]
                require(target.is_integer(),'Course target must be a whole number.')
            else:
                baseline=float(kr.get('baseline',0))
            require(0<=baseline<target<=1000000,'Target must exceed the baseline and be no more than 1,000,000.')
            label=str(kr.get('title','')).strip()
            require(3<=len(label)<=250,'Key-result title must be 3–250 characters.')
            c.execute('INSERT INTO key_results VALUES(?,?,?,?,?,?,?,?)',(secrets.token_hex(16),oid,label,metric,cid,baseline,target,baseline))
    return {'objective_id':oid}

def checkin(user,data):
    user_id=str(user['id'])
    with db() as c:
        kr=c.execute('SELECT k.*,o.user_id FROM key_results k JOIN objectives o ON o.id=k.objective_id WHERE k.id=?',(data.get('key_result_id'),)).fetchone()
        require(kr and (kr['user_id']==user_id or user['role'] in ('admin','superadmin')),'Key result not found.')
        require(kr['metric']=='manual','This result updates automatically from assessment evidence.')
        value=float(data.get('value',0))
        note=str(data.get('note','')).strip()
        require(0<=value<=1000000 and 3<=len(note)<=2000,'Provide a non-negative value and a check-in note.')
        c.execute('UPDATE key_results SET current=? WHERE id=?',(value,kr['id']))
        c.execute('INSERT INTO okr_checkins(key_result_id,value,note,user_id,created) VALUES(?,?,?,?,?)',(kr['id'],value,note,user_id,time.time()))
    return {}

def set_status(user,data):
    require(data.get('status') in ('active','archived'),'Invalid objective status.')
    with db() as c:
        row=c.execute('SELECT * FROM objectives WHERE id=?',(data.get('objective_id'),)).fetchone()
        require(row and (row['user_id']==str(user['id']) or user['role'] in ('admin','superadmin')),'Objective not found.')
        c.execute('UPDATE objectives SET status=? WHERE id=?',(data['status'],row['id']))
    return {}
