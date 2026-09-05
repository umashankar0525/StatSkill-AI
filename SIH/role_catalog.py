"""Role requirements transcribed from supplied PDFs, kept separate from inference."""
import json
from pathlib import Path
from storage import db

CATALOG=json.loads((Path(__file__).parent/'data/role_framework.json').read_text(encoding='utf-8'))
ROLES={r['id']:{**r,'area_id':a['id'],'area':a['name'],'ministry':a['ministry']} for a in CATALOG['areas'] for r in a['roles']}
LEVELS=CATALOG['levels']

def init():
    with db() as c:
        for comp in CATALOG['competencies']:
            c.execute('INSERT INTO frac_competencies VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,type=excluded.type,description=excluded.description',(comp['id'],comp['name'],comp['type'],comp['name']))
        for rid,role in ROLES.items():
            c.execute('INSERT OR IGNORE INTO frac_roles VALUES(?,?,?,?)',(rid,role['title']+' — '+role['area'],'Supplied role matrix',role['duties']))
            for cid,level in role['requirements'].items():
                c.execute('INSERT OR IGNORE INTO frac_role_competency_map VALUES(?,?,?)',(rid,cid,level))

def public_catalog():
    return dict(version=CATALOG['version'],ministries=CATALOG['ministries'],areas=[dict(id=a['id'],name=a['name'],ministry=a['ministry'],ministry_id=a['ministry_id'],roles=[dict(id=r['id'],title=r['title'],grade=r['grade']) for r in a['roles']]) for a in CATALOG['areas']],levels=LEVELS)

def apply_profile(data,p):
    rid=data.get('assessment_role_id',p.get('assessment_role_id'))
    if not rid:raise ValueError('Choose your ministry, work area and designation in your profile.')
    role=ROLES.get(rid)
    if not role:raise ValueError('Select a role from the supplied work-area list.')
    area=data.get('assessment_area',p.get('assessment_area',role['area_id']))
    if area!=role['area_id']:raise ValueError('The selected role does not belong to this work area.')
    if p.get('ministry')!=role['ministry']:raise ValueError('Choose a work area belonging to your selected ministry.')
    if p.get('administration_type') not in ('',None,'Central Government','central'):raise ValueError('Only the four selected central ministries are currently supported.')
    if p.get('department') and p['department']!=role['area']:raise ValueError('Choose a department matching your selected work area.')
    if data.get('designation') and data['designation']!=role['title']:
        raise ValueError('Choose the designation for your selected work area.')
    p.update(role_id=rid,assessment_role_id=rid,assessment_area=area,department=role['area'],administration_type='Central Government',state_name='',designation=role['title'],role_duties=role['duties'],framework_version=CATALOG['version'],role_grade=role['grade'],activities=[])
    return p
