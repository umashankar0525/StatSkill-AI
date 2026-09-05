/* Adapters for the UI imported from varshasrikadapa-a11y/statskill-ai-v.
 * Only authenticated API data supplies scores, courses, profiles and actions.
 */
const uiIsStaff = () => ['trainer','admin','superadmin'].includes(store.state.user?.role);
const uiCommand = (fn,...args) => esc(`${fn}(${args.map(x=>JSON.stringify(x)).join(',')})`);
const uiButton = (label,fn,args=[],secondary=false) => `<button class="btn ${secondary?'btn-secondary':'btn-primary'}" onclick="${uiCommand(fn,...args)}" ${store.state.busy?'disabled':''}>${esc(tr(label))}</button>`;
const uiHeader = (title,description,icon='fa-layer-group') => `<div class="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-200/80 shadow-sm border-l-4 border-l-teal-500"><div class="flex items-center gap-3"><i class="fa-solid ${icon} text-teal-600"></i><h1 class="text-2xl sm:text-3xl font-bold text-navy-900">${esc(tr(title))}</h1></div><p class="text-sm text-slate-600 mt-3">${esc(tr(description))}</p></div>`;

function importedState(){
    const s=store.state,d=s.data,p=d.profile,enrolled=d.courses.filter(c=>c.enrolment_status),completed=enrolled.filter(c=>c.enrolment_status==='completed');
    const competencies=d.gaps.map(g=>({id:g.competency_id,name:esc(tr(g.competency_name)),domain:esc(s.framework.competencies.find(c=>c.id===g.competency_id)?.type||'Skill'),currentLevel:g.current_level,requiredLevel:g.required_level,gap:g.gap,priority:g.gap>=3?'Critical':g.gap>=2?'High':g.gap>0?'Moderate':'None'}));
    const user={...d.user,education:p.education||'',experience:p.experience_years===''?'Not provided':p.experience_years,projects:p.responsibilities||'',administration_type:d.user.administration_type||p.cadre||d.user.org_type||'Official Cadre',employeeId:d.user.employee_id||d.user.id,learningProgressPercent:enrolled.length?Math.round(completed.length/enrolled.length*100):0,assessmentsCompleted:d.assessments.filter(a=>a.status==='complete').length};
    // Imported templates interpolate strings; escape profile data at the boundary.
    for(const key of Object.keys(user))if(typeof user[key]==='string')user[key]=esc(user[key]);
    return {...s,user,overallScore:d.overall_score,assessedCount:d.gaps.filter(g=>g.current_level!==null).length,activeGoalCount:d.okrs.filter(o=>o.status==='active').length,
        competencyFramework:[{competencies}],learningPath:d.courses.filter(c=>c.enrolment_status||c.recommended||(!c.external&&c.priority_score>0)).map((c,i)=>({id:c.id,title:esc(c.title),phase:`Course ${i+1}`,duration:'Self-paced',source:'Learning catalogue',provider:'Published learning material',competency:esc(tr(c.competency)),targetLevel:d.gaps.find(g=>g.competency_id===c.competency_id)?`Role target: Level ${d.gaps.find(g=>g.competency_id===c.competency_id).required_level}`:'Additional learning',progress:c.enrolment_status==='completed'?100:0,enrolled:!!c.enrolment_status,raw:c}))};
}

function renderRecentAssessment(){
    const latest=store.state.data.assessments[0];
    if(!latest)return empty('No assessments completed yet.');
    return `<div class="p-4 rounded-xl bg-white border border-slate-200 space-y-3"><p class="text-sm font-semibold">${latest.kind==='initial'?'Role assessment':'Course assessment'}</p><p class="text-xs text-slate-500">${new Date(latest.created*1000).toLocaleDateString()} · ${esc(latest.status)}</p>${uiButton(latest.status==='complete'?'View results':'Resume','store.resumeAssessment',[latest.id])}</div>`;
}

function courseActions(course){
    const actions=[];
    if(course.external){
        actions.push(`<a class="btn btn-primary" href="${esc(course.url)}" target="_blank" rel="noopener noreferrer">Open on iGOT</a>`);
        if(!course.enrolment_status)actions.push(uiButton('Save to my learning','store.save',['/api/igot/save',{course_id:course.id},'Course saved.'],true));
        return actions.join('');
    }
    if(course.doc_id){actions.push(uiButton('Read material','store.viewSource',[course.doc_id],true));actions.push(uiButton('Download material','store.download',[course.doc_id],true));}
    if(course.url){try{const url=new URL(course.url);if(['http:','https:'].includes(url.protocol))actions.push(`<a class="btn btn-secondary" href="${esc(url.href)}" target="_blank" rel="noopener noreferrer">Open course</a>`);}catch{}}
    if(!course.enrolment_status)actions.push(uiButton('Add to my learning','store.save',['/api/courses/enrol',{course_id:course.id},'Course added.']));
    else actions.push(uiButton('Take assessment','store.startAssessment',[course.id]));
    return actions.join('');
}

