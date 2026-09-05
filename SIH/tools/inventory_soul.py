"""Inventory the pinned upstream checkout without exporting account/config values."""
import ast,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT.parents[1]/'.soul-integration/complete/soul-f99c5e454cd1fd60bcdf9ca84a0ba78c222fe378'
rows=[]
for p in sorted(SOURCE.rglob('*')):
    if not p.is_file():continue
    raw=p.read_bytes();relative=p.relative_to(SOURCE).as_posix()
    row=dict(path=relative,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    if p.suffix=='.py':
        tree=ast.parse(raw.decode('utf-8-sig'))
        row['functions']=[n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
        row['imports']=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]+[a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names]
        row['category']='ingestion utility' if p.name.startswith('ingest_') else 'model pipeline' if p.name in ('groq_client.py','rag_quiz_client.py','pdf_ingestor.py') else 'server or mapping utility'
    elif p.suffix in ('.js','.html','.css','.md','.sql'):
        content=raw.decode('utf-8-sig',errors='replace')
        row['functions']=re.findall(r'\bfunction\s+(\w+)\s*\(',content)
        row['category']='demo server/database bootstrap' if relative.startswith('igot-demo 2/') else 'UI' if relative.startswith('static/') else 'documentation'
        row['demo_markers']=sorted(set(re.findall(r'\b(?:MOCK_DATA|mockData|setTimeout|localStorage|Math\.random)\b',content)))
    else:row['category']='metadata or binary; no executable integration'
    rows.append(row)
(ROOT/'data/soul_source_inventory.json').write_text(json.dumps(dict(repository='https://github.com/sivasankar-11/soul',commit='f99c5e454cd1fd60bcdf9ca84a0ba78c222fe378',files=rows),indent=2),encoding='utf-8')
print(json.dumps(dict(files=len(rows),python=sum(r['path'].endswith('.py') for r in rows),javascript=sum(r['path'].endswith('.js') for r in rows))))
