/**
 * User Profile Component — Block 1: Official Digital Competency Profile
 * Comprehensive profile displaying Personal/Professional, Educational, Experience, and Training records.
 */

function renderUserProfile(state) {
    const user = state.user || {};
    const defaultAvatar = null; // No legacy emblem — uses initial-based fallback below
    const avatar = user.profile_picture || user.avatar || defaultAvatar;
    const name = user.full_name || user.name || "Statistical Officer";
    const username = user.username ? `@${user.username}` : '';
    const cadre = user.administration_type || user.cadre || 'Official Statistical Cadre';
    const designation = (typeof user.designation === 'object' && user.designation)
        ? (user.designation.title || user.designation.name || 'Senior Statistical Officer (SSO)')
        : (String(user.designation || user.role || '').trim() === '[object Object]' || !(user.designation || user.role) ? 'Senior Statistical Officer (SSO)' : String(user.designation || user.role));
    const ministry = user.ministry || 'Not provided';
    const department = user.department || 'Not provided';
    const employeeId = user.government_id || user.employeeId || 'Not provided';
    const age = user.age || 'Not provided';
    const exp = user.experience !== '' && user.experience != null ? user.experience : 'Not provided';
    const degree = user.education || user.degree || 'Not provided';
    const spec = user.specialization || 'Not provided';
    const assignment = user.currentAssignment || user.projects || 'Not provided';
    const prevRoles = user.previousRoles || '';
    const domains = user.statisticalDomains || '';
    const projects = user.projectsHandled || '';
    const tools = user.technicalQualifications || '';
    const training = user.trainingProgrammes || '';
    const location = user.location || 'Not provided';
    const overallScore = state.overallScore;

    const toolList = typeof tools === 'string' ? tools.split(',').map(s => s.trim()).filter(Boolean) : (Array.isArray(tools) ? tools : []);
    const domainList = typeof domains === 'string' ? domains.split(',').map(s => s.trim()).filter(Boolean) : (Array.isArray(domains) ? domains : []);

    const certs = user.certifications || [];

    return `
    <div class="max-w-6xl mx-auto px-4 sm:px-8 py-8 space-y-8">
        <!-- Top Profile Banner Card -->
        <div class="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-200/80 shadow-md flex flex-col md:flex-row items-center gap-6 border-l-4 border-l-teal-500">
            <div class="w-24 h-24 rounded-2xl border-2 border-teal-500/80 overflow-hidden shadow-sm bg-navy-900 flex-shrink-0 flex items-center justify-center" style="background: #0B1B2B;">
                ${avatar ? `
                    <img src="${avatar}" alt="${name}" class="w-full h-full object-cover">
                ` : `
                    <span class="text-3xl font-black text-teal-300">${name.charAt(0).toUpperCase()}</span>
                `}
            </div>

            <div class="space-y-2 text-center md:text-left flex-1">
                <div class="flex flex-wrap items-center justify-center md:justify-start gap-2">
                    <h1 class="text-2xl font-black text-slate-900 tracking-tight font-heading">${name}</h1>
                    ${username ? `<span class="bg-teal-50 text-teal-800 border border-teal-200/80 text-xs font-mono font-bold px-2.5 py-0.5 rounded-full">${username}</span>` : ''}
                    <span class="bg-slate-100 text-slate-800 text-xs font-bold px-3 py-0.5 rounded-full border border-slate-200/80">
                        ${cadre}
                    </span>
                    <span class="bg-emerald-50 text-emerald-700 border-emerald-200/80 text-xs font-bold px-2.5 py-0.5 rounded-full border flex items-center gap-1">
                        <i class="fa-solid fa-circle-check text-emerald-600"></i> Saved Profile
                    </span>
                </div>
                <p class="text-xs sm:text-sm font-semibold text-slate-600">${designation} • ${department}</p>
                <div class="flex flex-wrap items-center justify-center md:justify-start gap-4 text-xs text-slate-500 pt-1">
                    <span><i class="fa-solid fa-id-badge text-teal-600"></i> <strong class="font-mono">${employeeId}</strong></span>
                    <span><i class="fa-solid fa-user-clock text-teal-600"></i> ${age === 'Not provided' ? 'Age not provided' : age + ' Years Old'}</span>
                    <span><i class="fa-solid fa-business-time text-teal-600"></i> ${exp} Years Experience</span>
                    <span><i class="fa-solid fa-graduation-cap text-teal-600"></i> ${degree}</span>
                </div>
            </div>

            <div class="flex flex-col items-center gap-4">
                <button onclick="openEditProfileModal()" class="btn btn-secondary text-xs"><i class="fa-solid fa-user-pen"></i> Edit Profile</button>
                <div class="p-4 bg-slate-50/80 border border-slate-200/80 rounded-2xl text-center min-w-[140px]">
                    <span class="text-[10px] font-bold text-slate-500 uppercase block">Competency Index</span>
                    <span class="text-3xl font-extrabold text-teal-700 font-heading">${overallScore == null ? 'Not assessed' : overallScore + '%'}</span>
                    <span class="text-[10px] text-teal-600 font-bold block mt-0.5">${overallScore == null ? 'Assessment pending' : 'Assessed Baseline'}</span>
                </div>
            </div>
        </div>

        <!-- 4 Grid Sections: Complete Block 1 Digital Competency Profile -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">

            <!-- Block 1.1: Personal / Professional Information -->
            <div class="stat-card p-6 space-y-4 bg-white border border-slate-200 rounded-3xl shadow-sm">
                <h2 class="text-base font-bold text-navy-900 flex items-center gap-2" style="color: #0B2545;">
                    <i class="fa-solid fa-building-columns text-orange-500"></i> 1. Personal & Professional Assignment
                </h2>

                <div class="space-y-3 text-xs">
                    <div class="p-3.5 bg-slate-50 rounded-xl border border-slate-100 space-y-1">
                        <span class="text-[10px] font-bold text-blue-700 uppercase">Ministry / Administration</span>
                        <div class="font-bold text-slate-800">${ministry || 'Ministry of Statistics & Programme Implementation'}</div>
                        <div class="text-slate-500">${department || 'National Statistical Office (NSO)'}</div>
                    </div>

                    <div class="p-3.5 bg-slate-50 rounded-xl border border-slate-100 space-y-1">
                        <span class="text-[10px] font-bold text-emerald-700 uppercase">Current Job Role & Cadre</span>
                        <div class="font-bold text-slate-800">${designation || 'Statistical Officer'}</div>
                        <div class="text-slate-500">Cadre: ${cadre} (${employeeId})</div>
                    </div>

                    <div class="p-3.5 bg-slate-50 rounded-xl border border-slate-100 space-y-1">
                        <span class="text-[10px] font-bold text-orange-700 uppercase">Current Survey / Analytical Assignment</span>
                        <div class="font-bold text-slate-800">${assignment || '<span class="text-slate-400 italic">Not yet specified (Click Edit Profile to add)</span>'}</div>
                        <div class="text-slate-500"><i class="fa-solid fa-location-dot"></i> Posting Location: ${location || '<span class="text-slate-400 italic">Not set</span>'}</div>
                    </div>
                </div>
            </div>

            <!-- Block 1.2: Educational & Technical Qualifications -->
            <div class="stat-card p-6 space-y-4 bg-white border border-slate-200 rounded-3xl shadow-sm">
                <h2 class="text-base font-bold text-navy-900 flex items-center gap-2" style="color: #0B2545;">
                    <i class="fa-solid fa-graduation-cap text-orange-500"></i> 2. Higher Education & Technical Qualifications
                </h2>

                <div class="space-y-3 text-xs">
                    <div class="p-3.5 bg-slate-50 rounded-xl border border-slate-100 space-y-1">
                        <span class="text-[10px] font-bold text-blue-700 uppercase">Higher Academic Degree & Specialization</span>
                        <div class="font-bold text-slate-800">${degree || '<span class="text-slate-400 italic">Not yet specified (Click Edit Profile)</span>'}</div>
                        <div class="text-slate-500">Specialization: ${spec || '<span class="text-slate-400 italic">General / Not specified</span>'}</div>
                    </div>

                    <div class="p-3.5 bg-slate-50 rounded-xl border border-slate-100 space-y-1.5">
                        <span class="text-[10px] font-bold text-purple-700 uppercase">Technical Qualifications & Software Tools</span>
                        ${toolList.length > 0 ? `
                            <div class="flex flex-wrap gap-1.5 pt-1">
                                ${toolList.map(t => `<span class="bg-purple-100 text-purple-800 text-[11px] font-bold px-2.5 py-1 rounded-md border border-purple-200">${t}</span>`).join('')}
                            </div>
                        ` : `
                            <div class="text-slate-400 italic">No tools recorded yet (Click Edit Profile to add)</div>
                        `}
                    </div>

                    <div class="p-3.5 bg-slate-50 rounded-xl border border-slate-100 space-y-1">
                        <span class="text-[10px] font-bold text-emerald-700 uppercase">Statistical Computing Competency</span>
                        <div class="text-slate-700 font-medium">View My skills for your saved assessment results.</div>
                    </div>
                </div>
            </div>

            <!-- Block 1.3: Experience & Statistical Domains -->
            <div class="stat-card p-6 space-y-4 bg-white border border-slate-200 rounded-3xl shadow-sm">
                <h2 class="text-base font-bold text-navy-900 flex items-center gap-2" style="color: #0B2545;">
                    <i class="fa-solid fa-briefcase text-orange-500"></i> 3. Experience & Statistical Domains
                </h2>

                <div class="space-y-3 text-xs">
                    <div class="p-3.5 bg-slate-50 rounded-xl border border-slate-100 space-y-1">
                        <span class="text-[10px] font-bold text-emerald-700 uppercase">Service Experience</span>
                        <div class="font-bold text-slate-800">${exp !== null ? exp + ' Years in Official Statistical System' : '<span class="text-slate-400 italic">Years of experience not set</span>'}</div>
                        <div class="text-slate-500">Previous Positions: ${prevRoles || '<span class="text-slate-400 italic">None recorded</span>'}</div>
                    </div>

                    <div class="p-3.5 bg-slate-50 rounded-xl border border-slate-100 space-y-1.5">
                        <span class="text-[10px] font-bold text-blue-700 uppercase">Statistical Domains Worked In</span>
                        ${domainList.length > 0 ? `
                            <div class="flex flex-wrap gap-1.5 pt-1">
                                ${domainList.map(d => `<span class="bg-blue-100 text-blue-800 text-[11px] font-bold px-2.5 py-1 rounded-md border border-blue-200">${d}</span>`).join('')}
                            </div>
                        ` : `
                            <div class="text-slate-400 italic">No statistical domains recorded yet</div>
                        `}
                    </div>

                    <div class="p-3.5 bg-slate-50 rounded-xl border border-slate-100 space-y-1">
                        <span class="text-[10px] font-bold text-orange-700 uppercase">Key Surveys / Projects Handled</span>
                        <div class="font-bold text-slate-800">${projects || '<span class="text-slate-400 italic">No surveys/projects listed yet</span>'}</div>
                    </div>
                </div>
            </div>

            <!-- Block 1.4: Training History & Continuous Learning -->
            <div class="stat-card p-6 space-y-4 bg-white border border-slate-200 rounded-3xl shadow-sm">
                <h2 class="text-base font-bold text-navy-900 flex items-center gap-2" style="color: #0B2545;">
                    <i class="fa-solid fa-award text-orange-500"></i> 4. Prior Training History & Academies
                </h2>

                <div class="space-y-3 text-xs">
                    <div class="p-3.5 bg-slate-50 rounded-xl border border-slate-100 space-y-1">
                        <span class="text-[10px] font-bold text-blue-700 uppercase">Training Academies / Pre-Training Attended</span>
                        <div class="font-bold text-slate-800">${training || '<span class="text-slate-400 italic">No pre-training recorded (Click Edit Profile to add)</span>'}</div>
                        <div class="text-slate-500"><i class="fa-solid fa-clock"></i> Training hours: ${user.learningHours == null ? 'Not recorded' : user.learningHours + ' hrs'}</div>
                    </div>

                    <div class="space-y-2 pt-1">
                        <span class="text-[10px] font-bold text-slate-500 uppercase block">Verified Certifications:</span>
                        ${certs.length > 0 ? certs.map(c => `
                            <div class="p-2.5 rounded-xl border border-slate-200 bg-white flex justify-between items-center">
                                <div>
                                    <div class="font-bold text-navy-900 text-xs">${c.title}</div>
                                    <div class="text-[10px] text-slate-500">${c.issuer} • ${c.year}</div>
                                </div>
                                <span class="badge badge-success text-[10px] px-2 py-0.5">Verified</span>
                            </div>
                        `).join('') : `
                            <div class="p-3 bg-slate-50 rounded-xl border border-slate-100 text-slate-400 italic text-center">
                                No certifications recorded yet.
                            </div>
                        `}
                    </div>
                </div>
            </div>
        </div>

        <!-- Edit Profile Modal Container -->
        <div id="editProfileModalContainer"></div>
    </div>
    `;
}

