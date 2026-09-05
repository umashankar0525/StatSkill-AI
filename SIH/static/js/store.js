/** State is hydrated from authenticated APIs; no sample personas or scores. */
class AppStore {
    constructor() {
        this.listeners=[];
        this.token=sessionStorage.getItem('statskill_token') || '';
        this.state={user:null,currentRole:'learner',currentLanguage:localStorage.getItem('statskill_language')==='hi'?'hi':'en',languageChosen:false,activeView:'landing',
            isAuthModalOpen:false,authModalTab:'login',busy:false,error:'',notice:'',
            data:null,framework:null,admin:null,session:null,source:null,chatMessages:[],isChatOpen:false};
    }
    subscribe(fn){this.listeners.push(fn);return ()=>this.listeners=this.listeners.filter(x=>x!==fn);}
    notify(){this.listeners.forEach(fn=>fn(this.state));}
    async api(path,body){
        const r=await fetch(path,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json',...(this.token?{Authorization:`Bearer ${this.token}`}:{})},...(body===undefined?{}:{body:JSON.stringify(body)})});
        const data=await r.json();
        if(!r.ok || data.success===false) {
            if(r.status===401){this.token='';sessionStorage.removeItem('statskill_token');Object.assign(this.state,{user:null,data:null,admin:null,source:null,session:null,chatMessages:[],activeView:'landing',authModalTab:'login'});}
            throw new Error(data.error || `Request failed (${r.status})`);
        }
        return data;
    }
    async run(fn,message='Saved.'){
        if(this.state.busy)return;
        const initialView=this.state.activeView;
        const selector='.live-form input:not([type="password"]):not([type="file"]),.live-form textarea,.live-form select';
        const drafts=[...document.querySelectorAll(selector)].map(el=>({name:el.name,value:el.value,checked:el.checked}));
        this.state.busy=true;this.state.error='';this.state.notice='';this.notify();
        try{await fn();this.state.notice=message;}catch(e){this.state.error=e.message;}
        finally{this.state.busy=false;this.notify();if(this.state.error&&this.state.activeView===initialView){[...document.querySelectorAll(selector)].forEach((el,i)=>{if(drafts[i]?.name===el.name){el.value=drafts[i].value;if(el.type==='checkbox'||el.type==='radio')el.checked=drafts[i].checked;}});}}
    }
    async hydrate(){
        this.state.framework=await this.api('/api/framework');
        this.state.registrationCatalog=await this.api('/api/registration/catalog');
        if(this.token){
            this.state.data=await this.api('/api/overview');
            this.state.user=this.state.data.user;this.state.currentRole=this.state.user.role;
            const rec=this.state.data.recommendation_job;
            if(rec&&['queued','running'].includes(rec.status))this.watchRecommendations(rec.id);
            if(['admin','superadmin','trainer'].includes(this.state.currentRole))this.state.admin=await this.api('/api/admin');
        }
    }
    async boot(){await this.run(async()=>{await this.hydrate();if(this.token)this.state.activeView='learner-dash';},'');}
    async watchRecommendations(id){
        if(this.recommendationWatch===id)return;
        this.recommendationWatch=id;const token=this.token;
        try{
            for(let i=0;i<300&&this.token===token;i++){
                await new Promise(resolve=>setTimeout(resolve,1500));
                if(this.token!==token)return;
                const {job}=await this.api('/api/jobs/'+id);
                if(job.status==='complete'){
                    const data=await this.api('/api/overview');
                    if(this.token!==token)return;
                    this.state.data=data;
                    if(!(this.state.activeView==='quiz-player'&&this.state.session?.status==='active'))this.notify();
                    return;
                }
                if(job.status==='failed')return;
            }
        }catch{}finally{if(this.recommendationWatch===id)this.recommendationWatch=null;}
    }
    openAuthModal(tab='register'){this.state.authModalTab=tab;this.state.isAuthModalOpen=true;if(window.openAuthModal)window.openAuthModal(tab);else this.notify();}
    async logout(){await this.run(async()=>{await this.api('/api/auth/logout',{});this.token='';sessionStorage.removeItem('statskill_token');Object.assign(this.state,{user:null,data:null,admin:null,session:null,source:null,chatMessages:[],activeView:'landing'});},'Signed out.');}
    navigate(view){
        if(['login','register'].includes(view)){this.openAuthModal(view);return;}
        if(!['landing','framework','igot-hub'].includes(view)&&!this.state.user){this.openAuthModal('login');return;}
        this.state.activeView=view;this.state.error='';this.state.notice='';this.notify();window.scrollTo(0,0);
    }
    chooseLanguage(lang){this.state.languageChosen=true;this.setLanguage(lang);}
    setLanguage(lang){
        if(!['en','hi'].includes(lang))return;
        if(!this.state.user)window.rememberAuthFields?.();
        this.state.currentLanguage=lang;localStorage.setItem('statskill_language',lang);document.documentElement.lang=lang;this.notify();
    }
    toggleChat(){if(!this.state.user){this.openAuthModal('login');return;}this.state.isChatOpen=!this.state.isChatOpen;this.notify();}
    async job(path,body){
        const started=await this.api(path,body);
        if(started.session)return started.session;
        if(!started.job_id)return started;
        const {job_id}=started;
        for(let i=0;i<4800;i++){
            await new Promise(resolve=>setTimeout(resolve,i<6?400:1500));
            const {job}=await this.api(`/api/jobs/${job_id}`);
            if(job.status==='complete'){
                if(path==='/api/quiz/next'&&!job.result?.question)return (await this.api('/api/quiz/next',body)).session;
                return job.result;
            }
            if(['/api/quiz/next','/api/quiz/submit'].includes(path)&&(i%3===0||job.status==='failed')){
                this.state.session=(await this.api('/api/quiz/'+body.session_id)).session;this.notify();
                if(path==='/api/quiz/submit'&&this.state.session.result)return {result:this.state.session.result};
            }
            if(job.status==='failed')throw new Error(job.error || 'Processing failed. Retry the operation.');
        }
        throw new Error('Processing is taking longer than expected. Refresh to check saved progress.');
    }
    async startAssessment(courseId){await this.run(async()=>{
        const data=await this.api('/api/quiz/start',{...(courseId?{kind:'course',course_id:courseId}:{kind:'initial'}),language:this.state.currentLanguage});
        this.state.session=data.session;this.state.activeView='quiz-player';this.notify();await this.advance();
    },'');}
    async resumeAssessment(id){await this.run(async()=>{this.state.session=(await this.api(`/api/quiz/${id}`)).session;this.state.activeView='quiz-player';this.notify();await this.advance();},'');}
    async advance(){
        let s=this.state.session;
        if(s.status==='complete')return;
        if(s.answered>=s.target){
            const data=await this.job('/api/quiz/submit',{session_id:s.id});
            this.state.session={...s,status:'complete',question:null,result:data.result};await this.hydrate();
        }else if(!s.question){this.state.session=await this.job('/api/quiz/next',{session_id:s.id});}
        const current=this.state.session;
        if(current?.question&&current.answered+1<current.target){
            this.api('/api/quiz/prepare',{session_id:current.id}).catch(()=>{});
        }
    }
    async submitAnswer(skip=false){
        const q=this.state.session?.question;
        if(!q || this.state.busy)return;
        const selected=document.querySelector('input[name="quizAnswer"]:checked');
        if(!skip&&!selected){this.state.error='Choose an answer or use Skip.';this.notify();return;}
        const choice=skip?null:Number(selected.value);
        await this.run(async()=>{this.state.session=(await this.api('/api/quiz/answer',{session_id:this.state.session.id,question_id:q.id,answer:choice})).session;this.notify();await this.advance();},'');
    }
    async save(path,body,message='Saved.') {await this.run(async()=>{await this.api(path,body);await this.hydrate();},message);}
    async viewSource(id){await this.run(async()=>{this.state.source=await this.api(`/api/documents/${id}`);this.state.activeView='source';},'');}
    async download(id){await this.run(async()=>{const r=await fetch(`/api/documents/${id}/download`,{headers:{Authorization:`Bearer ${this.token}`}});if(!r.ok)throw new Error('Original file is unavailable.');const blob=await r.blob();const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=this.state.data.documents.find(x=>x.id===id)?.filename||'material';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);},'');}
    async sendChatMessage(text){if(!text.trim()||this.state.busy)return;this.state.chatMessages.push({sender:'user',text});await this.run(async()=>{const result=await this.job('/api/ai/chat',{query:text,language:this.state.currentLanguage});this.state.chatMessages.push({sender:'ai',text:result.reply,sources:result.sources});},'');}
}
window.store=new AppStore();
