"""One-time wiring of the shared catalogue into account forms and APIs."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'live_api.py'
s=p.read_text(encoding='utf-8')
start=s.index('    """Validate optional work context',s.index('def registration_profile'))
end=s.index('\ndef ',start)
s=s[:start]+'''    """All account entry points share the same supported ministry/role checks."""
    try:
        p=account_service.profile_values(data)
        p['language']=data.get('language','en')
        require(p['language'] in ('en','hi'),'Please choose English or Hindi.')
        return p
    except (ValueError,TypeError) as exc:
        raise APIError(str(exc)) from exc

'''+s[end:]
start=s.index("        p=profile(user)",s.index("    if path=='/api/profile' and method=='POST':"))
end=s.index("    if path in ('/api/quiz/start'",start)
s=s[:start]+"        return account_service.update(user,data,profile(user))\n"+s[end:]
# These older public endpoints must never expose the previous all-government seed.
needle='def handle(h,method,path,data):\n'
s=s.replace(needle,needle+'''    if method=='GET' and path=='/api/ministries/central':
        h.send_json([dict(id=m['id'],name=m['name']) for m in role_catalog.CATALOG['ministries']]);return True
    if method=='GET' and path.startswith('/api/ministries/central/') and path.endswith('/departments'):
        mid=path.split('/')[4]
        ministry=next((m for m in role_catalog.CATALOG['ministries'] if m['id']==mid),None)
        h.send_json(ministry['departments'] if ministry else []);return True
    if method=='GET' and (path=='/api/states' or path.startswith('/api/departments/state/')):
        h.send_json([]);return True
''')
p.write_text(s,encoding='utf-8')

p=ROOT/'static/js/components/authModal.js';s=p.read_text(encoding='utf-8')
s=s.replace('store.state.registrationCatalog?.ministries||window.CENTRAL_HIERARCHY||[]','store.state.registrationCatalog?.ministries||[]')
s=s.replace("authState.assessmentArea=id;authState.assessmentRole='';", "authState.assessmentArea=id;authState.department=store.state.registrationCatalog?.areas.find(a=>a.id===id)?.name||'';authState.assessmentRole='';")
a=s.index('        authState.adminType=type;');b=s.index('        reRenderModal();',a)
s=s[:a]+"        authState.adminType='central';\n"+s[b:]
s=s.replace("const list=authState.adminType==='central'?centralOptions():window.STATE_HIERARCHY;","const list=centralOptions();")
s=s.replace("authState.ministry=name;authState.department=found?.departments[0]?.name||'';", "authState.ministry=name;authState.department='';authState.assessmentArea='';authState.assessmentRole='';authState.designation='';")
s=s.replace("if (!authState.ministry && window.CENTRAL_HIERARCHY && window.CENTRAL_HIERARCHY.length > 0)","if (!authState.ministry && centralOptions().length)")
s=s.replace("if(!authState.ministry){const first=centralOptions()[0];", "if(!authState.ministry&&centralOptions().length){const first=centralOptions()[0];")
s=s.replace("const centralMinistries = (authState.adminType==='central'?centralOptions():window.STATE_HIERARCHY) || [];", "authState.adminType='central';\n        const centralMinistries=centralOptions();\n        if(!centralMinistries.some(m=>m.name===authState.ministry)){authState.ministry=centralMinistries[0]?.name||'';authState.assessmentArea='';authState.assessmentRole='';authState.department='';}")
s=s.replace("const areas=store.state.registrationCatalog?.areas||[];", "const areas=(store.state.registrationCatalog?.areas||[]).filter(a=>a.ministry===authState.ministry);")
s=s.replace('                            <option value="state" ${authState.adminType === \'state\' ? \'selected\' : \'\'}>State / UT Government</option>','')
a=s.index('                    <!-- Department -->',s.index('function renderStage1'))
b=s.index('                    <div class="space-y-1 sm:col-span-2">',a+60)
# Replace the whole old department selector; the work-area selection supplies it.
b=s.index('                    <div class="space-y-1 sm:col-span-2">',b+65)
s=s[:a]+'''                    <input type="hidden" id="regDepartment" value="${esc(authState.department)}">

'''+s[b:]
p.write_text(s,encoding='utf-8')

p=ROOT/'static/js/components/profile.js';s=p.read_text(encoding='utf-8')
a=s.index('    const currentMinistry = user.ministry');b=s.index('    const modalHTML =',a)
s=s[:a]+'''    const currentMinistry=catalog?.ministries.some(m=>m.name===user.ministry)?user.ministry:'';
    const allMinistries=(catalog?.ministries||[]).map(m=>m.name);
    const selectedAreas=(catalog?.areas||[]).filter(a=>a.ministry===currentMinistry);
    const allDepts=selectedAreas.map(a=>a.name);
    const allDesignations=(selectedAreas.find(a=>a.id===selectedArea)?.roles||[]).map(r=>r.title);

'''+s[b:]
s=s.replace('${(catalog?.areas||[]).map(a=>', '${selectedAreas.map(a=>')
s=s.replace('                                    ${allMinistries.map', '                                    <option value="">Choose your ministry</option>${allMinistries.map')
s=s.replace('id="modal_prof_dept" class=', 'id="modal_prof_dept" disabled class=')
s=s.replace('id="modal_prof_desig" class=', 'id="modal_prof_desig" disabled class=')
a=s.index('    const selectedMin = minSelect.value;',s.index('window.onModalMinistryChange'))
b=s.index('\n};',a)
s=s[:a]+'''    const areas=(store.state.registrationCatalog?.areas||[]).filter(a=>a.ministry===minSelect.value);
    document.getElementById('modal_prof_area').innerHTML='<option value="">Choose your work area</option>'+areas.map(a=>`<option value="${esc(a.id)}">${esc(a.name)}</option>`).join('');
    window.changeProfileWorkArea();
'''+s[b:]
s=s.replace("    document.getElementById('modal_prof_role').innerHTML=", "    const department=document.getElementById('modal_prof_dept');\n    if(department.tagName==='SELECT')department.innerHTML=`<option value=\"${esc(area?.name||'')}\">${esc(area?.name||'')}</option>`;else department.value=area?.name||'';\n    const designation=document.getElementById('modal_prof_desig');if(designation.tagName==='SELECT')designation.innerHTML='<option value=\"\"></option>';else designation.value='';\n    document.getElementById('modal_prof_role').innerHTML=")
p.write_text(s,encoding='utf-8')
