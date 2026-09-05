"""Consistent SQLite backup before restarting the updated application."""
from pathlib import Path
import sqlite3,shutil,json,time
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT.parents[1]/'.soul-integration'/('database-before-restart-'+time.strftime('%Y%m%d-%H%M%S'))
folder.mkdir(parents=True,exist_ok=False)
source=sqlite3.connect(ROOT/'igot_demo.db')
target=sqlite3.connect(folder/'igot_demo.db')
source.backup(target)
assert target.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
counts={table:source.execute('SELECT count(*) FROM '+table).fetchone()[0] for table in ('users','assessments','competency_history','documents')}
source.close();target.close()
if (ROOT/'users.json').exists():shutil.copy2(ROOT/'users.json',folder/'users.json')
(folder/'counts.json').write_text(json.dumps(counts),encoding='utf-8')
print(json.dumps(dict(backup=str(folder),counts=counts)))