window.openEditProfileModal = function(overrideUser) {
    const storeUser = (window.store && window.store.state && window.store.state.user) || {};
    const user = overrideUser || storeUser;
    const desigVal = (typeof user.designation === 'object' && user.designation)
        ? (user.designation.title || user.designation.name || 'Senior Statistical Officer (SSO)')
        : (String(user.designation || user.role || '').trim() === '[object Object]' || !(user.designation || user.role) ? 'Senior Statistical Officer (SSO)' : String(user.designation || user.role));
    const exp = (user.experienceYears !== undefined && user.experienceYears !== null) ? user.experienceYears : ((user.experience_years !== undefined && user.experience_years !== null) ? user.experience_years : '');
    const degree = user.degree || "";
    const spec = user.specialization || "";
    const domains = user.statisticalDomains || user.statistical_domains || "";
    const tools = user.technicalQualifications || user.technical_qualifications || "";
    const prevRoles = user.previousRoles || user.previous_roles || "";
    const training = user.trainingProgrammes || user.training_programmes || "";
    const assignment = user.currentAssignment || user.current_assignment || "";
    const location = user.location || "";
    const projects = user.projectsHandled || user.projects_handled || "";

    const catalog=store.state.registrationCatalog;
    const selectedArea=user.assessment_area||'';
    const selectedRole=user.assessment_role_id||'';
    const currentMinistry=catalog?.ministries.some(m=>m.name===user.ministry)?user.ministry:'';
    const allMinistries=(catalog?.ministries||[]).map(m=>m.name);
    const selectedAreas=(catalog?.areas||[]).filter(a=>a.ministry===currentMinistry);
    const allDepts=selectedAreas.map(a=>a.name);
    const allDesignations=(selectedAreas.find(a=>a.id===selectedArea)?.roles||[]).map(r=>r.title);

    const modalHTML = `
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in overflow-y-auto">
        <div class="bg-white rounded-3xl max-w-2xl w-full p-6 sm:p-8 space-y-6 shadow-2xl border border-slate-200 my-8">
            <div class="flex items-center justify-between border-b border-slate-100 pb-4">
                <div class="flex items-center gap-2.5">
                    <div class="w-10 h-10 rounded-xl bg-orange-600 text-white flex items-center justify-center font-bold text-base shadow">
                        <i class="fa-solid fa-user-pen"></i>
                    </div>
                    <div>
                        <h2 class="text-lg font-black text-navy-900" style="color: #0B2545;">Edit Digital Competency Profile</h2>
                        <p class="text-xs text-slate-500">Block 1 — Official Cadre Records & Experience</p>
                    </div>
                </div>
                <button onclick="closeEditProfileModal()" class="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-500 flex items-center justify-center font-bold cursor-pointer">
                    ✕
                </button>
            </div>

            <div class="space-y-4 max-h-[65vh] overflow-y-auto pr-2 text-xs">
                <!-- Cadre Section with Unlock Toggle -->
                <div class="p-3.5 ${window.isModalCadreUnlocked ? 'bg-blue-50/50 border-blue-300' : 'bg-slate-50/80 border-slate-200'} rounded-2xl border space-y-3 transition-all">
                    <div class="flex items-center justify-between border-b ${window.isModalCadreUnlocked ? 'border-blue-200' : 'border-slate-200'} pb-2">
                        <div>
                            <h3 class="font-bold ${window.isModalCadreUnlocked ? 'text-blue-900' : 'text-slate-800'} text-xs flex items-center gap-2">
                                <i class="fa-solid fa-id-card text-blue-600"></i> Official Cadre Information
                            </h3>
                            <p class="text-[10px] text-slate-500">Ministry, Department, and Designation</p>
                        </div>
                        <button type="button" onclick="toggleModalCadreUnlock()" class="text-[11px] font-bold ${window.isModalCadreUnlocked ? 'text-emerald-700 bg-emerald-50 hover:bg-emerald-100 border-emerald-300' : 'text-blue-700 bg-blue-50 hover:bg-blue-100 border-blue-300'} px-3 py-1.5 rounded-lg border transition-all cursor-pointer inline-flex items-center gap-1.5 shadow-sm">
                            <i class="fa-solid ${window.isModalCadreUnlocked ? 'fa-check' : 'fa-user-pen'}"></i>
                            ${window.isModalCadreUnlocked ? 'Done Editing' : 'Edit Profile'}
                        </button>
                    </div>

                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <div>
                            <label for="modal_prof_name" class="font-bold ${window.isModalCadreUnlocked ? 'text-blue-900' : 'text-slate-700'} block mb-1">Official Name</label>
                            <div class="relative">
                                <input type="text" id="modal_prof_name" value="${esc(user.name || '')}" ${window.isModalCadreUnlocked ? '' : 'disabled'} class="w-full p-2.5 border rounded-lg font-semibold ${window.isModalCadreUnlocked ? 'bg-white border-blue-400 text-slate-900 focus:ring-2 focus:ring-blue-500 shadow-sm pr-10' : 'bg-slate-100/90 border-slate-200 text-slate-800 cursor-not-allowed select-none'}" placeholder="e.g. Dr. Rajesh Sharma" maxlength="150" autocomplete="name">
                                <span class="absolute right-3 top-2.5 ${window.isModalCadreUnlocked ? 'text-blue-600' : 'text-slate-400'}"><i class="fa-solid ${window.isModalCadreUnlocked ? 'fa-user-pen' : 'fa-lock'} text-xs"></i></span>
                            </div>
                        </div>
                        <div>
                            <label class="font-bold ${window.isModalCadreUnlocked ? 'text-blue-900' : 'text-slate-700'} block mb-1">Ministry / Administration</label>
                            ${window.isModalCadreUnlocked ? `
                                <select id="modal_prof_ministry" onchange="onModalMinistryChange()" class="w-full p-2.5 bg-white border-blue-400 text-slate-900 font-bold focus:ring-2 focus:ring-blue-500 border rounded-lg shadow-sm">
                                    <option value="">Choose your ministry</option>${allMinistries.map(m => `<option value="${esc(m)}" ${m.toLowerCase() === currentMinistry.toLowerCase() ? 'selected' : ''}>${esc(m)}</option>`).join('')}
                                </select>
                            ` : `
                                <input type="text" id="modal_prof_ministry" value="${esc(currentMinistry)}" disabled class="w-full p-2.5 bg-slate-100/90 border border-slate-200 text-slate-700 font-semibold cursor-not-allowed select-none rounded-lg">
                            `}
                        </div>
                        <div>
                            <label class="font-bold ${window.isModalCadreUnlocked ? 'text-blue-900' : 'text-slate-700'} block mb-1">Department / Division</label>
                            ${window.isModalCadreUnlocked ? `
                                <select id="modal_prof_dept" disabled class="w-full p-2.5 bg-white border-blue-400 text-slate-900 font-bold focus:ring-2 focus:ring-blue-500 border rounded-lg shadow-sm">
                                    ${allDepts.map(d => `<option value="${esc(d)}" ${d.toLowerCase() === String(user.department || '').toLowerCase() ? 'selected' : ''}>${esc(d)}</option>`).join('')}
                                </select>
                            ` : `
                                <input type="text" id="modal_prof_dept" value="${esc(user.department || '')}" disabled class="w-full p-2.5 bg-slate-100/90 border border-slate-200 text-slate-700 font-semibold cursor-not-allowed select-none rounded-lg">
                            `}
                        </div>
                        <div>
                            <label class="font-bold ${window.isModalCadreUnlocked ? 'text-blue-900' : 'text-slate-700'} block mb-1">Designation / Role</label>
                            ${window.isModalCadreUnlocked ? `
                                <select id="modal_prof_desig" disabled class="w-full p-2.5 bg-white border-blue-400 text-slate-900 font-bold focus:ring-2 focus:ring-blue-500 border rounded-lg shadow-sm">
                                    ${allDesignations.map(des => `<option value="${esc(des)}" ${des === desigVal ? 'selected' : ''}>${esc(des)}</option>`).join('')}
                                </select>
                            ` : `
                                <input type="text" id="modal_prof_desig" value="${esc(desigVal)}" disabled class="w-full p-2.5 bg-slate-100/90 border border-slate-200 text-slate-700 font-semibold cursor-not-allowed select-none rounded-lg">
                            `}
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                    <div><label for="modal_prof_area" class="font-bold text-slate-700 block mb-1">Work area *</label><select id="modal_prof_area" onchange="changeProfileWorkArea()" class="w-full p-2.5 border border-slate-300 rounded-lg"><option value="">Choose your work area</option>${selectedAreas.map(a=>`<option value="${esc(a.id)}" ${a.id===selectedArea?'selected':''}>${esc(a.name)}</option>`).join('')}</select></div>
                    <div><label for="modal_prof_role" class="font-bold text-slate-700 block mb-1">Designation *</label><select id="modal_prof_role" onchange="changeProfileWorkRole()" class="w-full p-2.5 border border-slate-300 rounded-lg"><option value="">Choose your designation</option>${(catalog?.areas.find(a=>a.id===selectedArea)?.roles||[]).map(r=>`<option value="${esc(r.id)}" ${r.id===selectedRole?'selected':''}>${esc(r.title)}</option>`).join('')}</select></div>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3.5 pt-1">
                    <div>
                        <label class="font-bold text-slate-700 block mb-1">Location of Workplace / Posting Office <span class="text-red-500">*</span></label>
                        <input type="text" id="modal_prof_location" value="${esc(location)}" class="w-full p-2.5 bg-white border border-slate-300 rounded-lg text-slate-800 font-medium" placeholder="e.g. Sankhyiki Bhawan, New Delhi or Regional Office">
                    </div>
                    <div class="sm:col-span-1">
                        <label class="font-bold text-slate-700 block mb-1">Current Survey & Statistical Assignment <span class="text-red-500">*</span></label>
                        <input type="text" id="modal_prof_assignment" value="${esc(assignment)}" class="w-full p-2.5 bg-white border border-slate-300 rounded-lg text-slate-800 font-medium" placeholder="e.g. Periodic Labour Force Survey (PLFS), National Accounts">
                    </div>
                    <div>
                        <label class="font-bold text-slate-700 block mb-1">Higher Education / Academic Degree <span class="text-red-500">*</span></label>
                        <input type="text" id="modal_prof_degree" value="${esc(degree)}" class="w-full p-2.5 bg-white border border-slate-300 rounded-lg text-slate-800 font-medium" placeholder="e.g. M.Sc. Statistics, M.A. Economics, Ph.D.">
                    </div>
                    <div>
                        <label class="font-bold text-slate-700 block mb-1">Specialization / Subject Area</label>
                        <input type="text" id="modal_prof_spec" value="${esc(spec)}" class="w-full p-2.5 bg-white border border-slate-300 rounded-lg text-slate-800 font-medium" placeholder="e.g. Mathematical Statistics, Sampling, Econometrics">
                    </div>
                    <div>
                        <label class="font-bold text-slate-700 block mb-1">Years of Experience in Official Statistics <span class="text-red-500">*</span></label>
                        <input type="number" step="0.5" id="modal_prof_exp" value="${esc(exp)}" class="w-full p-2.5 bg-white border border-slate-300 rounded-lg text-slate-800 font-medium" placeholder="e.g. 4">
                    </div>
                    <div>
                        <label class="font-bold text-slate-700 block mb-1">Previous Roles / Cadres</label>
                        <input type="text" id="modal_prof_prevRoles" value="${esc(prevRoles)}" class="w-full p-2.5 bg-white border border-slate-300 rounded-lg text-slate-800 font-medium" placeholder="e.g. Statistical Investigator, Junior Statistical Officer">
                    </div>
                    <div class="sm:col-span-2">
                        <label class="font-bold text-slate-700 block mb-1">Statistical Domains Worked In</label>
                        <input type="text" id="modal_prof_domains" value="${esc(domains)}" class="w-full p-2.5 bg-white border border-slate-300 rounded-lg text-slate-800 font-medium" placeholder="e.g. Survey Design, Sampling, National Accounts, Price Indices">
                    </div>
                    <div class="sm:col-span-2">
                        <label class="font-bold text-slate-700 block mb-1">Key Surveys / Projects Handled</label>
                        <input type="text" id="modal_prof_projects" value="${esc(projects)}" class="w-full p-2.5 bg-white border border-slate-300 rounded-lg text-slate-800 font-medium" placeholder="e.g. Periodic Labour Force Survey (PLFS), Consumer Expenditure Survey">
                    </div>
                    <div class="sm:col-span-2">
                        <label class="font-bold text-slate-700 block mb-1">Software & Analytical Tools Known</label>
                        <input type="text" id="modal_prof_tools" value="${esc(tools)}" class="w-full p-2.5 bg-white border border-slate-300 rounded-lg text-slate-800 font-medium" placeholder="e.g. Python, R, SPSS, SQL, PowerBI, Excel">
                    </div>
                    <div class="sm:col-span-2">
                        <label class="font-bold text-slate-700 block mb-1">Pre-Training / Academies Attended</label>
                        <input type="text" id="modal_prof_training" value="${esc(training)}" class="w-full p-2.5 bg-white border border-slate-300 rounded-lg text-slate-800 font-medium" placeholder="e.g. NSSTA Greater Noida, ISI Kolkata, iGOT Karmayogi, or None">
                    </div>
                </div>
            </div>

            <div class="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
                <button onclick="closeEditProfileModal()" class="btn btn-secondary text-xs py-2.5 px-5">Cancel</button>
                <button onclick="saveModalProfile()" class="btn btn-primary text-xs py-2.5 px-6">
                    <i class="fa-solid fa-floppy-disk"></i> Save Profile
                </button>
            </div>
        </div>
    </div>
    `;

    const container = document.getElementById('editProfileModalContainer');
    if (container) {
        container.innerHTML = modalHTML;
        container.querySelectorAll('input[id],select[id]').forEach(el=>{const label=el.closest('div')?.querySelector('label')||el.parentElement?.parentElement?.querySelector('label');if(label)label.htmlFor=el.id;});
    }
};

