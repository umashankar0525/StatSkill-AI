"""Read-only validation of the imported originals and role coverage."""
import hashlib,json,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'data/study_material_manifest.json').read_text(encoding='utf-8'))
report=json.loads((ROOT/'tmp/study-material-import.json').read_text(encoding='utf-8'))
c=sqlite3.connect(f'file:{(ROOT/"igot_demo.db").as_posix()}?mode=ro',uri=True);c.row_factory=sqlite3.Row
for entry in manifest['materials']:
    doc_id='pdf-'+entry['sha256'][:24]
    row=c.execute('SELECT * FROM documents WHERE id=?',(doc_id,)).fetchone()
    assert row and row['status']=='ready'
    assert hashlib.sha256(Path(row['storage_path']).read_bytes()).hexdigest()==entry['sha256']
    pages=c.execute('SELECT min(page_num),max(page_num),count(*) FROM doc_chunks WHERE doc_id=?',(doc_id,)).fetchone()
    assert pages[0]>=1 and pages[1]<=entry['pages'] and pages[2]>0
    assert c.execute('SELECT source_hash FROM document_provenance WHERE doc_id=?',(doc_id,)).fetchone()[0]==entry['sha256']
covered={r[0] for r in c.execute('SELECT DISTINCT competency_id FROM document_topics')}
needed={r[0] for r in c.execute("SELECT DISTINCT competency_id FROM frac_role_competency_map WHERE role_id LIKE 'PDF_%'")}
missing=[dict(r) for r in c.execute('SELECT id,name FROM frac_competencies ORDER BY name') if r['id'] in needed-covered]
summary={'documents':len(manifest['materials']),'pages':sum(x['pages'] for x in manifest['materials']),'chunks':sum(x['chunks'] for x in report['materials']),'covered_topics':len(covered),'required_topics':len(needed),'missing_topics':missing,'fully_covered_roles':sum(not r['missing'] for r in report['role_coverage'].values()),'roles':len(report['role_coverage']),'current_role_missing_topics':report['role_coverage']['PDF_A03_L1']['missing'],'integrity':c.execute('PRAGMA integrity_check').fetchone()[0],'users':c.execute('SELECT count(*) FROM users').fetchone()[0],'assessments':c.execute('SELECT count(*) FROM assessments').fetchone()[0]}
summary['covered_required_topics']=len(covered&needed)
(ROOT/'tmp/study-import-audit.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
c.close()
