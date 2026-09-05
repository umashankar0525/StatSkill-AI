from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=root/'rag_engine.py';s=p.read_text(encoding='utf-8');start=s.index('def generate_mcq_with_llm(')
s=s[:start]+'''def generate_mcq_with_llm(context_text, competency_name, bloom_level_name, role_title, profile=None, previous=(), model_override=None):
    from soul_quiz_engine import generate_mcq
    return generate_mcq(context_text,competency_name,bloom_level_name,role_title,profile,previous,model_override)
''';p.write_text(s,encoding='utf-8')
# Remove the old on-demand question generator; inference only runs during preparation.
p=root/'quiz_service.py';s=p.read_text(encoding='utf-8');start=s.index('def prepare_draft(');end=s.index('def prepare_next(',start);s=s[:start]+s[end:];p.write_text(s,encoding='utf-8')
for filename in ['live_api.py','okr_service.py','static/js/components/framework.js']:
    p=root/filename;s=p.read_text(encoding='utf-8').replace('1<=level<=5','1<=level<=6').replace('1<=target<=5','1<=target<=6').replace('1–5','1–6').replace('1 to 5','1 to 6').replace('max="5"','max="6"');p.write_text(s,encoding='utf-8')
p=root/'static/js/components/learnerDash.js';s=p.read_text(encoding='utf-8').replace('max: 5','max: 6').replace('max:5','max:6');p.write_text(s,encoding='utf-8')
p=root/'static/js/store.js';s=p.read_text(encoding='utf-8');s=s.replace("const data=await this.api('/api/quiz/submit'", "const data=await this.job('/api/quiz/submit'")
s=s.replace("if(started.session)return started.session;", "if(started.session)return started.session;\n        if(!started.job_id)return started;")
s=s.replace('for(let i=0;i<400;i++){','for(let i=0;i<4800;i++){')
s=s.replace("if(job.status==='complete')return job.result;", "if(job.status==='complete')return job.result;\n            if(path==='/api/quiz/next'&&i%3===0){this.state.session=(await this.api('/api/quiz/'+body.session_id)).session;this.notify();}")
s=s.replace("if(current?.question&&current.answered+1<current.target){", "if(current?.question&&current.preparation?.status!=='ready'&&current.answered+1<current.target){")
s=s.replace("this.state.framework=await this.api('/api/framework');", "this.state.framework=await this.api('/api/framework');\n        this.state.registrationCatalog=await this.api('/api/registration/catalog');")
p.write_text(s,encoding='utf-8')
p=root/'static/js/components/quizPlayer.js';s=p.read_text(encoding='utf-8').replace("${tr('Preparing your next question…')}", "${tr(s.answered>=s.target?'Evaluating your assessment…':'Preparing your assessment…')}")
s=s.replace("${tr(s.answered?'Your next question is being prepared. Your answer has been saved.':'Your first question is being prepared.')}", "${s.answered>=s.target?'Your answers are saved. Your results will appear here.':s.preparation?`${s.preparation.ready} of ${s.preparation.total} questions ready. Your quiz starts when preparation is complete.`:'Preparing questions for a smooth assessment. Your timer starts with the first question.'}")
p.write_text(s,encoding='utf-8')
print('Wired local Soul generation, six-level evaluation, and prepared question selection.')