window.isModalCadreUnlocked = false;

window.toggleModalCadreUnlock = function() {
    const locVal = document.getElementById('modal_prof_location')?.value;
    const assignVal = document.getElementById('modal_prof_assignment')?.value;
    const degVal = document.getElementById('modal_prof_degree')?.value;
    const specVal = document.getElementById('modal_prof_spec')?.value;
    const toolsVal = document.getElementById('modal_prof_tools')?.value;
    const expVal = document.getElementById('modal_prof_exp')?.value;
    const prevRolesVal = document.getElementById('modal_prof_prevRoles')?.value;
    const domainsVal = document.getElementById('modal_prof_domains')?.value;
    const projVal = document.getElementById('modal_prof_projects')?.value;
    const trainVal = document.getElementById('modal_prof_training')?.value;

    const nameVal = document.getElementById('modal_prof_name')?.value;
    const minVal = document.getElementById('modal_prof_ministry')?.value;
    const deptVal = document.getElementById('modal_prof_dept')?.value;
    const desigVal = document.getElementById('modal_prof_desig')?.value;

    window.isModalCadreUnlocked = !window.isModalCadreUnlocked;

    const baseUser = (window.store && window.store.state && window.store.state.user) || {};
    const mergedUser = Object.assign({}, baseUser, {
        name: (nameVal !== undefined && nameVal !== '') ? nameVal : baseUser.name,
        ministry: (minVal !== undefined && minVal !== '') ? minVal : baseUser.ministry,
        department: (deptVal !== undefined && deptVal !== '') ? deptVal : baseUser.department,
        designation: (desigVal !== undefined && desigVal !== '') ? desigVal : baseUser.designation,
        location: locVal !== undefined ? locVal : baseUser.location,
        currentAssignment: assignVal !== undefined ? assignVal : baseUser.currentAssignment,
        degree: degVal !== undefined ? degVal : baseUser.degree,
        specialization: specVal !== undefined ? specVal : baseUser.specialization,
        technicalQualifications: toolsVal !== undefined ? toolsVal : baseUser.technicalQualifications,
        experienceYears: expVal !== undefined ? expVal : baseUser.experienceYears,
        previousRoles: prevRolesVal !== undefined ? prevRolesVal : baseUser.previousRoles,
        statisticalDomains: domainsVal !== undefined ? domainsVal : baseUser.statisticalDomains,
        projectsHandled: projVal !== undefined ? projVal : baseUser.projectsHandled,
        assessment_area: document.getElementById('modal_prof_area')?.value||'',
        assessment_role_id: document.getElementById('modal_prof_role')?.value||'',
        trainingProgrammes: trainVal !== undefined ? trainVal : baseUser.trainingProgrammes
    });

    window.openEditProfileModal(mergedUser);
};

