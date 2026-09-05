"""Resumable adaptive assessments with server-owned answer keys and evidence."""
import json
import secrets
import threading
import weakref
import time
from storage import db, encode
import frac_engine as frac
import adaptive_quiz_engine as cat
import rag_engine as rag
import quiz_buffer
import assessment_evaluator
import role_catalog
import topic_evidence

_locks = weakref.WeakValueDictionary()
_guard = threading.Lock()

def lock(sid):
    with _guard:
        return _locks.setdefault(sid, threading.RLock())

def require(condition, message):
    if not condition:
        raise ValueError(message)

def session_row(sid, user):
    with db() as c:
        row = c.execute('SELECT * FROM assessments WHERE id=? AND user_id=?',(sid,str(user['id']))).fetchone()
    require(row is not None,'Assessment not found.')
    return dict(row)

def view(sid,user):
    s = session_row(sid,user)
    with db() as c:
        items = c.execute('SELECT * FROM assessment_items WHERE session_id=? ORDER BY position',(sid,)).fetchall()
    pending = next((q for q in items if q['answered'] is None),None)
    question = None
    if pending:
        q = json.loads(pending['payload'])
        question = {k:v for k,v in q.items() if k not in ('correct_answer','explanation','source_quote')}
        question.update(id=pending['id'],position=pending['position'],deadline=pending['issued']+180)
    return dict(id=sid,kind=s['kind'],target=s['target'],answered=sum(q['answered'] is not None for q in items),
                status=s['status'],question=question,preparation=quiz_buffer.status(sid),evaluation=assessment_evaluator.progress(sid),result=json.loads(s['result']) if s['result'] else None)