function sourceButtons(sources){
    return sources.length?`<div class="mt-3 pt-2 border-t border-slate-200 text-xs"><strong>${tr('Sources')}</strong>${sources.map(source=>`<button class="block text-left underline mt-2" onclick="${uiCommand('openUiSource',source.doc_id)}">${esc(source.title||source.filename||'Learning material')} ${esc(source.location||'')}</button>`).join('')}</div>`:'';
}
function openUiSource(id){store.state.isChatOpen=false;store.viewSource(id);}

function renderWorkspaceNavigation(){
    const items=[['learner-dash','Home'],['framework','My skills'],['assessment','Assessments'],['recommendations','Learning advisor'],['learning-path','My learning'],['okrs','My goals'],['reports','My progress'],['profile','My profile']];
    if(uiIsStaff())items.push(['ai-generator','Learning materials'],['admin-dash','Workforce']);
    return `<nav aria-label="Workspace" class="workspace-tabs no-print"><div class="max-w-7xl mx-auto flex gap-2 px-4 sm:px-8">${items.map(([id,label])=>`<button onclick="${uiCommand('store.navigate',id)}" ${store.state.activeView===id?'aria-current="page"':''}>${esc(tr(label))}</button>`).join('')}</div></nav>`;
}

function renderImportedView(){
    const s=store.state;
    if(!s.data)return `<div class="max-w-7xl mx-auto p-8">${empty('Loading your saved profile…')}</div>`;
    const view=s.activeView==='landing'?'learner-dash':s.activeView;
    if(['ai-generator','trainer-dash','admin-dash'].includes(view)&&!uiIsStaff())return empty('Trainer or administrator access is required.');
    const adapted=importedState();
    if(view==='learner-dash')return renderLearnerDashboard(adapted);
    if(view==='recommendations')return renderRecommendations(s);
    if(view==='learning-path')return renderLearningPath(adapted);
    if(view==='framework')return renderCompetencyFramework(s);
    if(view==='profile')return renderUserProfile(adapted);
    if(view==='quiz-player')return renderQuizPlayer(s);
    const routes={assessment:renderAssessments,profile:renderProfile,okrs:renderOKRs,reports:renderReports,'ai-generator':renderMaterials,'trainer-dash':renderMaterials,'admin-dash':renderWorkforce,source:renderSource};
    return `<section class="connected-view max-w-7xl mx-auto px-4 sm:px-8 py-8"><div class="live-content stat-card p-6 sm:p-8">${routes[view]?routes[view]():empty('Choose a workspace section.')}</div></section>`;
}

function uiBrand(){return `<div class="flex items-center gap-3"><div class="w-10 h-10 rounded-xl bg-navy-900 flex items-center justify-center text-teal-400"><i class="fa-solid fa-layer-group"></i></div><div><strong class="text-xl text-navy-900">StatSkill <span class="text-teal-600">AI</span></strong><span class="block text-[10px] uppercase tracking-wider text-slate-500">Workforce Intelligence</span></div></div>`;}
function languageControl(){return `<label class="flex items-center gap-2 text-xs text-slate-600"><span class="sr-only">${tr('Change language')}</span><i class="fa-solid fa-globe"></i><select aria-label="${tr('Change language')}" onchange="store.setLanguage(this.value)" class="border border-slate-200 rounded-xl p-2 bg-white"><option value="en" ${store.state.currentLanguage==='en'?'selected':''}>English</option><option value="hi" ${store.state.currentLanguage==='hi'?'selected':''}>हिन्दी</option></select></label>`;}
function renderLanguageGate(){return `<main class="access-screen"><section class="glass-panel language-panel p-7 sm:p-10 rounded-3xl border border-slate-200 shadow-xl">${uiBrand()}<div class="mt-10"><h1 class="text-3xl font-heading font-bold text-navy-900">Choose your language</h1><p class="text-lg text-slate-500 mt-3" lang="hi">अपनी भाषा चुनें</p></div><div class="grid sm:grid-cols-2 gap-4 mt-7"><button class="language-choice" onclick="store.chooseLanguage('en')"><strong>English</strong><span>Continue in English</span></button><button class="language-choice" lang="hi" onclick="store.chooseLanguage('hi')"><strong>हिन्दी</strong><span>हिन्दी में आगे बढ़ें</span></button></div></section></main>`;}
function renderEntry(state){return `<main class="access-screen"><div class="w-full max-w-xl"><header class="flex justify-between items-center gap-4 mb-7">${uiBrand()}${languageControl()}</header>${renderAuthModal({...state, isAuthModalOpen: true})}<p class="text-center text-xs text-slate-500 mt-7">${tr('National Competency & Learning Portal for Official Statistics')}</p></div></main>`;}

function renderImportedFooter(){return `<footer class="bg-navy-950 text-slate-400 text-xs border-t border-slate-800 py-8 px-4 sm:px-8 mt-auto no-print"><div class="max-w-7xl mx-auto flex flex-wrap justify-between gap-6"><div><strong class="text-white text-base">StatSkill <span class="text-teal-400">AI</span></strong><p class="mt-2">${tr('National Competency & Learning Portal for Official Statistics')}</p></div><div class="flex flex-wrap items-center gap-5"><button onclick="store.navigate('profile')">${tr('My profile')}</button><button onclick="store.navigate('reports')">${tr('My progress')}</button><button onclick="window.toggleAccessibilityPanel(event)">Accessibility</button></div></div></footer>`;}
