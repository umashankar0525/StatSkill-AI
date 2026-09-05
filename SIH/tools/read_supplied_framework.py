from pathlib import Path
from pypdf import PdfReader
root=Path(__file__).resolve().parents[1]
out=root/'tmp'/'pdfs';out.mkdir(parents=True,exist_ok=True)
for name in ('All4one.pdf','Filtered_Competency_Role_Depth_Matrix_Page6_Removed.pdf'):
    path=Path.home()/'Downloads'/name
    pdf=PdfReader(path)
    text='\n\n'.join(f'--- PAGE {i+1} ---\n'+page.extract_text(extraction_mode='layout') for i,page in enumerate(pdf.pages))
    (out/(path.stem+'.txt')).write_text(text,encoding='utf-8')
    print(f'{name}: {len(pdf.pages)} pages, {len(text)} characters')
