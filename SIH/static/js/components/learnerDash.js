/**
 * Learner Dashboard Component
 * Imported dashboard, connected to authenticated backend evidence.
 * Features: 5 KPI Cards with trends, Competency Radar Chart (Current vs Required), Prioritized Skill Gaps list with direct action buttons.
 */

function renderLearnerDashboard(state) {
    const user = state.user || {};
    const lang = state.currentLanguage || 'en';
    const overallScore = state.overallScore;

    const userDesig = (typeof user.designation === 'object' && user.designation)
        ? (user.designation.title || user.designation.name || 'Not provided')
        : (String(user.designation || user.role || '').trim() === '[object Object]' || !(user.designation || user.role) ? 'Not provided' : String(user.designation || user.role));

    // Filter skill gaps from all competencies
    const allComps = [];
    (state.competencyFramework || []).forEach(domain => {
        (domain.competencies || []).forEach(comp => {
            if (comp.gap > 0) {
                allComps.push(comp);
            }
        });
    });

    // Sort by critical, high, moderate
    const priorityOrder = { "Critical": 1, "High": 2, "Moderate": 3, "None": 4 };
    allComps.sort((a, b) => (priorityOrder[a.priority] || 4) - (priorityOrder[b.priority] || 4));

    return `
    <div class="max-w-7xl mx-auto px-4 sm:px-8 py-8 space-y-8">
        <!-- Top Personalized Greeting Banner with Complete User Profile -->
        <div class="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-200/80 shadow-md flex flex-col md:flex-row md:items-center justify-between gap-6 border-l-4 border-l-teal-500">
            <div class="flex items-start sm:items-center gap-4 sm:gap-5 flex-1">
                <!-- Circular Profile Picture Preview -->
                <div class="relative w-16 h-16 sm:w-20 sm:h-20 rounded-2xl overflow-hidden bg-navy-900 border-2 border-teal-500/80 flex-shrink-0 shadow-sm flex items-center justify-center" style="background: #0B1B2B;">
                    ${(user.profile_picture || user.avatar) ? `
                        <img src="${user.profile_picture || user.avatar}" alt="${user.full_name || user.name}" class="w-full h-full object-cover">
                    ` : `
                        <span class="text-xl sm:text-2xl font-black text-teal-300">
                            ${(user.full_name || user.name || 'O').charAt(0).toUpperCase()}
                        </span>
                    `}
                </div>

                <div class="space-y-1.5 flex-1">
                    <div class="flex items-center gap-2 flex-wrap">
                        <span class="text-xs font-bold text-teal-800 bg-teal-50 border border-teal-200/60 px-2.5 py-0.5 rounded-full uppercase">
                            ${user.administration_type || 'Official Cadre'}
                        </span>
                        <span class="text-xs font-bold text-slate-700 bg-slate-100 border border-slate-200/80 px-2.5 py-0.5 rounded-full">
                            ${user.designation || userDesig}
                        </span>
                        <span class="text-xs font-mono text-slate-500 font-medium">
                            ID: ${user.government_id || user.employeeId || 'Not provided'}
                        </span>
                    </div>

                    <h1 class="text-xl sm:text-3xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2 flex-wrap font-heading">
                        <span>${(lang === 'hi' && user.hindiName) ? user.hindiName : ((lang === 'te' && user.teluguName) ? user.teluguName : (user.full_name || user.name || 'Officer'))}</span>
                        ${user.username ? `<span class="text-xs sm:text-sm font-mono font-normal text-teal-700 bg-teal-50 px-2 py-0.5 rounded-md">@${user.username}</span>` : ''}
                    </h1>

                    <p class="text-xs sm:text-sm text-slate-600 leading-relaxed">
                        <span class="font-semibold text-slate-800">${user.department || user.ministry || 'Not provided'}</span>
                        ${user.age ? ` • <span class="text-slate-500">${user.age} yrs</span>` : ''}
                        • <span class="text-slate-500">${user.experience ?? 'Not provided'} yrs cadre experience</span>
                    </p>

                    <div class="text-[11px] text-slate-500 flex items-center gap-2 flex-wrap pt-0.5">
                        <span><i class="fa-solid fa-graduation-cap text-teal-600"></i> ${user.education || user.degree || 'Not provided'}</span>
                        <span>•</span>
                        <span><i class="fa-solid fa-briefcase text-teal-600"></i> ${user.projects || user.projectsHandled || 'No responsibilities saved'}</span>
                    </div>
                </div>
            </div>

            <!-- Quick Action Buttons -->
            <div class="flex items-center gap-3 flex-wrap flex-shrink-0">
                <button onclick="store.navigate('assessment')" class="btn btn-primary text-xs sm:text-sm py-2.5 px-4 shadow-sm cursor-pointer">
                    <i class="fa-solid fa-clipboard-check text-teal-400"></i>
                    <span>Skill Assessment</span>
                </button>
                <button onclick="store.navigate('recommendations')" class="btn btn-teal text-xs sm:text-sm py-2.5 px-4 shadow-sm cursor-pointer">
                    <i class="fa-solid fa-compass"></i>
                    <span>Learning Paths</span>
                </button>
            </div>
        </div>

        <!-- 5 KPI Cards Row -->
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
            <!-- Overall Competency -->
            <div class="stat-card p-5 stat-card-highlight flex flex-col justify-between">
                <div>
                    <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">Overall Competency</span>
                    <div class="text-3xl font-black text-navy-900 mt-1" style="color: #0B2545;">${overallScore === null ? tr('Not assessed') : overallScore + '%'}</div>
                </div>
                <div class="mt-3 flex items-center text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded w-fit">
                    <i class="fa-solid fa-arrow-trend-up mr-1"></i> ${state.assessedCount} assessed skills
                </div>
            </div>

            <!-- Skill Gaps -->
            <div class="stat-card p-5 stat-card-saffron flex flex-col justify-between">
                <div>
                    <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">Skill Gaps</span>
                    <div class="text-3xl font-black text-orange-600 mt-1">${allComps.length}</div>
                </div>
                <div class="mt-3 flex items-center text-xs font-bold text-red-600 bg-red-50 px-2 py-1 rounded w-fit">
                    <i class="fa-solid fa-triangle-exclamation mr-1"></i> ${allComps.filter(c => c.priority === 'Critical').length} Critical Priority
                </div>
            </div>

            <!-- Learning Progress -->
            <div class="stat-card p-5 stat-card-green flex flex-col justify-between">
                <div>
                    <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">Learning Progress</span>
                    <div class="text-3xl font-black text-emerald-600 mt-1">${user.learningProgressPercent}%</div>
                </div>
                <div class="mt-3 w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                    <div class="bg-emerald-500 h-full rounded-full" style="width: ${user.learningProgressPercent}%;"></div>
                </div>
            </div>

            <!-- Active goals -->
            <div class="stat-card p-5 flex flex-col justify-between border-top-navy">
                <div>
                    <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">Active goals</span>
                    <div class="text-3xl font-black text-navy-900 mt-1" style="color: #0B2545;">${state.activeGoalCount}</div>
                </div>
                <div class="mt-3 text-xs font-semibold text-slate-500">
                    <i class="fa-solid fa-clock text-orange-500"></i> Your saved learning objectives
                </div>
            </div>

            <!-- Assessments Completed -->
            <div class="stat-card p-5 flex flex-col justify-between">
                <div>
                    <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">Assessments</span>
                    <div class="text-3xl font-black text-purple-700 mt-1">${user.assessmentsCompleted}</div>
                </div>
                <div class="mt-3 text-xs font-bold text-purple-700 bg-purple-50 px-2 py-1 rounded w-fit">
                    <i class="fa-solid fa-circle-check mr-1"></i> Completed and saved
                </div>
            </div>
        </div>

        <!-- Middle Section: Radar Chart & Prioritized Skill Gap List -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <!-- Left: Competency Radar Chart (Current vs Required) -->
            <div class="lg:col-span-5 stat-card p-6 space-y-4 flex flex-col justify-between">
                <div>
                    <div class="flex justify-between items-center mb-2">
                        <h2 class="text-lg font-bold text-navy-900" style="color: #0B2545;">
                            Competency Radar Profile
                        </h2>
                        <span class="text-xs text-slate-500 font-medium">${userDesig}</span>
                    </div>
                    <p class="text-xs text-slate-600">
                        Comparing your <strong>Current Capability</strong> against the <strong>Required Level</strong> for your role. Unassessed skills have no current score.
                    </p>
                </div>

                <!-- Radar Canvas Container -->
                <div class="relative h-64 w-full flex items-center justify-center py-2">
                    <canvas id="competencyRadarChart"></canvas>
                </div>

                <!-- Legend & Summary -->
                <div class="pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-semibold">
                    <div class="flex items-center gap-2">
                        <span class="w-3 h-3 rounded-full bg-blue-600 inline-block"></span>
                        <span class="text-slate-700">Current Level</span>
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="w-3 h-3 rounded-full bg-orange-500 inline-block"></span>
                        <span class="text-slate-700">Required Target</span>
                    </div>
                    <button onclick="store.navigate('framework')" class="text-blue-600 hover:underline text-[11px]">
                        Full Matrix <i class="fa-solid fa-chevron-right text-[9px]"></i>
                    </button>
                </div>
            </div>

            <!-- Right: Prioritized Skill Gaps List -->
            <div class="lg:col-span-7 stat-card p-6 space-y-4 flex flex-col justify-between">
                <div class="flex justify-between items-center">
                    <div>
                        <h2 class="text-lg font-bold text-navy-900" style="color: #0B2545;">
                            Identified Competency Gaps
                        </h2>
                        <p class="text-xs text-slate-600">
                            Based on your saved assessment results.
                        </p>
                    </div>
                    <button onclick="store.navigate('recommendations')" class="btn btn-secondary text-xs py-1.5 px-3">
                        <i class="fa-solid fa-sparkles text-orange-500"></i> Find learning
                    </button>
                </div>

                <!-- Gaps List -->
                <div class="space-y-2.5 max-h-[380px] overflow-y-auto pr-1">${!allComps.length ? empty(state.assessedCount ? "No assessed gaps found." : "Complete an assessment to discover your skill gaps.") : ""}
                    ${allComps.map(comp => {
                        let badgeClass = "gap-moderate";
                        let priorityIcon = "fa-circle-info";
                        if (comp.priority === "Critical") {
                            badgeClass = "gap-critical";
                            priorityIcon = "fa-circle-xmark";
                        } else if (comp.priority === "High") {
                            badgeClass = "gap-high";
                            priorityIcon = "fa-triangle-exclamation";
                        }

                        const levelLabels = {0:"L0 No demonstrated foundation",1:"L1 Foundational",2:"L2 Working",3:"L3 Practitioner",4:"L4 Advanced",5:"L5 Expert",6:"L6 Leadership"};

                        return `
                        <div class="p-3.5 rounded-xl border border-slate-200 bg-white hover:border-slate-300 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-sm">
                            <div class="space-y-1">
                                <div class="flex items-center gap-2">
                                    <span class="${badgeClass}">
                                        <i class="fa-solid ${priorityIcon}"></i> ${comp.priority}
                                    </span>
                                    <span class="text-xs font-bold text-navy-900" style="color: #0B2545;">${comp.name}</span>
                                    <span class="text-[10px] text-slate-500">(${comp.domain})</span>
                                </div>
                                <div class="text-xs text-slate-600 flex items-center gap-3 flex-wrap">
                                    <span>Current: <strong class="text-slate-800">${levelLabels[comp.currentLevel] || 'Not assessed'}</strong></span>
                                    <span class="text-slate-400">→</span>
                                    <span>Required level: <strong class="text-orange-700">${levelLabels[comp.requiredLevel]}</strong></span>
                                    <span class="text-slate-400">|</span>
                                    <span>Gap: <strong class="text-red-600">${comp.gap} Levels</strong></span>
                                </div>
                            </div>

                            <button onclick="store.navigate('recommendations')" class="btn btn-secondary text-xs py-1.5 px-3 whitespace-nowrap hover:bg-orange-50 hover:text-orange-700 hover:border-orange-200">
                                <i class="fa-solid fa-route text-orange-500"></i> View Learning Path
                            </button>
                        </div>
                        `;
                    }).join('')}
                </div>
            </div>
        </div>

        <!-- Bottom Section: Active Learning Path & Recent Assessment Summary -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <!-- Active Learning Path Progress -->
            <div class="lg:col-span-7 stat-card p-6 space-y-4">
                <div class="flex justify-between items-center">
                    <div>
                        <h2 class="text-lg font-bold text-navy-900" style="color: #0B2545;">
                            Your Recommended Learning Path
                        </h2>
                        <p class="text-xs text-slate-600">
                            Sequenced milestone modules to bridge your identified skill gaps.
                        </p>
                    </div>
                    <button onclick="store.navigate('learning-path')" class="text-xs font-bold text-blue-600 hover:underline">
                        View Full Roadmap <i class="fa-solid fa-chevron-right text-[9px]"></i>
                    </button>
                </div>

                <div class="space-y-3">
                    ${!state.learningPath.length ? empty("No courses yet. Explore the learning advisor.") : ""}
                    ${state.learningPath.slice(0, 3).map((item, idx) => `
                        <div class="p-3.5 rounded-xl border border-slate-200 bg-slate-50/70 hover:bg-white flex items-center justify-between gap-4 transition-all">
                            <div class="flex items-center gap-3">
                                <div class="w-8 h-8 rounded-lg bg-navy-900 text-white font-bold text-xs flex items-center justify-center" style="background: #0B2545;">
                                    0${idx + 1}
                                </div>
                                <div>
                                    <div class="text-xs font-bold text-navy-900">${item.title}</div>
                                    <div class="text-[11px] text-slate-500 flex items-center gap-2 mt-0.5">
                                        <span><i class="fa-regular fa-clock text-slate-400"></i> ${item.duration}</span>
                                        <span>•</span>
                                        <span class="text-orange-600 font-semibold">${item.source}</span>
                                        <span>•</span>
                                        <span class="bg-blue-100 text-blue-800 px-1.5 py-0.2 rounded text-[10px]">${item.competency}</span>
                                    </div>
                                </div>
                            </div>
                            <div class="flex items-center gap-3">
                                ${item.progress > 0 ? `
                                    <div class="text-right">
                                        <div class="text-xs font-bold text-emerald-600">${item.progress}%</div>
                                        <div class="text-[10px] text-slate-400">In Progress</div>
                                    </div>
                                ` : `
                                    <span class="text-xs text-slate-500 font-medium">Not Started</span>
                                `}
                                <button onclick="store.navigate('learning-path')" class="w-8 h-8 rounded-lg bg-white border border-slate-200 hover:bg-orange-50 hover:text-orange-600 flex items-center justify-center text-slate-600 text-xs">
                                    <i class="fa-solid fa-arrow-right"></i>
                                </button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>

            <!-- Saved assessment and objective summaries in the imported card layout. -->
            <div class="lg:col-span-5 stat-card p-6 space-y-4 bg-gradient-to-br from-white via-slate-50 to-blue-50/40">
                <h2 class="text-lg font-bold text-navy-900">Latest assessment</h2>
                ${renderRecentAssessment()}
                <div class="p-4 bg-gradient-to-br from-blue-50 to-indigo-50/60 border border-blue-200 rounded-2xl text-xs space-y-3">
                    <h3 class="font-bold text-navy-900">Your next step</h3>
                    <p>Build your skills with an assessment tailored to your work.</p>
                    <button onclick="store.startAssessment()" class="btn btn-primary" ${store.state.busy?'disabled':''}>${tr('Start my assessment')}</button>
                    <button onclick="store.navigate('okrs')" class="btn btn-secondary">${tr('My goals')}</button>
                </div>
            </div>
        </div>
    </div>`;
}

function initCompetencyRadarChart() {
    const ctx = document.getElementById('competencyRadarChart');
    if (!ctx) return;
    if (typeof Chart === 'undefined') {ctx.replaceWith(document.createTextNode('Open My skills to see your saved levels.')); return;}
    const gaps=store.state.data.gaps.slice(0,8);

    if (window.radarChartInstance) {
        window.radarChartInstance.destroy();
    }

    window.radarChartInstance = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: gaps.map(g=>tr(g.competency_name)),
            datasets: [
                {
                    label: tr('Assessed'),
                    data: gaps.map(g=>g.current_level),
                    fill: true,
                    backgroundColor: 'rgba(11, 37, 69, 0.2)',
                    borderColor: '#0B2545',
                    pointBackgroundColor: '#0B2545',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#0B2545',
                    borderWidth: 2
                },
                {
                    label: tr('Required'),
                    data: gaps.map(g=>g.required_level),
                    fill: true,
                    backgroundColor: 'rgba(234, 88, 12, 0.15)',
                    borderColor: '#EA580C',
                    pointBackgroundColor: '#EA580C',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#EA580C',
                    borderWidth: 2,
                    borderDash: [4, 4]
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            elements: {
                line: { tension: 0.2 }
            },
            scales: {
                r: {
                    angleLines: { color: 'rgba(0, 0, 0, 0.08)' },
                    grid: { color: 'rgba(0, 0, 0, 0.08)' },
                    suggestedMin: 0,
                    suggestedMax: 6,
                    ticks: {
                        stepSize: 1,
                        display: false
                    },
                    pointLabels: {
                        font: {
                            size: 11,
                            weight: '600',
                            family: 'Inter'
                        },
                        color: '#334155'
                    }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

window.renderLearnerDashboard = renderLearnerDashboard;
window.initCompetencyRadarChart = initCompetencyRadarChart;
