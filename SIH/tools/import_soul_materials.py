"""Import literal study text safely; never execute upstream ingestion scripts."""
import ast,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
SOURCE=ROOT.parents[1]/'.soul-integration/complete/soul-f99c5e454cd1fd60bcdf9ca84a0ba78c222fe378'
COMMIT='f99c5e454cd1fd60bcdf9ca84a0ba78c222fe378'
MATERIALS=[('ingest_communication_skills_pdf.py','PAGES_TEXT','Communication skills — SOUL study text',['C_COMMUNICATION']),
 ('ingest_sampling_pdf.py','pages','Survey sampling and R — SOUL study text',['C_SURVEY','C_SAMPLING','C_R']),
 ('ingest_ilo_labour_statistics_pdf.py','PAGES_TEXT','Labour statistics — SOUL study text',['C_LABOUR']),
 ('ingest_sdg_pdf.py','pages','SDG indicators — SOUL study text',['C_SDG'])]

def extract(file,variable):
    for node in ast.parse(file.read_text(encoding='utf-8-sig')).body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==variable for t in node.targets):
            pages=ast.literal_eval(node.value)
            if not isinstance(pages,list) or not all(isinstance(x,str) for x in pages):raise ValueError('Unexpected study text format.')
            return pages
    raise ValueError('No literal study text found.')

def run():
    import server,rag_engine,role_catalog,live_api
    from storage import db,encode
    output=[]
    for filename,variable,title,topics in MATERIALS:
        pages=extract(SOURCE/filename,variable);digest=hashlib.sha256(encode(pages).encode()).hexdigest();doc_id='soul-'+digest[:24]
        path=live_api.UPLOADS/(doc_id+'.txt');path.parent.mkdir(exist_ok=True,parents=True)
        uri=f'https://github.com/sivasankar-11/soul/blob/{COMMIT}/{filename}'
        path.write_text('Study text extracted from '+uri+'\n\n'+'\n\n'.join(f'Source page {i+1}\n{text}' for i,text in enumerate(pages)),encoding='utf-8')
        with db() as c:
            ready=c.execute("SELECT 1 FROM documents WHERE id=? AND status='ready'",(doc_id,)).fetchone()
            c.execute('INSERT OR IGNORE INTO documents(id,title,filename,uploaded_by,status,storage_path) VALUES(?,?,?,?,?,?)',(doc_id,title,path.name,'source-import','pending',str(path)))
        if not ready:
            rag_engine.process_and_store_pages(doc_id,title,path.name,'source-import',[dict(page=i+1,text=text) for i,text in enumerate(pages)])
        with db() as c:
            c.execute('INSERT OR REPLACE INTO document_provenance VALUES(?,?,?,?)',(doc_id,uri,digest,'repository study text; original publisher attribution unverified'))
            for topic in topics:c.execute('INSERT OR IGNORE INTO document_topics VALUES(?,?)',(doc_id,topic))
            roles=[rid for rid,r in role_catalog.ROLES.items() if set(topics)&r['requirements'].keys()]
            for role in roles:c.execute('INSERT OR IGNORE INTO document_assignments VALUES(?,?)',(doc_id,role))
        output.append(dict(doc_id=doc_id,title=title,pages=len(pages),topics=topics,assigned_roles=len(roles)))
        print(json.dumps(output[-1]),flush=True)
    with db() as c:
        needed={r[0] for r in c.execute('SELECT DISTINCT competency_id FROM frac_role_competency_map WHERE role_id LIKE ?',('PDF_%',))}
        covered={r[0] for r in c.execute('SELECT DISTINCT competency_id FROM document_topics')}
    result=dict(imported=output,missing_topics=sorted(needed-covered))
    (ROOT/'tmp/soul-material-import.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result

if __name__=='__main__':run()
