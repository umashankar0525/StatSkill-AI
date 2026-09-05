/* Imported presentation, existing authenticated application lifecycle. */
document.addEventListener('DOMContentLoaded',()=>{store.subscribe(renderApp);renderApp();store.boot();});
function renderApp(){
    const s=store.state,root=document.getElementById('app');
    document.documentElement.lang=s.currentLanguage;
    if(window.radarChartInstance){window.radarChartInstance.destroy();window.radarChartInstance=null;}
    try{
        if(!s.languageChosen){root.innerHTML=renderLanguageGate();return;}
        if(!s.user){root.innerHTML=renderEntry(s);localizeVisibleUI(root);return;}
        root.innerHTML=`${renderNavbar(importedState())}${renderWorkspaceNavigation()}<main class="flex-1">${s.busy&&!(s.activeView==='quiz-player'&&s.session?.question)?`<div class="live-status" role="status">${tr('Working…')}</div>`:''}${s.error?`<div class="live-error" role="alert">${esc(userFacingError(s.error))}</div>`:''}${s.notice?`<div class="live-status" role="status">${esc(tr(s.notice))}</div>`:''}${renderImportedView()}</main>${renderAiAssistant(s)}${renderImportedFooter()}`;
        localizeVisibleUI(root);
        if(['learner-dash','landing'].includes(s.activeView))initCompetencyRadarChart();
        if(s.isChatOpen)scrollChatBottom();
    }catch(error){root.innerHTML=`<div role="alert" class="live-error">${esc(userFacingError(error.message))}</div>`;console.error(error);}
}
setInterval(()=>{
    const s=store.state.session,q=s?.question,el=document.getElementById('questionTimer');
    if(!q||s.status!=='active'||!el)return;
    const remaining=Math.max(0,Math.ceil(q.deadline-Date.now()/1000));
    el.textContent=`${Math.floor(remaining/60)}:${String(remaining%60).padStart(2,'0')} ${store.state.currentLanguage==='hi'?'शेष':'remaining'}`;
    if(!remaining&&!store.state.busy)store.submitAnswer(true);
},1000);
