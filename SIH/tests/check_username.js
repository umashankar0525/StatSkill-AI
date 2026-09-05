/* Regression: typing and asynchronous username checks must not replace the form. */
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const input={classList:{remove(){},add(){}},setAttribute(){},nextElementSibling:{innerHTML:''}};
const feedback={},button={classList:{toggle(){}},style:{}};
let pending,notifications=0,response,resolveFetch;
const ctx=vm.createContext({console,document:{getElementById:id=>id==='regUsernameInput'?input:id==='usernameFeedback'?feedback:null,querySelector:()=>button},store:{notify(){notifications++;}},setTimeout:fn=>(pending=fn,1),clearTimeout(){},fetch:async()=>response,esc:String});
ctx.window=ctx;
vm.runInContext(fs.readFileSync(require('node:path').join(__dirname,'../static/js/components/authModal.js'),'utf8'),ctx);
const reply=(available)=>({ok:true,json:async()=>({success:true,available})});
(async()=>{
  for(const name of ['p','pr','pre','prev','preview.name'])ctx.handleUsernameInput(name);
  assert.equal(notifications,0,'Typing must not recreate or blur the input');
  assert.equal(button.disabled,true,'Disable next while checking');
  response=reply(true);await pending();assert.equal(button.disabled,false);assert.match(feedback.textContent,/available/);
  ctx.handleUsernameInput('taken.name');response=reply(false);await pending();assert.equal(button.disabled,true);assert.match(feedback.textContent,/already taken/);
  ctx.handleUsernameInput('failed.lookup');response={ok:false,json:async()=>({error:'Unknown API GET endpoint'})};await pending();assert.equal(button.disabled,true);assert.match(feedback.textContent,/Unable to check/);assert.doesNotMatch(feedback.textContent,/taken/);
  ctx.handleUsernameInput('malformed.reply');response={ok:true,json:async()=>({success:true})};await pending();assert.match(feedback.textContent,/Unable to check/);
  ctx.fetch=()=>new Promise(resolve=>resolveFetch=resolve);
  ctx.handleUsernameInput('old.username');const old=pending();
  ctx.handleUsernameInput('new.username');resolveFetch(reply(false));await old;
  assert.equal(ctx.authState.usernameStatus,null,'Ignore an earlier response after the input changes');
  ctx.fetch=async()=>reply(true);await pending();assert.equal(button.disabled,false);
  assert.equal(notifications,0,'Neither typing nor an availability response may replace the form');
  console.log('PASS: uninterrupted typing, available/taken results, server errors, malformed responses, and stale-response protection.');
})().catch(error=>{console.error(error);process.exitCode=1;});
