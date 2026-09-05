"""Persistent application state. Migrations are additive and preserve existing data."""
import os
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = os.environ.get('STATSKILL_DB', str(ROOT / 'igot_demo.db'))

@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init():
    import frac_seed
    with db() as c:
        c.execute('PRAGMA journal_mode=WAL')
        frac_seed.create_frac_tables(c.cursor())
        frac_seed.seed_frac_data(c.cursor())
        c.executescript('''
        CREATE TABLE IF NOT EXISTS app_sessions(token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL, expires REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS learner_profiles(user_id TEXT PRIMARY KEY, data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS assessments(id TEXT PRIMARY KEY, user_id TEXT NOT NULL, kind TEXT NOT NULL,
          profile TEXT NOT NULL, competencies TEXT NOT NULL, target INTEGER NOT NULL, doc_id TEXT,
          course_id TEXT, status TEXT NOT NULL DEFAULT 'active', created REAL NOT NULL, result TEXT);
        CREATE TABLE IF NOT EXISTS assessment_items(id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES assessments(id),
          position INTEGER NOT NULL, payload TEXT NOT NULL, answer INTEGER, correct INTEGER, issued REAL NOT NULL,
          answered REAL, UNIQUE(session_id, position));
        CREATE TABLE IF NOT EXISTS competency_history(id INTEGER PRIMARY KEY, user_id TEXT NOT NULL,
          competency_id TEXT NOT NULL, old_level INTEGER NOT NULL, new_level INTEGER NOT NULL,
          session_id TEXT NOT NULL, created REAL NOT NULL, UNIQUE(session_id, competency_id));
        CREATE TABLE IF NOT EXISTS question_drafts(session_id TEXT NOT NULL REFERENCES assessments(id),
          position INTEGER NOT NULL, bloom INTEGER NOT NULL, payload TEXT NOT NULL,
          PRIMARY KEY(session_id,position,bloom));
        CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, user_id TEXT NOT NULL, kind TEXT NOT NULL,
          status TEXT NOT NULL, result TEXT, error TEXT, created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS learning_courses(id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT NOT NULL,
          competency_id TEXT NOT NULL REFERENCES frac_competencies(id), doc_id TEXT NOT NULL, created_by TEXT NOT NULL,
          created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS learning_enrolments(user_id TEXT NOT NULL, course_id TEXT NOT NULL REFERENCES learning_courses(id),
          status TEXT NOT NULL, started REAL NOT NULL, completed REAL, PRIMARY KEY(user_id,course_id));
        CREATE TABLE IF NOT EXISTS objectives(id TEXT PRIMARY KEY, user_id TEXT NOT NULL, title TEXT NOT NULL,
          due_date TEXT NOT NULL, created_by TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'active');
        CREATE TABLE IF NOT EXISTS key_results(id TEXT PRIMARY KEY, objective_id TEXT NOT NULL REFERENCES objectives(id),
          title TEXT NOT NULL, metric TEXT NOT NULL, competency_id TEXT, baseline REAL NOT NULL,
          target REAL NOT NULL, current REAL NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS okr_checkins(id INTEGER PRIMARY KEY, key_result_id TEXT NOT NULL REFERENCES key_results(id),
          value REAL NOT NULL, note TEXT NOT NULL, user_id TEXT NOT NULL, created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS support_requests(id TEXT PRIMARY KEY, contact TEXT, details TEXT, created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS role_activities(id TEXT PRIMARY KEY, title TEXT NOT NULL, competency_id TEXT NOT NULL,
          required_level INTEGER NOT NULL);
        CREATE INDEX IF NOT EXISTS assessment_owner ON assessments(user_id, status);
        CREATE INDEX IF NOT EXISTS history_owner ON competency_history(user_id, created);
        ''')
        for row in c.execute('SELECT id,name FROM frac_competencies').fetchall():
            c.execute('INSERT OR IGNORE INTO role_activities VALUES(?,?,?,?)',
                      ('A_' + row['id'], 'Work involving ' + row['name'], row['id'], 3))
        activities={
            'C_SURVEY':'Design questionnaires and field survey instruments',
            'C_SAMPLING':'Build sampling frames and calculate sample weights',
            'C_NAT_ACC':'Compile national accounts and gross value added estimates',
            'C_PRICE':'Compile and validate consumer or wholesale price indices',
            'C_PYTHON':'Clean and analyse official datasets with Python',
            'C_AI_ML':'Build and evaluate predictive or anomaly detection models',
            'C_DATAVIZ':'Publish dashboards and communicate statistical findings',
            'C_R':'Perform statistical analysis and modelling in R',
            'C_SQL':'Maintain and query statistical databases',
            'C_GIS':'Map survey coverage and analyse geographic data',
            'C_CYBER':'Protect statistical systems and manage security incidents',
            'C_DPDP':'Manage personal-data collection, access and disclosure',
            'C_SDG':'Compile and monitor SDG indicators',
            'C_ETHICS':'Review statistical outputs for impartiality and confidentiality',
            'C_LEADERSHIP':'Set team priorities and supervise statistical programmes',
            'C_CAPACITY':'Plan and evaluate workforce training programmes',
            'C_PEDAGOGY':'Design lessons and assess learner performance'}
        for cid,title in activities.items():
            c.execute("UPDATE role_activities SET title=? WHERE id=? AND title LIKE 'Work involving %'",(title,'A_'+cid))
        # A server restart must never leave an in-progress job polling forever.
        c.execute("UPDATE jobs SET status='failed', error='Server restarted. Retry this operation.' WHERE status IN ('queued','running')")

def encode(value):
    return json.dumps(value, ensure_ascii=False)