window.closeEditProfileModal = function() {
    window.isModalCadreUnlocked = false;
    const container = document.getElementById('editProfileModalContainer');
    if (container) container.innerHTML = '';
};

window.onModalMinistryChange = function() {
    const minSelect = document.getElementById('modal_prof_ministry');
    const deptSelect = document.getElementById('modal_prof_dept');
    if (!minSelect || !deptSelect) return;
    const areas=(store.state.registrationCatalog?.areas||[]).filter(a=>a.ministry===minSelect.value);
    document.getElementById('modal_prof_area').innerHTML='<option value="">Choose your work area</option>'+areas.map(a=>`<option value="${esc(a.id)}">${esc(a.name)}</option>`).join('');
    window.changeProfileWorkArea();

};

window.saveModalProfile = async function() {
    const fields={area:'assessment_area',role:'assessment_role_id',name:'name',ministry:'ministry',dept:'department',desig:'designation',location:'location',assignment:'currentAssignment',degree:'degree',spec:'specialization',exp:'experienceYears',prevRoles:'previousRoles',domains:'statisticalDomains',projects:'projectsHandled',tools:'technicalQualifications',training:'trainingProgrammes'};
    const payload={};for(const [id,key] of Object.entries(fields))payload[key]=document.getElementById('modal_prof_'+id)?.value.trim()||'';
    if(['assessment_area','assessment_role_id','name','location','currentAssignment','degree','experienceYears','statisticalDomains'].some(key=>payload[key]==='')){alert('Please complete the required profile fields.');return;}
    const button=document.querySelector('[onclick="saveModalProfile()"]');
    if(button?.disabled)return;
    if(button)button.disabled=true;
    try {
        await store.api('/api/profile/update',payload);
        await store.hydrate();
        window.closeEditProfileModal();
        store.state.notice='Profile saved.';store.notify();
    } catch(error) {
        const container=document.getElementById('editProfileModalContainer');
        if(container){let message=container.querySelector('[role="alert"]');if(!message){message=document.createElement('p');message.setAttribute('role','alert');message.className='text-sm text-rose-700';button?.parentElement?.prepend(message);}message.textContent=error.message;}
    } finally {if(button)button.disabled=false;}
};
window.renderUserProfile = renderUserProfile;

window.changeProfileWorkArea=function(){
    const area=store.state.registrationCatalog.areas.find(a=>a.id===document.getElementById('modal_prof_area').value);
    const department=document.getElementById('modal_prof_dept');
    if(department.tagName==='SELECT')department.innerHTML=`<option value="${esc(area?.name||'')}">${esc(area?.name||'')}</option>`;else department.value=area?.name||'';
    const designation=document.getElementById('modal_prof_desig');if(designation.tagName==='SELECT')designation.innerHTML='<option value=""></option>';else designation.value='';
    document.getElementById('modal_prof_role').innerHTML='<option value="">Choose your designation</option>'+(area?.roles||[]).map(r=>`<option value="${esc(r.id)}">${esc(r.title)}</option>`).join('');
};
window.changeProfileWorkRole=function(){
    const area=store.state.registrationCatalog.areas.find(a=>a.id===document.getElementById('modal_prof_area').value);
    const role=area?.roles.find(r=>r.id===document.getElementById('modal_prof_role').value);
    if(role){const designation=document.getElementById('modal_prof_desig');if(designation.tagName==='SELECT')designation.innerHTML=`<option value="${esc(role.title)}">${esc(role.title)}</option>`;else designation.value=role.title;}
};
