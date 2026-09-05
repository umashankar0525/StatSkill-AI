"""Reproducible extraction from the user's PDFs; no model-inferred requirements."""
from pathlib import Path
import re,json,hashlib
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
DOWNLOADS=Path.home()/'Downloads'
SOURCE=ROOT.parents[1]/'.soul-integration'/'source'
NAMES=['Survey Design','Sampling','Python','SQL','Ethics','Labour Statistics','Agricultural Statistics','Industrial Statistics','SDG Indicators','AI/ML','Cybersecurity','Communication']
IDS=['C_SURVEY','C_SAMPLING','C_PYTHON','C_SQL','C_ETHICS','C_LABOUR','C_AGRI','C_INDUSTRIAL','C_SDG','C_AI_ML','C_CYBER','C_COMMUNICATION']
TCODES={1:'C_SURVEY',2:'C_SAMPLING',11:'C_PYTHON',13:'C_SQL',31:'C_ETHICS',5:'C_LABOUR',6:'C_AGRI',7:'C_INDUSTRIAL',8:'C_SDG',19:'C_AI_ML',23:'C_CYBER',29:'C_COMMUNICATION'}
EXTRA={3:('C_NAT_ACC','National Accounts','Domain'),4:('C_PRICE','Price Statistics','Domain'),9:('C_METADATA','Metadata Standards','Domain'),10:('C_DATA_QUALITY','Data Quality Frameworks','Domain'),12:('C_R','R','Functional'),14:('C_STATA','Stata','Functional'),15:('C_SPSS','SPSS','Functional'),16:('C_SAS','SAS','Functional'),17:('C_GIS','GIS & Geospatial','Functional'),18:('C_DATAVIZ','Data Visualization','Functional'),20:('C_CLOUD','Cloud Computing','Functional'),21:('C_APIS','APIs','Functional'),22:('C_OPEN_DATA','Open Data','Functional'),24:('C_DPDP','Data Privacy','Functional'),25:('C_DIGITAL_SIGNATURES','Digital Signatures','Functional'),26:('C_GOV_CLOUD','Government Cloud','Functional'),27:('C_DPI','Digital Public Infrastructure (DPI)','Functional'),28:('C_LEADERSHIP','Leadership','Behavioural'),30:('C_PROJECT_MGMT','Project Management','Behavioural'),32:('C_DECISION_MAKING','Decision Making','Behavioural'),33:('C_CHANGE_MGMT','Change Management','Behavioural')}
TCODES.update({code:value[0] for code,value in EXTRA.items()})
FILES=['All4one.pdf','Filtered_Competency_Role_Depth_Matrix_Page6_Removed.pdf']
def parse(name,prefix):
    areas={};area=None;current=None
    for page_number,page in enumerate(PdfReader(DOWNLOADS/name).pages,1):
        for line in page.extract_text(extraction_mode='layout').splitlines():
            title=line.strip()
            if prefix=='T' and re.match(r'^\s{2}(MoSPI|Agriculture|Labour|Commerce) — ',line):
                area=title;areas.setdefault(area,[]);current=None;continue
            if prefix=='C' and title in ['Survey Methodology & Sampling','Labour Statistics','Agricultural Statistics','Industrial Statistics','SDG Indicators & Monitoring','Data Analytics, AI/ML & Digital Systems']:
                area=title;areas.setdefault(area,[]);current=None;continue
            match=re.match(r'^\s+(\d+)\s{2,}(.+?)\s{2,}L([1-6])\s{2,}(.+)',line)
            if match and area:
                rest=re.split(r'\s{4,}',match[4],maxsplit=1)
                current={'title':match[2].strip(),'grade':int(match[3]),'requirements':{},'duties':rest[1].strip() if len(rest)>1 else '', 'source':name,'page':page_number}
                areas[area].append(current);mapping=rest[0]
            elif current and re.match(r'^\s{15,}[TC]\d',line):
                rest=re.split(r'\s{4,}',line.strip(),maxsplit=1);mapping=rest[0]
                if len(rest)>1:current['duties']+=' '+rest[1].strip()
            else:
                continue
            for code,level in re.findall(rf'{prefix}(\d+):L([1-6])',mapping):
                cid=TCODES.get(int(code)) if prefix=='T' else IDS[int(code)-1]
                if cid:current['requirements'][cid]=int(level)
    return areas
