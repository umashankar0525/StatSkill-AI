/**
 * Personalized Learning Path Component
 * AI-generated phased learning roadmap with interactive milestone completion and timeline visualization.
 */

function renderLearningPath(state) {
    const pathItems = state.learningPath.filter(x=>x.enrolled);
    const completedCount = pathItems.filter(item => item.progress === 100).length;
    const totalCount = pathItems.length;
    const pathPercent = totalCount ? Math.round((completedCount / totalCount) * 100) : 0;

    return `
    <div class="max-w-5xl mx-auto px-4 sm:px-8 py-8 space-y-8">
        <!-- Header -->
        <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4 border-l-4 border-navy-900">
            <div>
                <span class="text-xs font-bold text-emerald-700 bg-emerald-100 px-3 py-1 rounded-full uppercase">
                    My learning journey
                </span>
                <h1 class="text-2xl sm:text-3xl font-black text-navy-900 mt-2" style="color: #0B2545;">
                    Your Recommended Learning Path
                </h1>
                <p class="text-xs sm:text-sm text-slate-600 max-w-2xl mt-1">
                    Continue your saved learning. iGOT course progress is managed on iGOT.
                </p>
            </div>

            <!-- Path Progress Badge -->
            <div class="p-4 bg-slate-50 border border-slate-200 rounded-xl text-center min-w-[140px]">
                <span class="text-xs text-slate-500 font-semibold block">Milestone Progress</span>
                <span class="text-2xl font-black text-navy-900" style="color: #0B2545;">${completedCount} / ${totalCount}</span>
                <span class="text-[10px] font-bold text-emerald-600 block mt-0.5">${pathPercent}% Completed</span>
            </div>
        </div>

        <!-- Phased Timeline View -->
        <div class="stat-card p-6 sm:p-10 space-y-8">
            <div class="roadmap-timeline space-y-8">
                ${!pathItems.length ? empty("No enrolled courses yet. Add a course from the learning advisor.") : ""}
                ${pathItems.map((item, idx) => {
                    const isCompleted = item.progress === 100;
                    const isInProgress = item.progress > 0 && item.progress < 100;
                    const nodeClass = isCompleted ? 'completed' : (isInProgress ? 'active' : '');

                    return `
                    <div class="roadmap-step">
                        <div class="roadmap-node ${nodeClass}"></div>
                        <div class="p-5 bg-white border border-slate-200 rounded-2xl shadow-sm hover:border-navy-900 transition-all space-y-3">
                            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
                                <div>
                                    <span class="text-[10px] font-bold text-orange-600 uppercase tracking-wide bg-orange-50 px-2 py-0.5 rounded border border-orange-200">${item.phase}</span>
                                    <h3 class="text-base font-bold text-navy-900 mt-1" style="color: #0B2545;">${item.title}</h3>
                                </div>
                                <div class="flex items-center gap-2 text-xs">
                                    <span class="bg-blue-100 text-blue-800 font-bold px-2 py-0.5 rounded">${item.competency}</span>
                                    <span class="bg-slate-100 text-slate-700 font-semibold px-2 py-0.5 rounded">${item.targetLevel}</span>
                                </div>
                            </div>

                            <!-- Metadata Row -->
                            <div class="flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500">
                                <div class="flex items-center gap-3">
                                    <span><i class="fa-regular fa-clock text-slate-400"></i> ${item.duration}</span>
                                    <span>•</span>
                                    <span><i class="fa-solid fa-building-columns text-slate-400"></i> ${item.provider}</span>
                                    <span>•</span>
                                    <span class="text-orange-600 font-semibold">${item.source}</span>
                                </div>

                                <div class="flex items-center gap-3">
                                    <span class="font-bold ${isCompleted ? 'text-emerald-600' : 'text-slate-700'}">
                                        ${item.progress}% Completed
                                    </span>
                                </div>
                            </div>

                            <!-- Progress Track -->
                            <div class="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                                <div class="bg-emerald-500 h-full rounded-full transition-all duration-300" style="width: ${item.progress}%;"></div>
                            </div>

                            <!-- Interactive Actions -->
                            <div class="pt-2 flex flex-wrap items-center justify-between gap-3">
                                <span class="text-xs font-semibold text-slate-600">${isCompleted ? 'Completed' : 'Complete the course assessment to record progress.'}</span>

                                <div class="flex items-center gap-2">
                                    ${courseActions(item.raw)}

                                </div>
                            </div>
                        </div>
                    </div>
                    `;
                }).join('')}
            </div>

            <!-- Footer Action -->
            <div class="p-4 bg-slate-50 border border-slate-200 rounded-2xl flex flex-col sm:flex-row items-center justify-between gap-4 text-xs">
                <div class="flex items-center gap-2 text-slate-700 font-medium">
                    <i class="fa-solid fa-circle-info text-blue-600 text-base"></i>
                    <span>Course completion is recorded after passing its assessment.</span>
                </div>
                <button onclick="store.navigate('recommendations')" class="btn btn-saffron text-xs py-2 px-4 whitespace-nowrap">
                    <i class="fa-solid fa-plus"></i> Add More Courses
                </button>
            </div>
        </div>
    </div>
    `;
}


window.renderLearningPath = renderLearningPath;
