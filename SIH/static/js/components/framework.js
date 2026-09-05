/* Skill-card / matrix layout adapted from statskill-ai-v/components/framework.js.
 * Levels and role requirements are read from the backend, never recomputed here.
 */
let skillView='cards';
function renderCompetencyFramework(state){
    const d=state.data,f=state.framework,admin=['admin','superadmin'].includes(state.currentRole);
    return `<div class="max-w-7xl mx-auto px-4 sm:px-8 py-8 space-y-8">
        ${uiHeader('Skills for your role','Compare your assessed skills with the requirements of your work.','fa-layer-group')}
        <div class="flex flex-wrap items-center justify-between gap-4"><div class="flex gap-2"><button class="btn ${skillView==='cards'?'btn-primary':'btn-secondary'}" onclick="skillView='cards';store.notify()">Cards</button><button class="btn ${skillView==='matrix'?'btn-primary':'btn-secondary'}" onclick="skillView='matrix';store.notify()">Skills matrix</button></div>${uiButton('Start my assessment','store.startAssessment')}</div>
        ${skillView==='matrix'?`<div class="stat-card p-5 live-content">${gapTable(d.gaps)}</div>`:`<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">${d.gaps.map(g=>{
            const c=f.competencies.find(c=>c.id===g.competency_id),gap=g.gap;
            return `<article class="stat-card p-5 space-y-4"><div class="flex items-start justify-between gap-3"><span class="text-xs font-semibold uppercase text-teal-700">${esc(c?.type||'Skill')}</span><span class="text-xs font-semibold ${gap===null?'text-slate-500':gap>0?'text-orange-600':'text-emerald-700'}">${gap===null?'Not assessed':gap>0?`${gap} level gap`:'Target met'}</span></div><h2 class="text-base font-bold text-navy-900">${esc(tr(g.competency_name))}</h2><p class="text-xs text-slate-600">${esc(c?.description||'')}</p><div class="grid grid-cols-2 gap-3 text-center"><div class="bg-slate-50 border border-slate-200 rounded-xl p-3"><span class="block text-xs text-slate-500">${tr('Assessed')}</span><strong class="block text-lg text-navy-900 mt-1 skill-current">${g.current_level===null?tr('Not assessed'):`Level ${g.current_level}`}</strong></div><div class="bg-teal-50 border border-teal-100 rounded-xl p-3"><span class="block text-xs text-teal-700">${tr('Required')}</span><strong class="block text-lg text-teal-900 mt-1">Level ${g.required_level}</strong></div></div><div>${uiButton('Find learning','store.navigate',['recommendations'],true)}</div></article>`;
        }).join('')}</div>`}
        ${!d.gaps.length?empty('Complete your role profile to establish the required competencies.'):''}
        ${admin?`<div class="stat-card p-6 live-content"><h2>Update a role requirement</h2><form class="live-form" onsubmit="saveMapping(event)"><div class="form-grid">${select('Role','role_id',f.roles,d.profile.role_id,'id','title')}${select('Competency','competency_id',f.competencies)}${field('Required level','required_level',3,'number','min="1" max="6" required')}</div><button class="live-btn" ${state.busy?'disabled':''}>Save mapping</button></form></div>`:''}
    </div>`;
}
