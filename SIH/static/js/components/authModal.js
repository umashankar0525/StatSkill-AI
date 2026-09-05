/**
 * StatSkill AI — Minimalist 3-Stage Authentication & Registration System
 *
 * Design Language:
 * - Refined frosted glass modal surface inspired by Web3 & modern SaaS design
 * - 3-Stage Registration:
 *     01 Hierarchy & Profile (Personal & Professional Information + Profile Picture Upload)
 *     02 Create Username (Real-time live backend availability check)
 *     03 Security Password (Password strength meter & confirmation)
 * - Single-step Login (Username + Password)
 * - Zero OTP / SMS / CAPTCHA / phone verification
 * - Automatic session establishment & direct redirect to Dashboard
 */

(function(window) {
    'use strict';

    // State for Authentication Wizard
    let authState = {
        tab: 'login', // 'login' | 'register'
        step: 1,      // 1: Profile, 2: Username, 3: Password

        // Stage 1 Fields
        fullName: '',
        age: '',
        experience: '',
        governmentId: '',
        avatar: '',
        adminType: 'central', // 'central' | 'state'
        stateName: 'Delhi',
        ministry: '',
        department: '',
        designation: '',
        education: '',
        projects: '',

        // Stage 2 Fields
        username: '',
        isCheckingUsername: false,
        usernameStatus: null, // null | 'available' | 'taken' | 'invalid'
        usernameMessage: '',

        // Stage 3 Fields
        password: '',
        confirmPassword: '',
        passwordStrength: 0, // 0 to 4

        // Login Fields
        loginUsername: '',
        loginPassword: '',
        loginError: null,
        isLoggingIn: false,

        // General
        error: null,
        isSubmitting: false
    };

    window.authState = authState;
    window.rememberAuthFields = function() {
        const fields = {regFullName:'fullName',regAge:'age',regExperience:'experience',regGovernmentId:'governmentId',regEducation:'education',regProjects:'projects',loginUsernameInput:'loginUsername',loginPasswordInput:'loginPassword',regPassword:'password',regConfirmPassword:'confirmPassword'};
        for (const [id,key] of Object.entries(fields)) { const el=document.getElementById(id); if(el)authState[key]=el.value; }
    };
    async function acceptAccount(data) {
        if(!data.token)throw new Error('The server did not return a session.');
        store.token=data.token;sessionStorage.setItem('statskill_token',data.token);
        await store.hydrate();
        Object.assign(store.state,{isAuthModalOpen:false,activeView:'learner-dash',error:'',notice:''});
        Object.assign(authState,{password:'',confirmPassword:'',loginPassword:'',tab:'login',step:1});
        store.notify();
    }
    let checkUsernameDebounceTimer = null;
    const centralOptions=()=>store.state.registrationCatalog?.ministries||[];
    window.handleAssessmentArea=function(id){
        window.rememberAuthFields();authState.assessmentArea=id;authState.department=store.state.registrationCatalog?.areas.find(a=>a.id===id)?.name||'';authState.assessmentRole='';authState.designation='';reRenderModal();
    };
    window.handleAssessmentRole=function(id){
        const area=store.state.registrationCatalog?.areas.find(a=>a.id===authState.assessmentArea);
        const role=area?.roles.find(r=>r.id===id);authState.assessmentRole=id;authState.designation=role?.title||'';
    };


    // Reset or Open Modal
    window.openAuthModal = function(initialTab = 'login', initialStep = 1) {
        authState.tab = initialTab;
        store.state.authModalTab = initialTab;
        authState.step = initialStep;
        authState.error = null;
        authState.loginError = null;

        // Auto-seed default hierarchy options if empty
        if (!authState.ministry && centralOptions().length) {
            const firstMin = centralOptions()[0];
            authState.ministry = firstMin.name;
            if (firstMin.departments && firstMin.departments.length > 0) {
                authState.department = firstMin.departments[0].name;
            }
        }
        if (!authState.designation && window.OFFICIAL_STATISTICAL_DESIGNATIONS && window.OFFICIAL_STATISTICAL_DESIGNATIONS.length > 0) {
            authState.designation = window.OFFICIAL_STATISTICAL_DESIGNATIONS[0].name;
        }

        if (window.store) {
            window.store.state.isAuthModalOpen = true;
            window.store.notify();
        }
    };

    window.closeAuthModal = function() { window.switchAuthTab('login'); };

    window.switchAuthTab = function(tab) {
        window.rememberAuthFields();
        authState.tab = tab;
        store.state.authModalTab = tab;
        authState.error = null;
        authState.loginError = null;
        if (tab === 'register') {
            authState.step = 1;
        }
        reRenderModal();
    };

    function reRenderModal() {
        const active=document.activeElement, id=active?.id, start=active?.selectionStart, end=active?.selectionEnd;
        const scroll=document.querySelector('#authModalBackdrop .auth-content')?.scrollTop;
        if(window.store)store.notify();
        const next=id&&document.getElementById(id);
        if(next){next.focus({preventScroll:true});if(start!=null&&typeof next.setSelectionRange==='function')next.setSelectionRange(start,end);}
        const panel=document.querySelector('#authModalBackdrop .auth-content');if(panel&&scroll!=null)panel.scrollTop=scroll;
    }
    window.reRenderModal = reRenderModal;

    // -------------------------------------------------------------
    // STAGE 1: PROFILE PICTURE UPLOAD HANDLER
    // -------------------------------------------------------------
    window.handleProfilePicSelect = function(event) {
        window.rememberAuthFields();
        const file = event.target.files && event.target.files[0];
        if (!file) return;

        if (!file.type.match(/^image\/(png|jpeg|jpg|webp)$/)) {
            alert("Please select a valid image file (PNG, JPG, or WebP).");
            return;
        }

        if (file.size > 5 * 1024 * 1024) {
            alert("Image file size exceeds 5MB limit. Please choose a smaller photo.");
            return;
        }

        const reader = new FileReader();
        reader.onload = async function(e) {
            const dataUrl = e.target.result;
            authState.avatar = dataUrl;
            reRenderModal();

        };
        reader.readAsDataURL(file);
    };

    // -------------------------------------------------------------
    // STAGE 1: CASCADING HIERARCHY HELPERS
    // -------------------------------------------------------------
    window.handleAdminTypeChange = function(type) {
        window.rememberAuthFields();
        authState.adminType='central';
        reRenderModal();
    };
    window.handleMinistryChange = function(name) {
        window.rememberAuthFields();
        const list=centralOptions();
        const found=list.find(m=>m.name===name);
        authState.ministry=name;authState.department='';authState.assessmentArea='';authState.assessmentRole='';authState.designation='';
        if(authState.adminType==='state')authState.stateName=name;
        reRenderModal();
    };

    // -------------------------------------------------------------
    // STAGE 1 VALIDATION & ADVANCE
    // -------------------------------------------------------------
    window.handleStage1Next = function() {
        const nameEl = document.getElementById('regFullName');
        const ageEl = document.getElementById('regAge');
        const expEl = document.getElementById('regExperience');
        const gidEl = document.getElementById('regGovernmentId');
        const eduEl = document.getElementById('regEducation');
        const projEl = document.getElementById('regProjects');
        const desigEl = document.getElementById('regDesignation');

        if (nameEl) authState.fullName = nameEl.value.trim();
        if (ageEl) authState.age = ageEl.value.trim();
        if (expEl) authState.experience = expEl.value.trim();
        if (gidEl) authState.governmentId = gidEl.value.trim();
        if (eduEl) authState.education = eduEl.value.trim();
        if (projEl) authState.projects = projEl.value.trim();
        if (desigEl) window.handleAssessmentRole(desigEl.value);

        if (!authState.fullName) {
            authState.error = "Please enter your Full Name.";
            reRenderModal();
            return;
        }

        if (!authState.governmentId) {
            authState.error = "Please enter your Unique Government ID or Cadre Employee Number.";
            reRenderModal();
            return;
        }

        if(!authState.assessmentRole){authState.error='Choose your work area and designation.';reRenderModal();return;}
        authState.error = null;
        authState.step = 2;
        reRenderModal();
    };

    // -------------------------------------------------------------
    // STAGE 2: USERNAME AVAILABILITY CHECK
    // -------------------------------------------------------------
    let usernameRequest = 0;
    function updateUsernameFeedback() {
        const input=document.getElementById('regUsernameInput');
        if(!input)return;
        const available=authState.usernameStatus==='available';
        const invalid=['taken','invalid','error'].includes(authState.usernameStatus);
        input.classList.remove('border-teal-500','ring-1','ring-teal-200','border-rose-400','border-slate-200');
        input.classList.add(available?'border-teal-500':invalid?'border-rose-400':'border-slate-200');
        input.setAttribute('aria-invalid',invalid?'true':'false');
        const icon=input.nextElementSibling;
        if(icon)icon.innerHTML=authState.isCheckingUsername?'<i class="fa-solid fa-spinner fa-spin text-slate-400"></i>':available?'<i class="fa-solid fa-circle-check text-teal-600"></i>':invalid?'<i class="fa-solid fa-circle-xmark text-rose-500"></i>':'';
        const feedback=document.getElementById('usernameFeedback');
        if(feedback){feedback.textContent=authState.usernameMessage||'Letters, numbers, dots, and underscores allowed (3-30 characters).';feedback.className='text-xs font-semibold '+(available?'text-teal-700':invalid?'text-rose-600':'text-slate-400');}
        const button=document.querySelector('[onclick="handleStage2Next()"]');
        if(button){button.disabled=!available;button.classList.toggle('cursor-not-allowed',!available);button.classList.toggle('text-white',available);button.classList.toggle('text-slate-400',!available);button.style.backgroundColor=available?'#0B1B2B':'#E2E8F0';}
    }
    window.handleUsernameInput = function(val) {
        const request=++usernameRequest;
        const clean = (val || '').trim().toLowerCase();
        authState.username = clean;
        authState.error = null;

        if (checkUsernameDebounceTimer) {
            clearTimeout(checkUsernameDebounceTimer);
        }

        if (!clean) {
            authState.usernameStatus = null;
            authState.usernameMessage = '';
            authState.isCheckingUsername = false;
            updateUsernameFeedback();
            return;
        }

        if (!/^[a-zA-Z0-9_.]{3,30}$/.test(clean)) {
            authState.usernameStatus = 'invalid';
            authState.usernameMessage = 'Username must be 3-30 characters (letters, numbers, dots, underscores).';
            authState.isCheckingUsername = false;
            updateUsernameFeedback();
            return;
        }

        authState.isCheckingUsername = true;
        authState.usernameStatus = null;
        authState.usernameMessage = 'Checking availability…';
        updateUsernameFeedback();

        checkUsernameDebounceTimer = setTimeout(async () => {
            try {
                const res = await fetch(`/api/auth/check-username?username=${encodeURIComponent(clean)}`);
                const data = await res.json();
                if(request!==usernameRequest)return;
                if(!res.ok || data.success!==true || typeof data.available!=='boolean')throw new Error(data.error || 'Availability check failed');
                authState.isCheckingUsername = false;

                if (data.available) {
                    authState.usernameStatus = 'available';
                    authState.usernameMessage = '✓ Username available';
                } else {
                    authState.usernameStatus = 'taken';
                    authState.usernameMessage = '✕ Username already taken';
                }
            } catch (err) {
                if(request!==usernameRequest)return;
                authState.isCheckingUsername = false;
                authState.usernameStatus = 'error';
                authState.usernameMessage = 'Unable to check availability. Please try again.';
            }
            updateUsernameFeedback();
        }, 320);
    };

    window.handleStage2Next = function() {
        if (!authState.username || authState.usernameStatus !== 'available') {
            authState.error = "Please choose a valid and available username before continuing.";
            reRenderModal();
            return;
        }
        authState.error = null;
        authState.step = 3;
        reRenderModal();
    };

    // -------------------------------------------------------------
    // STAGE 3: PASSWORD STRENGTH & SUBMISSION
    // -------------------------------------------------------------
    window.handlePasswordInput = function(val) {
        authState.password = val || '';
        let score = 0;
        if (val.length >= 8) score++;
        if (/[A-Z]/.test(val)) score++;
        if (/[0-9]/.test(val)) score++;
        if (/[^A-Za-z0-9]/.test(val)) score++;
        authState.passwordStrength = score;

        const meterEl = document.getElementById('passwordStrengthBar');
        if (meterEl) {
            const widths = ['0%', '25%', '50%', '75%', '100%'];
            const colors = ['#CBD5E1', '#F43F5E', '#F59E0B', '#0EA5E9', '#10B981'];
            meterEl.style.width = widths[score];
            meterEl.style.backgroundColor = colors[score];
        }
    };

    window.handleConfirmPasswordInput = function(val) {
        authState.confirmPassword = val || '';
        const matchNotice = document.getElementById('passwordMatchNotice');
        if (matchNotice) {
            if (!val) {
                matchNotice.className = 'hidden';
            } else if (val === authState.password) {
                matchNotice.className = 'text-xs font-semibold text-emerald-600 flex items-center gap-1 mt-1';
                matchNotice.innerHTML = `<i class="fa-solid fa-circle-check text-xs"></i> <span>Passwords match</span>`;
            } else {
                matchNotice.className = 'text-xs font-semibold text-rose-600 flex items-center gap-1 mt-1';
                matchNotice.innerHTML = `<i class="fa-solid fa-circle-xmark text-xs"></i> <span>Passwords do not match</span>`;
            }
        }
    };

    window.handleCompleteRegistration = async function() {
        const pwdEl = document.getElementById('regPassword');
        const cpwdEl = document.getElementById('regConfirmPassword');
        if (pwdEl) authState.password = pwdEl.value;
        if (cpwdEl) authState.confirmPassword = cpwdEl.value;

        if (!authState.password || authState.password.length < 8) {
            authState.error = "Password must be at least 8 characters long.";
            reRenderModal();
            return;
        }

        if (authState.password !== authState.confirmPassword) {
            authState.error = "Passwords do not match. Please re-enter.";
            reRenderModal();
            return;
        }

        authState.isSubmitting = true;
        authState.error = null;
        reRenderModal();

        const payload = {
            full_name: authState.fullName,
            age: authState.age,
            experience: authState.experience,
            government_id: authState.governmentId,
            administration_type: authState.adminType === 'central' ? 'Central Government' : `State Government (${authState.stateName})`,
            ministry: authState.ministry,
            department: authState.department,
            designation: authState.designation,
            assessment_area: authState.assessmentArea,
            assessment_role_id: authState.assessmentRole,
            education: authState.education,
            projects: authState.projects,
            profile_picture: authState.avatar || '',
            username: authState.username,
            password: authState.password,
            confirm_password: authState.confirmPassword
        };

        try {
            const res = await fetch('/api/auth/register-username', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            authState.isSubmitting = false;

            if (res.ok && data.success && data.token) {
                await acceptAccount(data);
            } else {
                authState.error = data.error || "Registration failed. Please try again.";
                reRenderModal();
            }
        } catch (err) {
            authState.isSubmitting = false;
            authState.error = "Connection error. Please try again.";
            reRenderModal();
        }
    };

    // -------------------------------------------------------------
    // LOGIN HANDLER (Minimal Username + Password)
    // -------------------------------------------------------------
    window.handleDirectLogin = async function(e) {
        if (e && e.preventDefault) e.preventDefault();

        const uEl = document.getElementById('loginUsernameInput');
        const pEl = document.getElementById('loginPasswordInput');
        const username = uEl ? uEl.value.trim() : '';
        const password = pEl ? pEl.value : '';

        if (!username || !password) {
            authState.loginError = "Please enter both username and password.";
            reRenderModal();
            return;
        }

        authState.isLoggingIn = true;
        authState.loginError = null;
        reRenderModal();

        try {
            const res = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: username, password: password })
            });
            const data = await res.json();
            authState.isLoggingIn = false;

            if (res.ok && data.success && data.token) {
                await acceptAccount(data);
            } else {
                // Generic error: does not disclose if username exists
                authState.loginError = data.error || "Username or password is incorrect.";
                reRenderModal();
            }
        } catch (err) {
            authState.isLoggingIn = false;
            authState.loginError = "Connection error. Please verify the server is running.";
            reRenderModal();
        }
    };

    // -------------------------------------------------------------
    // RENDER MAIN AUTH MODAL
    // -------------------------------------------------------------
    function renderAuthModal(state) {
        if (state.user) return '';
        if(!authState.ministry&&centralOptions().length){const first=centralOptions()[0];authState.ministry=first.name;authState.department=first.departments[0].name;authState.designation=window.OFFICIAL_STATISTICAL_DESIGNATIONS[0].name;}

        return `
        <!-- Minimal Frosted Glass Backdrop -->
        <div id="authModalBackdrop" class="flex items-center justify-center w-full">

            <!-- Main Modal Container -->
            <div class="relative w-full max-w-xl bg-white/95 backdrop-blur-xl rounded-3xl border border-slate-200/80 shadow-2xl overflow-hidden transition-all text-left my-auto">

                <!-- Modal Top Header & Tab Toggle -->
                <div class="flex items-center justify-between px-6 pt-6 pb-4 border-b border-slate-100">
                    <div class="flex items-center gap-2.5">
                        <div class="w-8 h-8 rounded-xl bg-navy-900 flex items-center justify-center text-teal-400 font-bold text-xs" style="background: #0B1B2B;">
                            <i class="fa-solid fa-shield-halved text-teal-400"></i>
                        </div>
                        <div>
                            <h2 class="text-base font-bold text-slate-900 tracking-tight">StatSkill AI Access</h2>
                            <p class="text-[11px] text-slate-500">Secure Workforce Intelligence Platform</p>
                        </div>
                    </div>

                    <!-- Close Button -->
                    <button onclick="closeAuthModal()" aria-label="Return to sign in" class="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-500 hover:text-slate-800 flex items-center justify-center text-sm transition-all cursor-pointer">
                        <i class="fa-solid fa-xmark"></i>
                    </button>
                </div>

                <!-- Tab Switcher (Sign In vs Register) -->
                <div class="flex border-b border-slate-100 bg-slate-50/50 p-1.5">
                    <button onclick="switchAuthTab('login')" class="flex-1 py-2 text-xs font-semibold rounded-xl transition-all cursor-pointer ${authState.tab === 'login' ? 'bg-white text-slate-950 shadow-xs border border-slate-200/60' : 'text-slate-500 hover:text-slate-900'}">
                        <i class="fa-solid fa-arrow-right-to-bracket mr-1.5 text-slate-400"></i> Sign In
                    </button>
                    <button onclick="switchAuthTab('register')" class="flex-1 py-2 text-xs font-semibold rounded-xl transition-all cursor-pointer ${authState.tab === 'register' ? 'bg-white text-slate-950 shadow-xs border border-slate-200/60' : 'text-slate-500 hover:text-slate-900'}">
                        <i class="fa-solid fa-user-plus mr-1.5 text-slate-400"></i> Create Account
                    </button>
                </div>

                <!-- Content Area -->
                <div class="auth-content p-6 sm:p-8">
                    ${authState.tab === 'login' ? renderLoginForm() : renderRegisterWizard()}
                </div>

            </div>
        </div>
        `;
    }

    // -------------------------------------------------------------
    // RENDER LOGIN FORM
    // -------------------------------------------------------------
    function renderLoginForm() {
        return `
        <form onsubmit="handleDirectLogin(event)" class="space-y-5">
            <div>
                <h3 class="text-xl font-bold text-slate-900 tracking-tight">Welcome Back</h3>
                <p class="text-xs text-slate-500 mt-0.5">Enter your credentials to access your competency dashboard.</p>
            </div>

            ${authState.loginError ? `
                <div class="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium rounded-xl flex items-center gap-2">
                    <i class="fa-solid fa-triangle-exclamation text-rose-500"></i>
                    <span>${esc(authState.loginError)}</span>
                </div>
            ` : ''}

            <!-- Username Input -->
            <div class="space-y-1.5">
                <label for="loginUsernameInput" class="block text-xs font-semibold text-slate-700">Username or email</label>
                <div class="relative">
                    <i class="fa-solid fa-user absolute left-3.5 top-3 text-slate-400 text-xs"></i>
                    <input type="text" id="loginUsernameInput" value="${esc(authState.loginUsername)}" oninput="authState.loginUsername=this.value" placeholder="e.g. ananya.sharma" required autofocus class="w-full pl-9 pr-3.5 py-2.5 bg-white border border-slate-200 rounded-xl text-xs sm:text-sm font-medium focus:outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-100 transition-all text-slate-900">
                </div>
            </div>

            <!-- Password Input -->
            <div class="space-y-1.5">
                <div class="flex items-center justify-between">
                    <label for="loginPasswordInput" class="block text-xs font-semibold text-slate-700">Password</label>
                </div>
                <div class="relative">
                    <i class="fa-solid fa-lock absolute left-3.5 top-3 text-slate-400 text-xs"></i>
                    <input type="password" id="loginPasswordInput" placeholder="Enter your password" required class="w-full pl-9 pr-3.5 py-2.5 bg-white border border-slate-200 rounded-xl text-xs sm:text-sm font-medium focus:outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-100 transition-all text-slate-900">
                </div>
            </div>

            <!-- Submit Button -->
            <button type="submit" ${authState.isLoggingIn ? 'disabled' : ''} class="w-full py-2.5 px-4 bg-navy-900 hover:bg-navy-800 text-white rounded-xl text-xs sm:text-sm font-bold shadow-sm transition-all cursor-pointer flex items-center justify-center gap-2" style="background: #0B1B2B;">
                ${authState.isLoggingIn ? `
                    <i class="fa-solid fa-spinner fa-spin text-xs"></i>
                    <span>Authenticating...</span>
                ` : `
                    <span>Sign In</span>
                    <i class="fa-solid fa-arrow-right text-xs"></i>
                `}
            </button>

            <!-- Bottom Prompt -->
            <div class="text-center pt-2">
                <p class="text-xs text-slate-500">
                    Don't have an account?
                    <button type="button" onclick="switchAuthTab('register')" class="text-teal-700 hover:text-teal-800 font-bold ml-1 cursor-pointer">Register here</button>
                </p>
            </div>
        </form>
        `;
    }

    // -------------------------------------------------------------
    // RENDER REGISTER 3-STAGE WIZARD
    // -------------------------------------------------------------
    function renderRegisterWizard() {
        const step = authState.step;

        return `
        <div class="space-y-6">

            <!-- Progress Stepper (01 Hierarchy & Profile | 02 Create Username | 03 Security Password) -->
            <div class="grid grid-cols-3 gap-2 pb-2 border-b border-slate-100 text-center select-none">
                <div class="flex flex-col items-center gap-1 ${step >= 1 ? 'text-teal-700 font-bold' : 'text-slate-400'}">
                    <span class="text-[10px] uppercase font-mono tracking-wider">Step 01</span>
                    <span class="text-xs ${step === 1 ? 'font-bold' : 'font-medium'}">Hierarchy & Profile</span>
                    <div class="w-full h-1 rounded-full ${step >= 1 ? 'bg-teal-500' : 'bg-slate-200'} mt-1"></div>
                </div>
                <div class="flex flex-col items-center gap-1 ${step >= 2 ? 'text-teal-700 font-bold' : 'text-slate-400'}">
                    <span class="text-[10px] uppercase font-mono tracking-wider">Step 02</span>
                    <span class="text-xs ${step === 2 ? 'font-bold' : 'font-medium'}">Create Username</span>
                    <div class="w-full h-1 rounded-full ${step >= 2 ? 'bg-teal-500' : 'bg-slate-200'} mt-1"></div>
                </div>
                <div class="flex flex-col items-center gap-1 ${step >= 3 ? 'text-teal-700 font-bold' : 'text-slate-400'}">
                    <span class="text-[10px] uppercase font-mono tracking-wider">Step 03</span>
                    <span class="text-xs ${step === 3 ? 'font-bold' : 'font-medium'}">Security Password</span>
                    <div class="w-full h-1 rounded-full ${step >= 3 ? 'bg-teal-500' : 'bg-slate-200'} mt-1"></div>
                </div>
            </div>

            ${authState.error ? `
                <div class="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium rounded-xl flex items-center gap-2">
                    <i class="fa-solid fa-circle-exclamation text-rose-500"></i>
                    <span>${esc(authState.error)}</span>
                </div>
            ` : ''}

            <!-- Step 1: Hierarchy & Profile -->
            ${step === 1 ? renderStage1() : ''}

            <!-- Step 2: Create Username -->
            ${step === 2 ? renderStage2() : ''}

            <!-- Step 3: Security Password -->
            ${step === 3 ? renderStage3() : ''}

        </div>
        `;
    }

    // -------------------------------------------------------------
    // STAGE 1 FORM (Hierarchy & Profile)
    // -------------------------------------------------------------
    function renderStage1() {
        authState.adminType='central';
        const centralMinistries=centralOptions();
        if(!centralMinistries.some(m=>m.name===authState.ministry)){authState.ministry=centralMinistries[0]?.name||'';authState.assessmentArea='';authState.assessmentRole='';authState.department='';}
        const activeMin = centralMinistries.find(m => m.name === authState.ministry) || centralMinistries[0];
        const depts = (activeMin && activeMin.departments) ? activeMin.departments : [];
        const areas=(store.state.registrationCatalog?.areas||[]).filter(a=>a.ministry===authState.ministry);
        const designations=areas.find(a=>a.id===authState.assessmentArea)?.roles||[];

        return `
        <div class="space-y-6">

            <!-- Group 1: Personal Information -->
            <div class="space-y-4">
                <div class="flex items-center justify-between border-b border-slate-100 pb-1.5">
                    <h4 class="text-xs font-bold uppercase tracking-wider text-slate-800">Personal Information</h4>
                    <span class="text-[11px] text-slate-400">Step 1 of 3</span>
                </div>

                <!-- Profile Picture Upload with Circular Preview -->
                <div class="flex items-center gap-4 p-3 bg-slate-50/80 rounded-2xl border border-slate-200/80">
                    <div class="relative w-16 h-16 rounded-full overflow-hidden bg-slate-200 border-2 border-teal-500 flex-shrink-0 flex items-center justify-center">
                        ${authState.avatar ? `
                            <img src="${esc(authState.avatar)}" alt="Avatar Preview" class="w-full h-full object-cover">
                        ` : `
                            <i class="fa-solid fa-user text-slate-400 text-2xl"></i>
                        `}
                    </div>
                    <div class="space-y-1">
                        <label class="block text-xs font-bold text-slate-800">Profile Picture</label>
                        <p class="text-[11px] text-slate-500">Upload an official avatar (PNG, JPG, max 5MB)</p>
                        <label class="inline-flex items-center gap-1.5 px-3 py-1 bg-white hover:bg-slate-100 text-slate-700 text-xs font-semibold border border-slate-300 rounded-lg cursor-pointer transition-all shadow-2xs">
                            <i class="fa-solid fa-arrow-up-from-bracket text-xs text-teal-600"></i>
                            <span>Choose Photo</span>
                            <input type="file" accept="image/*" onchange="handleProfilePicSelect(event)" class="hidden">
                        </label>
                    </div>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div class="space-y-1">
                        <label for="regFullName" class="block text-xs font-semibold text-slate-700">Full Name <span class="text-rose-500">*</span></label>
                        <input type="text" id="regFullName" oninput="authState.fullName=this.value" value="${esc(authState.fullName)}" placeholder="e.g. Ananya Sharma" class="w-full px-3 py-2 bg-white border border-slate-200 rounded-xl text-xs font-medium text-slate-900 focus:outline-none focus:border-teal-500">
                    </div>

                    <div class="space-y-1">
                        <label for="regGovernmentId" class="block text-xs font-semibold text-slate-700">Unique Government ID <span class="text-rose-500">*</span></label>
                        <input type="text" id="regGovernmentId" oninput="authState.governmentId=this.value" value="${esc(authState.governmentId)}" placeholder="e.g. ISS/2026/84920" class="w-full px-3 py-2 bg-white border border-slate-200 rounded-xl text-xs font-medium text-slate-900 focus:outline-none focus:border-teal-500">
                    </div>

                    <div class="space-y-1">
                        <label for="regAge" class="block text-xs font-semibold text-slate-700">Age</label>
                        <input type="number" id="regAge" oninput="authState.age=this.value" value="${esc(authState.age)}" min="18" max="75" class="w-full px-3 py-2 bg-white border border-slate-200 rounded-xl text-xs font-medium text-slate-900 focus:outline-none focus:border-teal-500">
                    </div>

                    <div class="space-y-1">
                        <label for="regExperience" class="block text-xs font-semibold text-slate-700">Experience in Cadre (Years)</label>
                        <input type="text" id="regExperience" oninput="authState.experience=this.value" value="${esc(authState.experience)}" placeholder="e.g. 5" class="w-full px-3 py-2 bg-white border border-slate-200 rounded-xl text-xs font-medium text-slate-900 focus:outline-none focus:border-teal-500">
                    </div>
                </div>
            </div>

            <!-- Group 2: Professional Information & Administrative Hierarchy -->
            <div class="space-y-4">
                <div class="border-b border-slate-100 pb-1.5">
                    <h4 class="text-xs font-bold uppercase tracking-wider text-slate-800">Professional Information</h4>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <!-- Administration Type -->
                    <div class="space-y-1">
                        <label class="block text-xs font-semibold text-slate-700">Administration Type</label>
                        <select onchange="handleAdminTypeChange(this.value)" class="w-full px-3 py-2 bg-white border border-slate-200 rounded-xl text-xs font-medium text-slate-900 focus:outline-none focus:border-teal-500">
                            <option value="central" ${authState.adminType === 'central' ? 'selected' : ''}>Central Government</option>

                        </select>
                    </div>

                    <!-- Ministry / Entity -->
                    <div class="space-y-1">
                        <label class="block text-xs font-semibold text-slate-700">${authState.adminType==='central'?'Ministry / Central Entity':'State / Union Territory'}</label>
                        <select onchange="handleMinistryChange(this.value)" class="w-full px-3 py-2 bg-white border border-slate-200 rounded-xl text-xs font-medium text-slate-900 focus:outline-none focus:border-teal-500 truncate">
                            ${centralMinistries.map(m => `
                                <option value="${m.name}" ${authState.ministry === m.name ? 'selected' : ''}>${m.name}</option>
                            `).join('')}
                        </select>
                    </div>

                    <input type="hidden" id="regDepartment" value="${esc(authState.department)}">

                    <div class="space-y-1 sm:col-span-2">
                        <label for="regAssessmentArea" class="block text-xs font-semibold text-slate-700">Work area *</label>
                        <select id="regAssessmentArea" onchange="handleAssessmentArea(this.value)" class="w-full px-3 py-2 bg-white border border-slate-200 rounded-xl text-xs font-medium text-slate-900">
                            <option value="">Choose your work area</option>${areas.map(a=>`<option value="${esc(a.id)}" ${a.id===authState.assessmentArea?'selected':''}>${esc(a.name)}</option>`).join('')}
                        </select>
                    </div>

                    <div class="space-y-1 sm:col-span-2">
                        <label for="regDesignation" class="block text-xs font-semibold text-slate-700">Designation *</label>
                        <select id="regDesignation" onchange="handleAssessmentRole(this.value)" class="w-full px-3 py-2 bg-white border border-slate-200 rounded-xl text-xs font-medium text-slate-900">
                            <option value="">Choose your designation</option>${designations.map(r=>`<option value="${esc(r.id)}" ${r.id===authState.assessmentRole?'selected':''}>${esc(r.title)}</option>`).join('')}
                        </select>
                    </div>

                    <!-- Education -->
                    <div class="space-y-1 sm:col-span-2">
                        <label for="regEducation" class="block text-xs font-semibold text-slate-700">Education</label>
                        <input type="text" id="regEducation" oninput="authState.education=this.value" value="${esc(authState.education)}" placeholder="e.g. M.Sc. Statistics / Economics" class="w-full px-3 py-2 bg-white border border-slate-200 rounded-xl text-xs font-medium text-slate-900 focus:outline-none focus:border-teal-500">
                    </div>

                    <!-- Projects -->
                    <div class="space-y-1 sm:col-span-2">
                        <label for="regProjects" class="block text-xs font-semibold text-slate-700">Key Projects & Statistical Assignments</label>
                        <input type="text" id="regProjects" oninput="authState.projects=this.value" value="${esc(authState.projects)}" placeholder="e.g. Consumer Price Index, PLFS, IIP Base Revision" class="w-full px-3 py-2 bg-white border border-slate-200 rounded-xl text-xs font-medium text-slate-900 focus:outline-none focus:border-teal-500">
                    </div>
                </div>
            </div>

            <!-- Advance Button -->
            <div class="pt-2">
                <button type="button" onclick="handleStage1Next()" class="w-full py-2.5 px-4 bg-navy-900 hover:bg-navy-800 text-white rounded-xl text-xs sm:text-sm font-bold shadow-sm transition-all cursor-pointer flex items-center justify-center gap-2" style="background: #0B1B2B;">
                    <span>Next: Create Username</span>
                    <i class="fa-solid fa-arrow-right text-xs"></i>
                </button>
            </div>

        </div>
        `;
    }

    // -------------------------------------------------------------
    // STAGE 2 FORM (Create Username)
    // -------------------------------------------------------------
    function renderStage2() {
        return `
        <div class="space-y-6">
            <div>
                <h3 class="text-xl font-bold text-slate-900 tracking-tight">Create your username</h3>
                <p class="text-xs text-slate-500 mt-0.5">Choose a unique username for your StatSkill AI account.</p>
            </div>

            <div class="space-y-2">
                <label for="regUsernameInput" class="block text-xs font-semibold text-slate-700">Choose a unique username</label>
                <div class="relative">
                    <span class="absolute left-3.5 top-2.5 text-slate-400 font-mono text-xs">@</span>
                    <input type="text" id="regUsernameInput" value="${esc(authState.username)}" oninput="handleUsernameInput(this.value)" placeholder="e.g. ananya.sharma" autofocus class="w-full pl-8 pr-10 py-2.5 bg-white border ${authState.usernameStatus === 'available' ? 'border-teal-500 ring-1 ring-teal-200' : (authState.usernameStatus === 'taken' || authState.usernameStatus === 'invalid' ? 'border-rose-400' : 'border-slate-200')} rounded-xl text-xs sm:text-sm font-mono font-medium focus:outline-none focus:border-teal-500 text-slate-900">

                    <div class="absolute right-3 top-3 text-xs">
                        ${authState.isCheckingUsername ? `
                            <i class="fa-solid fa-spinner fa-spin text-slate-400"></i>
                        ` : (authState.usernameStatus === 'available' ? `
                            <i class="fa-solid fa-circle-check text-teal-600"></i>
                        ` : (authState.usernameStatus === 'taken' || authState.usernameStatus === 'invalid' ? `
                            <i class="fa-solid fa-circle-xmark text-rose-500"></i>
                        ` : ''))}
                    </div>
                </div>

                <!-- Status Feedback Label -->
                ${authState.usernameMessage ? `
                    <div id="usernameFeedback" role="status" aria-live="polite" class="text-xs font-semibold ${authState.usernameStatus === 'available' ? 'text-teal-700' : 'text-rose-600'}">
                        ${esc(authState.usernameMessage)}
                    </div>
                ` : `
                    <p id="usernameFeedback" role="status" aria-live="polite" class="text-[11px] text-slate-400">Letters, numbers, dots, and underscores allowed (3-30 characters).</p>
                `}
            </div>

            <!-- Navigation Buttons -->
            <div class="flex items-center gap-3 pt-4">
                <button type="button" onclick="authState.step=1; reRenderModal();" class="py-2.5 px-4 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold transition-all cursor-pointer">
                    ← Back
                </button>
                <button type="button" onclick="handleStage2Next()" ${authState.usernameStatus !== 'available' ? 'disabled' : ''} class="flex-1 py-2.5 px-4 ${authState.usernameStatus === 'available' ? 'bg-navy-900 hover:bg-navy-800 text-white cursor-pointer' : 'bg-slate-200 text-slate-400 cursor-not-allowed'} rounded-xl text-xs sm:text-sm font-bold shadow-sm transition-all flex items-center justify-center gap-2" style="${authState.usernameStatus === 'available' ? 'background: #0B1B2B;' : ''}">
                    <span>Next: Create Password</span>
                    <i class="fa-solid fa-arrow-right text-xs"></i>
                </button>
            </div>
        </div>
        `;
    }

    // -------------------------------------------------------------
    // STAGE 3 FORM (Security Password)
    // -------------------------------------------------------------
    function renderStage3() {
        return `
        <div class="space-y-6">
            <div>
                <h3 class="text-xl font-bold text-slate-900 tracking-tight">Create your password</h3>
                <p class="text-xs text-slate-500 mt-0.5">Set a secure password to protect your statistical intelligence profile.</p>
            </div>

            <!-- Password Input -->
            <div class="space-y-1.5">
                <label for="regPassword" class="block text-xs font-semibold text-slate-700">Password (min 8 characters)</label>
                <div class="relative">
                    <i class="fa-solid fa-lock absolute left-3.5 top-3 text-slate-400 text-xs"></i>
                    <input type="password" id="regPassword" value="${esc(authState.password)}" oninput="handlePasswordInput(this.value)" placeholder="Enter strong password" autofocus class="w-full pl-9 pr-3.5 py-2.5 bg-white border border-slate-200 rounded-xl text-xs sm:text-sm font-medium focus:outline-none focus:border-teal-500 text-slate-900">
                </div>
                <!-- Strength bar -->
                <div class="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden mt-1.5">
                    <div id="passwordStrengthBar" class="h-full bg-slate-300 transition-all duration-300" style="width: ${authState.passwordStrength * 25}%"></div>
                </div>
            </div>

            <!-- Confirm Password -->
            <div class="space-y-1.5">
                <label for="regConfirmPassword" class="block text-xs font-semibold text-slate-700">Confirm Password</label>
                <div class="relative">
                    <i class="fa-solid fa-lock-open absolute left-3.5 top-3 text-slate-400 text-xs"></i>
                    <input type="password" id="regConfirmPassword" value="${esc(authState.confirmPassword)}" oninput="handleConfirmPasswordInput(this.value)" placeholder="Re-enter password to confirm" class="w-full pl-9 pr-3.5 py-2.5 bg-white border border-slate-200 rounded-xl text-xs sm:text-sm font-medium focus:outline-none focus:border-teal-500 text-slate-900">
                </div>
                <div id="passwordMatchNotice" class="hidden"></div>
            </div>

            <!-- Review Summary Capsule -->
            <div class="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-600 space-y-1">
                <div>Account for: <strong class="text-slate-900">${esc(authState.fullName)}</strong> (@${esc(authState.username)})</div>
                <div>Cadre ID: <strong class="text-slate-900 font-mono">${esc(authState.governmentId)}</strong></div>
            </div>

            <!-- Action Buttons -->
            <div class="flex items-center gap-3 pt-2">
                <button type="button" onclick="authState.step=2; reRenderModal();" class="py-2.5 px-4 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold transition-all cursor-pointer">
                    ← Back
                </button>
                <button type="button" onclick="handleCompleteRegistration()" ${authState.isSubmitting ? 'disabled' : ''} class="flex-1 py-2.5 px-4 bg-navy-900 hover:bg-navy-800 text-white rounded-xl text-xs sm:text-sm font-bold shadow-sm transition-all cursor-pointer flex items-center justify-center gap-2" style="background: #0B1B2B;">
                    ${authState.isSubmitting ? `
                        <i class="fa-solid fa-spinner fa-spin text-xs"></i>
                        <span>Registering Account...</span>
                    ` : `
                        <i class="fa-solid fa-check text-xs text-teal-400"></i>
                        <span>Complete Registration</span>
                    `}
                </button>
            </div>
        </div>
        `;
    }

    // Attach to window
    window.renderAuthModal = renderAuthModal;

})(window);
