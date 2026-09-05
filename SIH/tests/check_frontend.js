/* Run against tests/preview_server.py only: node tests/check_frontend.js [static-root]. */
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const root=path.resolve(process.argv[2]||path.join(__dirname,'../static'));
const base='http://127.0.0.1:8011';
async function main(){
    const login=await fetch(base+'/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({identifier:'browser@test.invalid',password:'BrowserTest123'})}).then(r=>r.json());
    assert(login.token,'The isolated preview server must be running');
    const api=p=>fetch(base+p,{headers:{Authorization:`Bearer ${login.token}`}}).then(r=>r.json());
    const [data,framework,admin,registrationCatalog]=await Promise.all(['/api/overview','/api/framework','/api/admin','/api/registration/catalog'].map(api));
    const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
    const scripts=[...html.matchAll(/<script src="(\/[^"?]+)[^"]*"/g)].map(m=>m[1]);
    const context=vm.createContext({console,URL,Blob,Date,JSON,setTimeout:()=>0,setInterval:()=>0,clearTimeout:()=>{},sessionStorage:{getItem:()=>'',setItem:()=>{},removeItem:()=>{}},localStorage:{getItem:()=>'',setItem:()=>{}},document:{addEventListener:()=>{},querySelector:()=>null,querySelectorAll:()=>[],documentElement:{lang:'en'}},fetch});
    context.window=context;
    for(const file of scripts){
        assert(fs.existsSync(path.join(root,file)),`Missing script ${file}`);
        if(file.endsWith('accessibilityManager.js'))continue; // Requires a real browser; covered manually.
        vm.runInContext(fs.readFileSync(path.join(root,file),'utf8'),context,{filename:file});
    }
    context.store.state={...context.store.state,user:data.user,currentRole:data.user.role,data,framework,admin,registrationCatalog,languageChosen:true};
    const evaluate=expression=>vm.runInContext(expression,context);
    for(const activeView of ['learner-dash','framework','assessment','recommendations','learning-path','okrs','reports','profile','ai-generator','admin-dash']){
        context.store.state.activeView=activeView;
        const rendered=evaluate('renderImportedView()');
        assert(rendered.includes('<h1'),`Missing heading in ${activeView}`);
        assert(!/\b(undefined|NaN)\b/.test(rendered),`Invalid data in ${activeView}`);
        assert(!/MOCK_DATA|Groq|FRAC|82% Score|6% Improvement/.test(rendered),`Demo content in ${activeView}`);
    }
    context.store.state.data.overall_score=0;
    assert.equal(evaluate('importedState().overallScore'),0,'A genuine zero must not become a sample score');
    context.store.state.data.overall_score=null;
    assert(evaluate('renderLearnerDashboard(importedState())').includes('Not assessed'));
    context.store.state.data.user.name='<img src=x onerror=alert(1)>';
    assert(!evaluate('renderLearnerDashboard(importedState())').includes('<img src=x'),'Profile must be escaped');
    assert(!evaluate("formatAiText('<img src=x onerror=alert(1)>')").includes('<img'),'Model text must be escaped');
    context.store.state.chatMessages=[{sender:'ai',text:'Grounded answer',sources:[{doc_id:'safe-id',title:'Handbook <img src=x>'}]}];
    const chat=evaluate('renderAiAssistant(store.state)');
    assert(chat.includes('openUiSource'),'Citations must open source documents');
    assert(!chat.includes('<img src=x'),'Source titles must be escaped');
    context.store.state.session={id:'session',kind:'initial',answered:0,target:32,status:'active',preparation:{status:'failed',ready:3,total:48,error:'A source needs attention.'}};
    const preparation=evaluate('renderQuizPlayer(store.state)');
    assert(preparation.includes('Preparing two opening questions'));
    assert(!preparation.includes('of 48'));
    assert(preparation.includes('A source needs attention.'));
    assert.equal((preparation.match(/aria-label="Question \d+:/g)||[]).length,32);
    context.store.state.session={id:'session',kind:'initial',answered:1,target:30,status:'active',preparation:{status:'ready'},question:{id:'q2',position:2,deadline:Date.now()/1000+180,competency:'Survey design',question:'What is the next step?',options:['Plan','Guess','Ignore','Skip']}};
    const quiz=evaluate('renderQuizPlayer(store.state)');
    assert(quiz.includes('name="quizAnswer"'));
    assert(quiz.includes('id="questionTimer"'));
    assert(!quiz.includes('Continue assessment'));
    const calls=[];
    context.document.querySelector=()=>({value:'0'});
    context.store.notify=()=>{};
    context.store.api=async(route,body)=>{
        calls.push({route,body});
        if(route==='/api/quiz/answer')return {session:{...context.store.state.session,answered:2,question:{id:'q3',position:3,deadline:Date.now()/1000+180}}};
        return {job_id:'background-prepare'};
    };
    await context.store.submitAnswer();
    assert.deepEqual(calls.map(c=>c.route),['/api/quiz/answer','/api/quiz/prepare'],'The saved next question appears before rolling preparation starts');
    assert.equal(context.store.state.session.question.id,'q3');
    assert.equal(calls[0].body.question_id,'q2');
    console.log('PASS: 10 connected views, null/zero scores, escaped user/model/source text, source links, question timer and rolling answer handoff.');
}
main().catch(e=>{console.error(e);process.exitCode=1;});
