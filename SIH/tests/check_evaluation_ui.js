const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const context=vm.createContext({console,Date,JSON,setTimeout:fn=>fn(),sessionStorage:{getItem:()=>''},localStorage:{getItem:()=>''},document:{},tr:x=>x,esc:x=>String(x).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;'),table:(headers,rows)=>headers.join('|')+rows.join(''),uiHeader:(heading,description)=>heading+description,uiButton:()=>'',competencyName:id=>id,sourceButtons:()=>''});
context.window=context;
for(const file of ['store.js','components/quizPlayer.js'])vm.runInContext(fs.readFileSync(path.join(__dirname,'../static/js',file),'utf8'),context);
const result={score_percent:25,correct_count:1,total:4,levels:{0:'No Demonstrated Foundation / Needs Foundational Support',1:'Foundational / Guided',3:'Practitioner / Analytical'},changes:[{competency_id:'C_SQL',competency_name:'SQL',new_level:0,required_level:1,correct_count:1,evidence_count:4}],review:[]};
context.result=result;
const html=vm.runInContext('renderImportedResult(result)',context);
for(const text of ['Topic','Correct answers','Current level','Required level','L0 — No Demonstrated Foundation / Needs Foundational Support','L1 — Foundational / Guided','1 / 4'])assert(html.includes(text),text);
context.session={kind:'initial',target:32,answered:32,evaluation:{completed:6,total:8,topics:result.changes,error:'Temporary <error>'}};
const pending=vm.runInContext('renderQuizPlayer({session,error:"retry"})',context);
assert(pending.includes('6 of 8 topics evaluated'));assert(pending.includes('SQL'));assert(pending.includes('Temporary &lt;error&gt;'));assert(!pending.includes('Temporary <error>'));
async function main(){
  context.store.state.session={id:'test',target:4,answered:4};
  context.store.api=async route=>route==='/api/quiz/submit'?{job_id:'test-job'}:route==='/api/jobs/test-job'?{job:{status:'failed',error:'Interrupted after saving'}}:{session:{id:'test',status:'complete',result}};
  const saved=await context.store.job('/api/quiz/submit',{session_id:'test'});
  assert.equal(saved.result,result);
  console.log('PASS: topic levels, required levels, saved topic progress, escaped errors and recovery of committed results.');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
