"""Idempotently index the supplied original PDFs. Run while the app is stopped."""
import argparse,hashlib,json,shutil,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))

def run(folder):
    import server,rag_engine,role_catalog,live_api
    from storage import db
    manifest=json.loads((ROOT/'data/study_material_manifest.json').read_text(encoding='utf-8'))
    report={'materials':[], 'excluded_framework':manifest['excluded_framework'], 'coverage_notes':manifest.get('coverage_notes',{})}
    report_path=ROOT/'tmp/study-material-import.json';report_path.parent.mkdir(exist_ok=True)
    for item in manifest['materials']:
        start=time.monotonic();source=folder/item['filename'];doc_id='pdf-'+item['sha256'][:24]
        result={'filename':item['filename'],'doc_id':doc_id,'pages':item['pages'],'topics':item['competencies']}
        print(json.dumps({'indexing':item['filename'] }),flush=True)
        try:
            digest=hashlib.sha256(source.read_bytes()).hexdigest()
            if digest!=item['sha256']:raise ValueError('Source checksum differs from the inspected PDF.')
            target=live_api.UPLOADS/(doc_id+'.pdf');target.parent.mkdir(parents=True,exist_ok=True)
            if not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest()!=digest:shutil.copy2(source,target)
            with db() as c:
                ready=c.execute("SELECT 1 FROM documents WHERE id=? AND status='ready'",(doc_id,)).fetchone()
                c.execute('INSERT OR IGNORE INTO documents(id,title,filename,uploaded_by,status,storage_path) VALUES(?,?,?,?,?,?)',(doc_id,item['title'],item['filename'],'source-import','pending',str(target)))
            if not ready:rag_engine.process_and_store_document(doc_id,item['title'],item['filename'],'source-import',str(target))
            with db() as c:
                c.execute('INSERT OR REPLACE INTO document_provenance VALUES(?,?,?,?)',(doc_id,source.as_uri(),digest,'user supplied original PDF'))
                for topic in item['competencies']:c.execute('INSERT OR IGNORE INTO document_topics VALUES(?,?)',(doc_id,topic))
                roles=[rid for rid,r in role_catalog.ROLES.items() if set(item['competencies'])&r['requirements'].keys()]
                for rid in roles:c.execute('INSERT OR IGNORE INTO document_assignments VALUES(?,?)',(doc_id,rid))
                result.update(status='ready',chunks=c.execute('SELECT count(*) FROM doc_chunks WHERE doc_id=?',(doc_id,)).fetchone()[0],assigned_roles=len(roles),reused=bool(ready))
        except Exception as exc:
            result.update(status='failed',error=str(exc))
            with db() as c:c.execute("UPDATE documents SET status='failed',error=? WHERE id=? AND status!='ready'",(str(exc),doc_id))
        result['seconds']=round(time.monotonic()-start,2);report['materials'].append(result)
        report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(result),flush=True)
    with db() as c:
        covered={r[0] for r in c.execute("SELECT DISTINCT t.competency_id FROM document_topics t JOIN documents d ON d.id=t.doc_id WHERE d.status='ready'")}
        report['role_coverage']={rid:{'covered':sorted(set(r['requirements'])&covered),'missing':sorted(set(r['requirements'])-covered)} for rid,r in role_catalog.ROLES.items()}
        report['integrity']=c.execute('PRAGMA integrity_check').fetchone()[0]
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return 1 if any(x['status']!='ready' for x in report['materials']) else 0

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('folder',type=Path,nargs='?',default=ROOT/'data/study_materials')
    sys.exit(run(parser.parse_args().folder))
