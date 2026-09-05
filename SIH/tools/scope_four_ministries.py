"""Apply the user's explicit four-ministry, seventeen-work-area scope."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
MINISTRIES=[
 ('MOSPI','Ministry of Statistics & Programme Implementation (MoSPI)',[
  'Survey Methodology & Sampling','National Accounts & Economic Statistics','Price & Index Statistics','Industrial Statistics','SDG, Metadata & Data Quality','Data Informatics, AI & Analytics']),
 ('AGRICULTURE','Ministry of Agriculture & Farmers Welfare (ES&E / DES)',[
  'Agricultural Statistics','Cost of Cultivation','Land Use, GIS & Geospatial Analytics','Agricultural Prices & Market Intelligence']),
 ('LABOUR','Ministry of Labour & Employment (Labour Bureau)',[
  'Labour & Employment Statistics','Price & Index Statistics','Labour Surveys, Research & Analytics','Training, Data Quality & Digitization']),
 ('COMMERCE','Ministry of Commerce & Industry (Department of Commerce / DGCI&S)',[
  'Trade Statistics','Export-Import Data & Commercial Intelligence','Open Data, APIs & Data Processing'])]

def apply(result):
    result['ministries']=[]
    index=0
    for mid,name,names in MINISTRIES:
        departments=[]
        for label in names:
            area=result['areas'][index]
            area.setdefault('source_area',area['name'])
            area.update(name=label,ministry_id=mid,ministry=name)
            departments.append(dict(id=area['id'],name=label))
            index+=1
        result['ministries'].append(dict(id=mid,name=name,departments=departments))
    assert index==len(result['areas'])==17
    result['ministry_source']='User-selected four ministries and seventeen work areas, 2026-09-04'
    result['version']='supplied-pdfs-four-ministries-2026-09-04'
    return result

if __name__=='__main__':
    path=ROOT/'data/role_framework.json'
    path.write_text(json.dumps(apply(json.loads(path.read_text(encoding='utf-8'))),ensure_ascii=False,indent=2),encoding='utf-8')