def question_plan(sid,user,preparing=False,position=None):
    s=session_row(sid,user)
    with db() as c:
        rows=[dict(r) for r in c.execute('SELECT payload,correct,answered FROM assessment_items WHERE session_id=? ORDER BY position',(sid,))]
    pending=next((r for r in rows if r['answered'] is None),None)
    if position is None:
        if preparing:
            if not pending or s['status']!='active':
                return None
        elif pending:
            return None
        position=len(rows)+1
    if position>s['target'] or s['status']!='active':
        return None
    comps=json.loads(s['competencies'])
    schedule=[comp for i,comp in enumerate(comps) for _ in range(s['target']//len(comps)+(i<s['target']%len(comps)))]
    comp=schedule[position-1]
    previous=[json.loads(r['payload']) for r in rows]
    # One-answer delay: Q(n) uses results through Q(n-2). Its difficulty is already
    # determined while Q(n-1) is on screen, so it can be prepared without guessing.
    matching=[(q,r['correct']) for q,r in zip(previous[:-1],rows[:-1]) if q['competency_id']==comp['id']]
    bloom=cat.get_next_blooms_level(matching[-1][0]['bloom_level'],bool(matching[-1][1])) if matching else quiz_buffer.start_depth(comp,json.loads(s['profile']))
    return dict(sid=sid,session=s,position=position,comp=comp,bloom=bloom,previous=previous)

def prepare_next(sid,user):
    # A draft stays server-side and has no timer until it is actually issued.
    quiz_buffer.ensure(sid,user)
    return {}

def next_is_ready(sid,user):
    current=view(sid,user)
    if current['question'] or current['status']!='active' or current['answered']>=current['target']:
        return True
    plan=question_plan(sid,user)
    if not plan:return True
    with db() as c:
        return c.execute('SELECT 1 FROM question_drafts WHERE session_id=? AND position=? AND bloom=?',
                         (sid,plan['position'],plan['bloom'])).fetchone() is not None

def next_question(sid,user):
    with lock(sid):
        current=view(sid,user)
        if current['question'] or current['status']!='active' or current['answered']>=current['target']:
            return current
        if not next_is_ready(sid,user):quiz_buffer.ensure(sid,user)
        plan=question_plan(sid,user)
        q=quiz_buffer.select(plan)
        with db() as c:
            c.execute('INSERT INTO assessment_items(id,session_id,position,payload,issued) VALUES(?,?,?,?,?)',
                      (secrets.token_hex(16),sid,plan['position'],encode(q),time.time()))
            c.execute('DELETE FROM question_drafts WHERE session_id=? AND position<=?',(sid,plan['position']))
        return view(sid,user)

def start(user,body,p):
    language=body.get('language',p.get('language','en'))
    require(language in ('en','hi'),'Choose English or Hindi.')
    p={**p,'language':language}
    kind = body.get('kind','initial')
    require(kind in ('initial','course'),'Invalid assessment type.')
    doc_id = course_id = None
    if kind == 'initial':
        require(p['role_id'] in role_catalog.ROLES,'Choose your work area and designation in My profile before starting the assessment.')
        comps = frac.get_required_competencies(p['role_id'],p['activities'])
        require(comps,'Select your job role in your profile before starting.')
        target = max(30,min(50,len(comps)*4))
    else:
        course_id = body.get('course_id')
        with db() as c:
            row = c.execute('SELECT * FROM learning_courses WHERE id=?',(course_id,)).fetchone()
            enrol = c.execute('SELECT * FROM learning_enrolments WHERE user_id=? AND course_id=?',(str(user['id']),course_id)).fetchone()
            require(row and enrol,'Enrol in this course before starting its assessment.')
            doc_id = row['doc_id']
            comp = c.execute('SELECT * FROM frac_competencies WHERE id=?',(row['competency_id'],)).fetchone()
        comps = [dict(comp,required_level=3)]
        target = 10
    with lock('start-'+str(user['id'])):
        with db() as c:
            row = c.execute("SELECT id FROM assessments WHERE user_id=? AND kind=? AND status='active' AND course_id IS ? AND json_extract(profile,'$.role_id')=? AND json_extract(profile,'$.language')=? ORDER BY created DESC",(str(user['id']),kind,course_id,p['role_id'],language)).fetchone()
            if row:
                sid=row['id']
            else:
                sid=secrets.token_hex(16)
                c.execute('INSERT INTO assessments(id,user_id,kind,profile,competencies,target,doc_id,course_id,created) VALUES(?,?,?,?,?,?,?,?,?)',
                          (sid,str(user['id']),kind,encode(p),encode(comps),target,doc_id,course_id,time.time()))
    return {'session':view(sid,user)}

def answer(user,body):
    sid,qid,choice = body.get('session_id'),body.get('question_id'),body.get('answer')
    require(choice is None or type(choice) is int and 0<=choice<=3,'Choose an option from 0 to 3, or skip.')
    with lock(sid):
        s=session_row(sid,user)
        require(s['status']=='active','This assessment has already been submitted.')
        with db() as c:
            row=c.execute('SELECT * FROM assessment_items WHERE id=? AND session_id=?',(qid,sid)).fetchone()
            require(row is not None,'Question not found.')
            if row['answered'] is not None:
                require(row['answer']==choice or time.time()>row['issued']+180,'This answer has already been saved.')
            else:
                if time.time()>row['issued']+180:
                    choice=None
                q=json.loads(row['payload'])
                correct=choice is not None and q['options'][choice]==q['correct_answer']
                c.execute('UPDATE assessment_items SET answer=?,correct=?,answered=? WHERE id=?',(choice,int(correct),time.time(),qid))
        if next_is_ready(sid,user):
            return {'session':next_question(sid,user)}
    return {'session':view(sid,user)}

def submit(user,body):
    sid=body.get('session_id')
    with lock(sid):
        s=session_row(sid,user)
        if s['status']=='complete':
            return {'result':json.loads(s['result'])}
        require(view(sid,user)['answered']==s['target'],'Answer or skip every question before submitting.')
        with db() as c:
            rows=c.execute('SELECT * FROM assessment_items WHERE session_id=? ORDER BY position',(sid,)).fetchall()
        grouped,review={},[]
        for row in rows:
            q=json.loads(row['payload'])
            grouped.setdefault(q['competency_id'],[]).append(dict(row))
            review.append(dict(q,answer=row['answer'],correct=bool(row['correct'])))
        old=frac.get_user_competency_profile(str(user['id']))
        requirements={c['id']:c for c in json.loads(s['competencies'])}
        progress=dict(status='evaluating',total=len(grouped),completed=0,topics=[],error=None)
        assessment_evaluator.save_progress(sid,progress)
        changes=[]
        for k,items in grouped.items():
            try:evaluation=assessment_evaluator.evaluate(sid,k,items)
            except Exception as exc:
                progress.update(status='failed',error=str(exc),current_topic=requirements.get(k,{}).get('name',k))
                assessment_evaluator.save_progress(sid,progress)
                raise
            change=dict(competency_id=k,competency_name=requirements.get(k,{}).get('name',k),required_level=requirements.get(k,{}).get('required_level'),old_level=old.get(k),new_level=evaluation['current_level'],evidence_count=len(items),correct_count=sum(bool(r['correct']) for r in items),evaluation=evaluation)
            changes.append(change)
            progress['topics'].append({key:change[key] for key in ('competency_id','competency_name','required_level','new_level','evidence_count','correct_count')})
            progress['completed']=len(changes)
            assessment_evaluator.save_progress(sid,progress)
        correct=sum(r['correct'] for r in rows)
        result=dict(session_id=sid,score_percent=round(correct/len(rows)*100),correct_count=correct,total=len(rows),changes=changes,review=review,
                    levels=role_catalog.LEVELS,
                    scoring_note='Knowledge estimate from saved assessment answers using L0 plus the supplied L1-L6 criteria. Workplace performance requires separate evidence.',
                    time_minutes=round((time.time()-s['created'])/60,1))
        with db() as c:
            for change in changes:
                topic_evidence.save(c,user['id'],sid,change['competency_id'],grouped[change['competency_id']],change['evaluation'])
                if change['new_level'] is None:continue
                c.execute('INSERT INTO competency_profiles VALUES(?,?,?) ON CONFLICT(user_id,competency_id) DO UPDATE SET current_level=excluded.current_level',
                          (str(user['id']),change['competency_id'],change['new_level']))
                c.execute('INSERT INTO competency_history(user_id,competency_id,old_level,new_level,session_id,created) VALUES(?,?,?,?,?,?)',
                          (str(user['id']),change['competency_id'],change['old_level'] or 0,change['new_level'],sid,time.time()))
            c.execute("UPDATE assessments SET status='complete',result=? WHERE id=?",(encode(result),sid))
            c.execute('INSERT OR REPLACE INTO assessment_evaluation_progress VALUES(?,?)',(sid,encode({**progress,'status':'complete'})))
            if s['course_id'] and result['score_percent']>=60:
                c.execute("UPDATE learning_enrolments SET status='completed',completed=? WHERE user_id=? AND course_id=?",(time.time(),str(user['id']),s['course_id']))
        return {'result':result}
