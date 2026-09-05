"""Transparent provisional FRAC mapping; scores require saved assessment evidence."""
from storage import db

PROVENANCE = 'Current role requirements follow the supplied PDFs and four selected ministries. Legacy mappings are retained for historical records. These project records are not independently certified official policy.'

def map_designation_to_role(designation):
    d = (designation or '').lower()
    for text, role in [('capacity', 'R_CB_DIR'), ('district statistical', 'R_DSO'),
                       ('data quality', 'R_DQA'), ('faculty', 'R_FACULTY'), ('trainer', 'R_FACULTY'),
                       ('senior statistical', 'R_SSO'), ('joint director', 'R_JD'),
                       ('deputy director', 'R_DD'), ('assistant director', 'R_DD'),
                       ('director', 'R_DIR'), ('statistical officer', 'R_SO'),
                       ('investigator', 'R_SO'), ('field officer', 'R_SO')]:
        if text in d:
            return role
    return None

def get_required_competencies(role_id, activities=()):
    if role_id and role_id.startswith('PDF_'):activities=()
    with db() as c:
        rows = c.execute('''SELECT c.id,c.name,c.type,m.required_level FROM frac_role_competency_map m
          JOIN frac_competencies c ON c.id=m.competency_id WHERE m.role_id=? ORDER BY c.id''', (role_id,)).fetchall()
        found = {r['id']: dict(r, mapping_reason='Role requirement') for r in rows}
        for aid in activities:
            a = c.execute('''SELECT c.id,c.name,c.type,a.required_level,a.title FROM role_activities a
              JOIN frac_competencies c ON c.id=a.competency_id WHERE a.id=?''', (aid,)).fetchone()
            if a:
                level = max(a['required_level'], found.get(a['id'], {}).get('required_level', 0))
                found[a['id']] = dict(id=a['id'], name=a['name'], type=a['type'], required_level=level,
                                      mapping_reason='Selected activity: ' + a['title'])
    return list(found.values())

def get_user_competency_profile(user_id):
    with db() as c:
        return {r['competency_id']: r['current_level'] for r in c.execute('''
          SELECT p.* FROM competency_profiles p WHERE p.user_id=? AND EXISTS
          (SELECT 1 FROM competency_history h WHERE h.user_id=p.user_id AND h.competency_id=p.competency_id)''', (str(user_id),))}

def compute_skill_gap(user_id, role_id, activities=()):
    current = get_user_competency_profile(user_id)
    return [dict(competency_id=r['id'], competency_name=r['name'], type=r['type'], required_level=r['required_level'],
                 current_level=current.get(r['id']), gap=max(0,r['required_level']-current[r['id']]) if r['id'] in current else None,
                 mapping_reason=r['mapping_reason']) for r in get_required_competencies(role_id, activities)]

def overall_score(gaps):
    assessed = [g for g in gaps if g['current_level'] is not None]
    if not assessed:
        return None
    return round(100 * sum(min(g['current_level'],g['required_level']) for g in assessed) / sum(g['required_level'] for g in assessed))
