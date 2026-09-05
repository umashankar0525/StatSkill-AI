"""Persistent username accounts and extended profile fields for the imported UI."""
import base64
import hashlib
import io
import json
import re
import secrets
import sqlite3
from storage import db, encode
import frac_engine
import role_catalog

PROFILE_FIELDS = ('age','ministry','government_id','administration_type','state_name',
                  'profile_picture','location','specialization','previousRoles',
                  'statisticalDomains','projectsHandled','technicalQualifications','assessment_role_id','assessment_area')

def init():
    with db() as c:
        c.execute('''CREATE TABLE IF NOT EXISTS account_usernames(
          user_id TEXT PRIMARY KEY, username TEXT NOT NULL UNIQUE COLLATE NOCASE)''')

def username(value):
    if not isinstance(value,str) or not re.fullmatch(r'[a-zA-Z0-9_.]{3,30}',value):
        raise ValueError('Username must be 3–30 characters: letters, numbers, dots or underscores.')
    return value.lower()

def available(value):
    value=username(value)
    with db() as c:
        return not c.execute('SELECT 1 FROM account_usernames WHERE username=?',(value,)).fetchone()

def login_identifier(value):
    with db() as c:
        row=c.execute('SELECT u.email FROM account_usernames a JOIN users u ON CAST(u.id AS TEXT)=a.user_id WHERE a.username=?',(value,)).fetchone()
    return row['email'] if row else value

def public_details(user_id):
    with db() as c:
        p=c.execute('SELECT data FROM learner_profiles WHERE user_id=?',(str(user_id),)).fetchone()
        account=c.execute('SELECT username FROM account_usernames WHERE user_id=?',(str(user_id),)).fetchone()
    p=json.loads(p['data']) if p else {}
    result={k:p[k] for k in PROFILE_FIELDS if k in p}
    result.update(education=p.get('education',''),experience=p.get('experience_years',''),
                  experienceYears=p.get('experience_years',''),degree=p.get('education',''),
                  currentAssignment=p.get('responsibilities',''),projects=p.get('responsibilities',''),
                  trainingProgrammes=p.get('training_history',''))
    if account:result['username']=account['username']
    return result

def photo(value):
    if not value:return ''
    if not isinstance(value,str) or len(value)>7*1024*1024 or not re.match(r'^data:image/(png|jpeg|webp);base64,',value):
        raise ValueError('Choose a PNG, JPG or WebP photo up to 5 MB.')
    from PIL import Image, ImageOps
    try:
        raw=base64.b64decode(value.split(',',1)[1],validate=True)
        if len(raw)>5*1024*1024:raise ValueError()
        with Image.open(io.BytesIO(raw)) as image:
            if image.width*image.height>20_000_000:raise ValueError()
            image=ImageOps.exif_transpose(image).convert('RGB')
            image.thumbnail((512,512))
            output=io.BytesIO();image.save(output,format='JPEG',quality=85)
        return 'data:image/jpeg;base64,'+base64.b64encode(output.getvalue()).decode()
    except Exception as exc:
        raise ValueError('The profile photo could not be read. Choose a valid image up to 5 MB.') from exc

def text(data,key,default='',limit=5000):
    value=data.get(key,default)
    if not isinstance(value,str) or len(value)>limit:raise ValueError(f'Please check {key}.')
    return value.strip()

def profile_values(data,previous=None):
    p=dict(previous or {})
    aliases={'degree':'education','experienceYears':'experience_years','experience':'experience_years',
             'currentAssignment':'responsibilities','projects':'responsibilities','trainingProgrammes':'training_history'}
    for source,target in aliases.items():
        if source in data:p[target]=data[source]
    for key in ('designation','department','education','experience_years','responsibilities','training_history','cadre')+PROFILE_FIELDS:
        if key in data:p[key]=data[key]
    for key in ('designation','department','education','responsibilities','training_history','cadre')+tuple(k for k in PROFILE_FIELDS if k not in ('age','profile_picture')):
        p[key]=text(p,key)
    experience=p.get('experience_years','')
    if experience!='' and (isinstance(experience,bool) or not 0<=float(experience)<=65):raise ValueError('Experience must be between 0 and 65 years.')
    if p.get('age','')!='' and (isinstance(p['age'],bool) or not 18<=int(p['age'])<=100):raise ValueError('Age must be between 18 and 100.')
    if 'profile_picture' in data:p['profile_picture']=photo(data['profile_picture'])
    p=role_catalog.apply_profile(data,p)
    role=p.get('assessment_role_id') or frac_engine.map_designation_to_role(p.get('designation',''))
    if not role:raise ValueError('Please select a supported statistical designation.')
    p['role_id']=role
    p.setdefault('activities',[])
    return p

def register(data):
    handle=username(data.get('username'))
    password=data.get('password','')
    if not isinstance(password,str) or not 8<=len(password)<=256 or not re.search('[a-zA-Z]',password) or not re.search('[0-9]',password):
        raise ValueError('Password must be 8–256 characters and contain letters and numbers.')
    if password!=data.get('confirm_password'):raise ValueError('Passwords do not match.')
    name=text(data,'full_name',limit=150)
    if not name or not text(data,'government_id',limit=150):raise ValueError('Full name and government ID are required.')
    p=profile_values(data)
    if not p['ministry'] or not p['department']:raise ValueError('Please select your ministry and department.')
    salt=secrets.token_hex(16)
    hashed='pbkdf2$'+hashlib.pbkdf2_hmac('sha256',password.encode(),salt.encode(),300000).hex()
    # Internal compatibility identifier, not a claimed email address or verified ID.
    email=secrets.token_hex(16)+'@accounts.statskill.invalid'
    try:
        with db() as c:
            row=c.execute('''INSERT INTO users(name,email,password_hash,salt,role,employee_id,org_type,ministry_id,department,designation)
              VALUES(?,?,?,?,?,?,?,?,?,?)''',(name,email,hashed,salt,'learner',p['government_id'],p['administration_type'],p['ministry'],p['department'],p['designation']))
            uid=str(row.lastrowid)
            c.execute('INSERT INTO account_usernames VALUES(?,?)',(uid,handle))
            c.execute('INSERT INTO learner_profiles VALUES(?,?)',(uid,encode(p)))
    except sqlite3.IntegrityError as exc:
        raise ValueError('Username is already taken. Please choose another.') from exc
    return {'token':secrets.token_urlsafe(32),'user':{'email':email}}

def update(user,data,previous):
    p=profile_values(data,previous)
    name=text(data,'name',user['name'],150)
    if not name:raise ValueError('Full name is required.')
    with db() as c:
        c.execute('INSERT INTO learner_profiles VALUES(?,?) ON CONFLICT(user_id) DO UPDATE SET data=excluded.data',(str(user['id']),encode(p)))
        c.execute('UPDATE users SET name=?,designation=?,department=?,ministry_id=? WHERE id=?',(name,p['designation'],p['department'],p['ministry'],user['id']))
    return {'profile':p}