all_areas=parse(FILES[0],'T');filtered=parse(FILES[1],'C')
assert len(all_areas)==17 and sum(map(len,all_areas.values()))==102
assert len(filtered)==6 and sum(map(len,filtered.values()))==36
overrides={'MoSPI — Survey Methodology & Sampling':'Survey Methodology & Sampling','MoSPI — Industrial Statistics':'Industrial Statistics','MoSPI — SDG, Metadata & Data Quality':'SDG Indicators & Monitoring','MoSPI — Data Informatics, AI & Analytics':'Data Analytics, AI/ML & Digital Systems','Agriculture — Agricultural Statistics':'Agricultural Statistics','Labour — Labour & Employment Statistics':'Labour Statistics'}
areas=[]
for i,(name,rows) in enumerate(all_areas.items(),1):
    if name in overrides:rows=filtered[overrides[name]]
    assert len(rows)==6 and {r['grade'] for r in rows}==set(range(1,7)),name
    for row in rows:
        assert row['requirements'],(name,row)
        row['id']=f'PDF_A{i:02d}_L{row["grade"]}'
    areas.append({'id':f'A{i:02d}','name':name,'roles':rows})
ministries=[];active=None
for line in (SOURCE/'statskill-ministry-department-framework.md').read_text(encoding='utf-8').splitlines():
    if line.startswith('### Ministry'):
        active={'name':line[4:],'departments':[]};ministries.append(active)
    elif line.startswith('## 5.'):
        break
    elif active and line.startswith('| ') and not line.startswith('| Department'):
        cells=[x.strip() for x in line.strip('|').split('|')]
        if len(cells)==4:active['departments'].append({'name':cells[0],'sector':cells[1],'topics':cells[2]})
assert len(ministries)==10 and all(m['departments'] for m in ministries)
types=['Domain','Domain','Functional','Functional','Behavioural','Domain','Domain','Domain','Domain','Functional','Functional','Behavioural']
levels=['Foundational / Guided','Working / Independent','Practitioner / Analytical','Advanced / Supervisory','Expert / Strategic','Leadership / Governance']
result={'version':'supplied-pdfs-2026-09-04','sources':[{'file':name,'sha256':hashlib.sha256((DOWNLOADS/name).read_bytes()).hexdigest()} for name in FILES],
 'precedence':'Filtered PDF overrides the matching six domains. The other eleven All4one domains retain every explicit topic requirement from the full 33-topic register. A dash is not a requirement.',
 'competencies':[{'id':cid,'code':f'C{i+1}','name':name,'type':kind} for i,(cid,name,kind) in enumerate(zip(IDS,NAMES,types))],
 'levels':{str(i+1):label for i,label in enumerate(levels)},'areas':areas,'ministries':ministries,'ministry_source':'https://github.com/sivasankar-11/soul/blob/f99c5e454cd1fd60bcdf9ca84a0ba78c222fe378/statskill-ministry-department-framework.md'}
from scope_four_ministries import apply
result['competencies'].extend(dict(id=cid,code=f'T{code}',name=name,type=kind) for code,(cid,name,kind) in EXTRA.items())
result=apply(result)
(ROOT/'data').mkdir(exist_ok=True)
(ROOT/'data'/'role_framework.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'areas':len(areas),'roles':sum(len(a['roles']) for a in areas),'competencies':len(result['competencies']),'ministries':len(result['ministries']),'work_areas':sum(len(m['departments']) for m in result['ministries'])}))
