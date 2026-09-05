from pathlib import Path
root=Path(__file__).resolve().parents[1]/'static'/'js'
p=root/'components/authModal.js';s=p.read_text(encoding='utf-8')
s=s.replace("    let checkUsernameDebounceTimer = null;",'''    let checkUsernameDebounceTimer = null;
    const centralOptions=()=>store.state.registrationCatalog?.ministries||window.CENTRAL_HIERARCHY||[];
    window.handleAssessmentArea=function(id){
        window.rememberAuthFields();authState.assessmentArea=id;authState.assessmentRole='';authState.designation='';reRenderModal();
    };
    window.handleAssessmentRole=function(id){
        const area=store.state.registrationCatalog?.areas.find(a=>a.id===authState.assessmentArea);
        const role=area?.roles.find(r=>r.id===id);authState.assessmentRole=id;authState.designation=role?.title||'';
    };
''')
s=s.replace("window.CENTRAL_HIERARCHY[0]", "centralOptions()[0]")
s=s.replace("type==='central'?window.CENTRAL_HIERARCHY:window.STATE_HIERARCHY", "type==='central'?centralOptions():window.STATE_HIERARCHY")
s=s.replace("authState.adminType==='central'?window.CENTRAL_HIERARCHY:window.STATE_HIERARCHY", "authState.adminType==='central'?centralOptions():window.STATE_HIERARCHY")
s=s.replace("if (desigEl) authState.designation = desigEl.value.trim();", "if (desigEl) window.handleAssessmentRole(desigEl.value);")
s=s.replace("        authState.error = null;\n        authState.step = 2;", "        if(!authState.assessmentRole){authState.error='Choose your work area and designation.';reRenderModal();return;}\n        authState.error = null;\n        authState.step = 2;",1)
s=s.replace('            designation: authState.designation,','            designation: authState.designation,\n            assessment_area: authState.assessmentArea,\n            assessment_role_id: authState.assessmentRole,')
s=s.replace("const designations = (window.OFFICIAL_STATISTICAL_DESIGNATIONS || []);", "const areas=store.state.registrationCatalog?.areas||[];\n        const designations=areas.find(a=>a.id===authState.assessmentArea)?.roles||[];")
a=s.index('                    <!-- Designation -->');b=s.index('                    <!-- Education -->',a)
s=s[:a]+'''                    <div class="space-y-1 sm:col-span-2">
                        <label for="regAssessmentArea" class="block text-xs font-semibold text-slate-700">Work area *</label>
                        <select id="regAssessmentArea" onchange="handleAssessmentArea(this.value)" class="w-full px-3 py-2 bg-white border border-slate-200 rounded-xl text-xs font-medium text-slate-900">
                            <option value="">Choose your work area</option>${areas.map(a=>`<option value="${esc(a.id)}" ${a.id===authState.assessmentArea?'selected':''}>${esc(a.name)}</option>`).join('')}
                        </select>
                    </div>
                    <div class="space-y-1 sm:col-span-2">
                        <label for="regDesignation" class="block text-xs font-semibold text-slate-700">Designation *</label>
                        <select id="regDesignation" onchange="handleAssessmentRole(this.value)" class="w-full px-3 py-2 bg-white border border-slate-200 rounded-xl text-xs font-medium text-slate-900">
                            <option value="">Choose your designation</option>${designations.map(r=>`<option value="${esc(r.id)}" ${r.id===authState.assessmentRole?'selected':''}>${esc(r.title)}</option>`).join('')}
                        </select>
                    </div>

'''+s[b:]
s=s.replace('Ministry / Central Entity', "${authState.adminType==='central'?'Ministry / Central Entity':'State / Union Territory'}")
p.write_text(s,encoding='utf-8')
p=root/'components/profile.js';s=p.read_text(encoding='utf-8')
a=s.index('    const currentMinistry =',s.index('window.openEditProfileModal'))
s=s[:a]+'''    const catalog=store.state.registrationCatalog;
    const selectedArea=user.assessment_area||'';
    const selectedRole=user.assessment_role_id||'';
'''+s[a:]
# Use the same supplied ministry/department directory in the edit dialog.
s=s.replace("typeof window.getAllMinistriesList === 'function' ? window.getAllMinistriesList()", "catalog ? catalog.ministries.map(m=>m.name) : typeof window.getAllMinistriesList === 'function' ? window.getAllMinistriesList()")
s=s.replace("typeof window.getDepartmentsForMinistry === 'function' ? window.getDepartmentsForMinistry(currentMinistry)", "catalog?.ministries.find(m=>m.name===currentMinistry) ? catalog.ministries.find(m=>m.name===currentMinistry).departments.map(d=>d.name) : typeof window.getDepartmentsForMinistry === 'function' ? window.getDepartmentsForMinistry(currentMinistry)")
marker='                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3.5 pt-1">'
s=s.replace(marker,'''                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                    <div><label for="modal_prof_area" class="font-bold text-slate-700 block mb-1">Work area *</label><select id="modal_prof_area" onchange="changeProfileWorkArea()" class="w-full p-2.5 border border-slate-300 rounded-lg"><option value="">Choose your work area</option>${(catalog?.areas||[]).map(a=>`<option value="${esc(a.id)}" ${a.id===selectedArea?'selected':''}>${esc(a.name)}</option>`).join('')}</select></div>
                    <div><label for="modal_prof_role" class="font-bold text-slate-700 block mb-1">Designation *</label><select id="modal_prof_role" onchange="changeProfileWorkRole()" class="w-full p-2.5 border border-slate-300 rounded-lg"><option value="">Choose your designation</option>${(catalog?.areas.find(a=>a.id===selectedArea)?.roles||[]).map(r=>`<option value="${esc(r.id)}" ${r.id===selectedRole?'selected':''}>${esc(r.title)}</option>`).join('')}</select></div>
                </div>
'''+marker)
s=s.replace("    const selectedMin = minSelect.value;", "    const selectedMin = minSelect.value;\n    const entry=store.state.registrationCatalog?.ministries.find(m=>m.name===selectedMin);\n    if(entry){deptSelect.innerHTML=entry.departments.map(d=>`<option value=\"${esc(d.name)}\">${esc(d.name)}</option>`).join('');return;}")
s=s.replace("const fields={name:","const fields={area:'assessment_area',role:'assessment_role_id',name:")
s=s.replace("    if(['name','location'", "    if(['assessment_area','assessment_role_id','name','location'")
s=s.replace("        trainingProgrammes: trainVal !== undefined ? trainVal : baseUser.trainingProgrammes", "        assessment_area: document.getElementById('modal_prof_area')?.value||'',\n        assessment_role_id: document.getElementById('modal_prof_role')?.value||'',\n        trainingProgrammes: trainVal !== undefined ? trainVal : baseUser.trainingProgrammes")
s+='''
window.changeProfileWorkArea=function(){
    const area=store.state.registrationCatalog.areas.find(a=>a.id===document.getElementById('modal_prof_area').value);
    document.getElementById('modal_prof_role').innerHTML='<option value="">Choose your designation</option>'+(area?.roles||[]).map(r=>`<option value="${esc(r.id)}">${esc(r.title)}</option>`).join('');
};
window.changeProfileWorkRole=function(){
    const area=store.state.registrationCatalog.areas.find(a=>a.id===document.getElementById('modal_prof_area').value);
    const role=area?.roles.find(r=>r.id===document.getElementById('modal_prof_role').value);
    if(role){const designation=document.getElementById('modal_prof_desig');if(designation.tagName==='SELECT')designation.innerHTML=`<option value="${esc(role.title)}">${esc(role.title)}</option>`;else designation.value=role.title;}
};
'''
p.write_text(s,encoding='utf-8')
