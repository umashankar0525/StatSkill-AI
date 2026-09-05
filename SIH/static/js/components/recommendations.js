/* Course-card layout adapted from statskill-ai-v/components/recommendations.js.
 * Catalogue, enrolment and recommendation reasons come from /api/overview.
 */
let courseSearch='';
function renderRecommendations(state){
    const courses=state.data.courses.filter(c=>`${c.title} ${c.description} ${c.competency}`.toLowerCase().includes(courseSearch.toLowerCase()));
    return `<div class="max-w-7xl mx-auto px-4 sm:px-8 py-8 space-y-8">
        ${uiHeader('Learning advisor','Find learning for your role and goals.','fa-compass')}
        <div class="stat-card p-5 space-y-3"><div class="flex flex-wrap justify-between items-center gap-3"><p class="text-sm">Recommendations use your assessed skill gaps. iGOT courses open on the iGOT website.</p>${uiButton('Personalise recommendations','refreshCourseRecommendations')}</div>${state.data.recommendations?.uncovered_skills?.length?`<p class="text-xs text-slate-500">No matching course in the current catalogue for: ${state.data.recommendations.uncovered_skills.map(esc).join(', ')}.</p>`:''}<p class="text-xs text-slate-500">Course links come from published iGOT listings. Availability, enrolment and completion are managed by iGOT.</p></div>
        <form class="flex flex-wrap gap-3 items-end bg-white p-4 rounded-xl border border-slate-200" onsubmit="event.preventDefault();courseSearch=this.elements.search.value;store.notify()"><label class="flex-1 text-xs font-semibold text-slate-600">Search courses<input name="search" value="${esc(courseSearch)}" type="search" class="block w-full border border-slate-200 rounded-xl p-3 mt-2" placeholder="Search by title or skill"></label><button class="btn btn-primary">Search</button><span class="text-xs text-slate-500 py-3">${courses.length} courses</span></form>
        ${!courses.length?empty(state.data.courses.length?'No courses match your search.':'No courses have been published yet. Ask a trainer to upload and publish learning material.'):''}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" id="coursesGrid">${courses.map(course=>`
            <article class="stat-card overflow-hidden flex flex-col justify-between course-card">
                <div><div class="relative h-36 bg-navy-900 flex items-center justify-center"><i class="fa-solid fa-book-open text-5xl text-teal-400" aria-hidden="true"></i><span class="absolute top-3 right-3 bg-white/95 text-navy-900 px-2.5 py-1 rounded-lg text-xs font-semibold">${esc(course.enrolment_status||'Not enrolled')}</span></div>
                <div class="p-5 space-y-3"><span class="text-xs font-semibold text-teal-700">${esc(tr(course.competency))}</span><h2 class="text-lg font-bold text-navy-900">${esc(course.title)}</h2><p class="text-xs text-slate-600 leading-relaxed">${esc(course.description)}</p><details class="text-xs text-slate-600"><summary class="cursor-pointer font-semibold text-teal-700">Why this course?</summary><p class="mt-2">${esc(course.reason.replace('OKR','goal'))}</p></details></div></div>
                <div class="p-5 pt-0 course-actions">${courseActions(course)}</div>
            </article>`).join('')}</div>
    </div>`;
}
function refreshCourseRecommendations(){return store.run(async()=>{await store.job('/api/recommendations',{});await store.hydrate();},'Recommendations updated.');}
