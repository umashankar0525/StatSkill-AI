/* Examination card and palette layout adapted from statskill-ai-v/quizPlayer.js.
 * Issued questions, deadlines, answers and results belong to the backend session.
 */
function renderQuizPlayer(state){
    const s=state.session;
    if(!s)return `<div class="max-w-7xl mx-auto p-8">${empty('Choose an assessment to begin.')}</div>`;
    if(s.result)return renderImportedResult(s.result);
    const q=s.question;
    return `<div class="max-w-7xl mx-auto px-4 sm:px-8 py-8 space-y-6">
        ${uiHeader(s.kind==='initial'?'Skill assessment':'Course assessment',`${s.answered} of ${s.target} answers saved`,'fa-clipboard-check')}
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div class="lg:col-span-8 stat-card p-6 sm:p-8 space-y-6">${q?`
                <div class="flex flex-wrap justify-between items-center gap-3 text-xs"><span class="text-teal-700 font-semibold bg-teal-50 px-3 py-1 rounded-lg">${esc(tr(q.competency))}</span><span id="questionTimer" aria-label="Time remaining" class="font-mono font-semibold text-navy-900">${timerLabel(q.deadline)}</span></div>
                <form onsubmit="event.preventDefault();store.submitAnswer()"><h2 class="text-base sm:text-lg font-bold text-navy-900 leading-relaxed">${q.position}. ${esc(q.question)}</h2><fieldset class="space-y-3 mt-6"><legend class="sr-only">${tr('Choose one answer')}</legend>${q.options.map((option,index)=>`<label class="assessment-option p-4 rounded-xl border border-slate-200 bg-slate-50/50 cursor-pointer transition-colors flex items-center gap-3 text-sm"><input type="radio" name="quizAnswer" value="${index}" ${state.busy?'disabled':''}><span class="w-7 h-7 rounded-full border border-slate-300 bg-white flex-shrink-0 flex items-center justify-center text-xs font-semibold" aria-hidden="true">${String.fromCharCode(65+index)}</span><span>${esc(option)}</span></label>`).join('')}</fieldset><div class="flex flex-wrap justify-between gap-3 pt-6 mt-6 border-t border-slate-100"><button type="button" class="btn btn-secondary" onclick="store.submitAnswer(true)" ${state.busy?'disabled':''}>${tr('Skip question')}</button><button class="btn btn-primary" ${state.busy?'disabled':''}>${tr('Submit answer')} <i class="fa-solid fa-arrow-right"></i></button></div></form>
            `:`<div class="text-center py-8" role="status"><i class="fa-solid fa-spinner fa-spin text-2xl text-teal-600" aria-hidden="true"></i><h2 class="font-semibold text-lg mt-4">${tr(s.answered>=s.target?'Evaluating your assessment…':'Preparing your assessment…')}</h2><p class="text-sm text-slate-500 mt-3">${s.answered>=s.target?evaluationMessage(s):s.answered?'Preparing the next question. Your saved answers are safe.':'Preparing two opening questions. Your timer starts with the first question.'}</p>${s.answered>=s.target?renderEvaluationProgress(s):''}${s.preparation?.error?`<p class="text-sm text-rose-700 mt-3" role="alert">${esc(s.preparation.error)}</p>`:''}${state.error?`<button class="btn btn-primary mt-4" onclick="store.run(()=>store.advance(),'')">${tr('Retry')}</button>`:''}</div>`}</div>
            <aside class="lg:col-span-4 space-y-6"><div class="stat-card p-6 space-y-4"><h2 class="text-base font-bold text-navy-900">Assessment progress</h2><div class="question-palette" aria-label="Question progress">${Array.from({length:s.target},(_,i)=>`<span class="${i<s.answered?'answered':''}" ${q&&i+1===q.position?'aria-current="step"':''} aria-label="Question ${i+1}: ${i<s.answered?'saved':q&&i+1===q.position?'current':'upcoming'}">${i+1}</span>`).join('')}</div><p class="text-xs text-slate-500 leading-relaxed">Saved answers are final. You can review them when the assessment is complete.</p></div><div class="stat-card p-5 text-xs text-slate-500">Each question has three minutes. Preparation time does not reduce your answer time.</div></aside>
        </div>
    </div>`;
}
function timerLabel(deadline){const seconds=Math.max(0,Math.ceil(deadline-Date.now()/1000));return `${Math.floor(seconds/60)}:${String(seconds%60).padStart(2,'0')} ${store.state.currentLanguage==='hi'?'शेष':'remaining'}`;}
function renderImportedResult(result){
    return `<div class="max-w-5xl mx-auto px-4 sm:px-8 py-8 space-y-6"><div class="stat-card p-6 sm:p-10 space-y-6 text-center"><div class="w-20 h-20 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center text-3xl mx-auto"><i class="fa-solid fa-award"></i></div><h1 class="text-3xl font-bold text-navy-900">${tr('Assessment results')}</h1><p class="text-sm text-slate-500">Your answers are saved. Use your results to plan what to learn next.</p><div class="grid grid-cols-2 gap-4"><div class="p-5 rounded-2xl bg-blue-50 border border-blue-200"><span class="text-xs text-blue-700">Score</span><strong class="block text-3xl text-blue-900 mt-2">${result.score_percent}%</strong></div><div class="p-5 rounded-2xl bg-emerald-50 border border-emerald-200"><span class="text-xs text-emerald-700">Correct answers</span><strong class="block text-3xl text-emerald-900 mt-2">${result.correct_count} / ${result.total}</strong></div></div><div class="flex flex-wrap justify-center gap-3">${uiButton('Learning advisor','store.navigate',['recommendations'])}${uiButton('My goals','store.navigate',['okrs'],true)}</div></div><div class="stat-card p-6 live-content"><h2>${tr('Skills for your role')}</h2>${renderTopicResults(result)}<h2>${tr('Answer review')}</h2>${result.review.map((q,i)=>`<details class="review-item"><summary>${i+1}. ${esc(q.question)} — ${q.correct?'Correct':'Incorrect / skipped'}</summary><p>Your answer: ${q.answer===null?'Skipped':esc(q.options[q.answer])}</p><p><strong>Correct answer:</strong> ${esc(q.correct_answer)}</p><p>${esc(q.explanation)}</p>${q.source_quote?`<blockquote>${esc(q.source_quote)}</blockquote>`:''}${sourceButtons(q.sources||[])}</details>`).join('')}</div></div>`;
}


function evaluationMessage(session){
    const progress=session.evaluation;
    return progress?`${progress.completed} of ${progress.total} topics evaluated. Your answers are saved.`:'Your answers are saved. Evaluating your topic levels…';
}
function resultLevel(level,levels={}){
    return level===null||level===undefined?tr('Not assessed'):`L${level}${levels[String(level)]?' — '+levels[String(level)]:''}`;
}
function renderTopicResults(result){
    return table(['Topic','Correct answers','Current level','Required level'],result.changes.map(c=>`<tr><td>${esc(tr(c.competency_name||competencyName(c.competency_id)))}</td><td>${c.correct_count===undefined?'—':`${c.correct_count} / ${c.evidence_count}`}</td><td>${esc(resultLevel(c.new_level,result.levels))}</td><td>${esc(resultLevel(c.required_level,result.levels))}</td></tr>`));
}
function renderEvaluationProgress(session){
    const p=session.evaluation;if(!p)return '';
    return `${p.topics?.length?`<div class="text-left mt-4">${renderTopicResults({changes:p.topics})}</div>`:''}${p.error?`<p class="text-sm text-rose-700 mt-3" role="alert">${esc(p.error)} Your completed topic evaluations are saved.</p>`:''}`;
}
