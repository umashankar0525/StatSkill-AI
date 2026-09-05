"""Isolated browser-test server. Never seeds test users into the real database."""
import os
import sys
import tempfile
from pathlib import Path
temp=tempfile.TemporaryDirectory()
os.environ['STATSKILL_DB']=str(Path(temp.name)/'preview.db')
os.environ['STATSKILL_USERS']=str(Path(temp.name)/'users.json')
os.environ['STATSKILL_UPLOADS']=str(Path(temp.name)/'uploads')
os.environ['STATSKILL_PORT']='8011'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
server.STATIC_DIR=os.environ.get('STATSKILL_PREVIEW_STATIC',server.STATIC_DIR)
from storage import db
with db() as c:
    hashed,salt=server.hash_password('BrowserTest123')
    c.execute('INSERT INTO users(name,email,password_hash,salt,role,designation,department) VALUES(?,?,?,?,?,?,?)',
              ('Browser Test Officer','browser@test.invalid',hashed,salt,'admin','Statistical Officer','Survey division'))
server.run_server()
