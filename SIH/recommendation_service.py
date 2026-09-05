"""Llama ranks an attributable iGOT catalogue; it cannot invent course URLs."""
import hashlib,json,time
from pathlib import Path
from storage import db,encode
import model_tasks
from role_catalog import CATALOG

SEED=json.loads((Path(__file__).parent/'data/igot_courses.json').read_text(encoding='utf-8'))
def init():
    with db() as c:
        c.executescript('''CREATE TABLE IF NOT EXISTS igot_catalog(id TEXT PRIMARY KEY,payload TEXT);
        CREATE TABLE IF NOT EXISTS igot_saved(user_id TEXT,course_id TEXT REFERENCES igot_catalog(id),created REAL,PRIMARY KEY(user_id,course_id));
        CREATE TABLE IF NOT EXISTS learner_recommendations(user_id TEXT PRIMARY KEY,fingerprint TEXT,payload TEXT,created REAL);''')
        for course in SEED['courses']:
            course={**course,'url':'https://portal.igotkarmayogi.gov.in/app/toc/'+course['id']+'/overview',
                    'source_url':SEED['source_url'],'source_title':SEED['source_title'],'verified_on':SEED['verified_on']}
            c.execute('INSERT OR IGNORE INTO igot_catalog VALUES(?,?)',(course['id'],encode(course)))

def catalog():
    with db() as c:return [json.loads(r[0]) for r in c.execute('SELECT payload FROM igot_catalog ORDER BY id')]

def fingerprint(p,gaps):
    return hashlib.sha256(encode(dict(role=p['role_id'],department=p.get('department'),language=p.get('language','en'),gaps=gaps,catalog=catalog(),model=model_tasks.RECOMMENDATION_MODEL)).encode()).hexdigest()

def saved_result(user,p,gaps):
    with db() as c:row=c.execute('SELECT payload FROM learner_recommendations WHERE user_id=? AND fingerprint=?',(str(user['id']),fingerprint(p,gaps))).fetchone()
    return json.loads(row[0]) if row else None

def recommend(user,p,gaps):
    cached=saved_result(user,p,gaps)
    if cached:return cached
    needed={g['competency_id']:g for g in gaps if g['gap'] is not None and g['gap']>0}
    candidates=[x for x in catalog() if set(x['competencies'])&needed.keys()]
    uncovered=[g['competency_name'] for cid,g in needed.items() if not any(cid in c['competencies'] for c in candidates)]
    ranked=[];model=None
    if candidates:
        prompt={'role':p.get('designation'),'department':p.get('department'),'gaps':list(needed.values()),
                'language':p.get('language','en'),'courses':[{k:c[k] for k in ('id','title','provider','competencies')} for c in candidates]}
        system='''Recommend up to five suitable iGOT courses from the supplied candidates for the learner's assessed gaps.
Rank the largest relevant gaps first and consider the job role. Return only existing course IDs and
the matching competency_id from that course's competencies. Explain relevance in the requested language
without claiming a guaranteed proficiency gain or inventing syllabus, level, duration, rating or availability.
Return {"recommendations":[{"course_id":"...","competency_id":"...","reason":"one short sentence"}]}.
Do not return URLs. Course links are attached by the server from the verified catalogue.'''
        result,model=model_tasks.json_task('recommendation',system,prompt,tokens=900)
        ranked=result.get('recommendations')
        if not isinstance(ranked,list) or not ranked or len(ranked)>5:raise ValueError('The recommendation model returned an invalid course list.')
        indexed={c['id']:c for c in candidates};seen=set()
        for r in ranked:
            if not isinstance(r,dict) or r.get('course_id') not in indexed or r['course_id'] in seen:raise ValueError('The recommendation model returned an unknown or repeated course.')
            if r.get('competency_id') not in indexed[r['course_id']]['competencies'] or r['competency_id'] not in needed:raise ValueError('The recommendation did not match an assessed gap.')
            if not isinstance(r.get('reason'),str) or not 5<=len(r['reason'])<=700:raise ValueError('The recommendation explanation is invalid.')
            seen.add(r['course_id'])
        ranked=[{k:r[k] for k in ('course_id','competency_id','reason')} for r in ranked]
    result={'recommendations':ranked,'uncovered_skills':uncovered,'model':model,'catalogue_verified_on':SEED['verified_on']}
    with db() as c:c.execute('INSERT OR REPLACE INTO learner_recommendations VALUES(?,?,?,?)',(str(user['id']),fingerprint(p,gaps),encode(result),time.time()))
    return result

def courses_for(user,p,gaps):
    result=saved_result(user,p,gaps)
    ranked={r['course_id']:(i,r) for i,r in enumerate((result or {}).get('recommendations',[]))}
    with db() as c:saved={r[0] for r in c.execute('SELECT course_id FROM igot_saved WHERE user_id=?',(str(user['id']),))}
    courses=[]
    for course in catalog():
        recommendation=ranked.get(course['id'])
        cid=recommendation[1]['competency_id'] if recommendation else course['competencies'][0]
        gap=next((g for g in gaps if g['competency_id']==cid),None)
        courses.append(dict(course,id='igot:'+course['id'],external=True,doc_id=None,competency_id=cid,
          competency=gap['competency_name'] if gap else next((x['name'] for x in CATALOG['competencies'] if x['id']==cid),'Professional skills'),description='iGOT Karmayogi · '+course['provider'],
          enrolment_status='saved' if course['id'] in saved else None,priority_score=100-recommendation[0] if recommendation else -1,
          recommended=bool(recommendation),reason=recommendation[1]['reason'] if recommendation else 'Published iGOT course. Complete your assessment for personalised recommendations.'))
    return sorted(courses,key=lambda c:c['priority_score'],reverse=True)

def save(user,course_id):
    cid=course_id.removeprefix('igot:') if isinstance(course_id,str) else ''
    with db() as c:
        if not c.execute('SELECT 1 FROM igot_catalog WHERE id=?',(cid,)).fetchone():raise ValueError('Course not found in the iGOT catalogue.')
        c.execute('INSERT OR IGNORE INTO igot_saved VALUES(?,?,?)',(str(user['id']),cid,time.time()))
    return {}
