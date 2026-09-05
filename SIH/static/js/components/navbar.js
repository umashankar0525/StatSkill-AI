/**
 * StatSkill AI — Modern Minimalist Navigation Header
 * Inspired by modern Web3 & SaaS aesthetics:
 * - Single-tier clean frosted glass sticky header
 * - Modern StatSkill AI wordmark with subtle geometric badge
 * - Task navigation is provided by the separate workspace bar
 * - Accessibility panel trigger & Language selector
 * - User profile pill with avatar & logout, or clean Login / Register CTA
 */

function renderNavbar(state) {
    const lang = state.currentLanguage || 'en';
    const user = state.user;

    const navLabels = {
        en: { home: "Home", about: "About", dashboard: "Dashboard", quizzes: "Ministry Quizzes", userGuide: "User Guide", loginBtn: "Login / Register", a11y: "Accessibility", logout: "Sign Out" },
        hi: { home: "होम", about: "परिचय", dashboard: "डैशबोर्ड", quizzes: "मंत्रालय प्रश्नोत्तरी", userGuide: "निर्देशिका", loginBtn: "लॉगिन / पंजीकरण", a11y: "सुगमता", logout: "लॉगआउट" },
        te: { home: "హోమ్", about: "గురించి", dashboard: "డ్యాష్‌బోర్డ్", quizzes: "మంత్రిత్వ క్విజ్‌లు", userGuide: "యూజర్ గైడ్", loginBtn: "లాగిన్ / నమోదు", a11y: "యాక్సెసిబిలిటీ", logout: "లాగౌట్" }
    };
    const labels = navLabels[lang] || navLabels.en;

    const avatarUrl = (user && (user.profile_picture || user.avatar)) ? (user.profile_picture || user.avatar) : null;
    const displayName = user ? (user.full_name || user.name || user.username || 'Officer') : '';
    const displayUsername = user ? (user.username ? `@${user.username}` : '') : '';

    return `
    <header class="main-header border-b border-slate-200/80 bg-white/80 backdrop-blur-md px-4 sm:px-8 py-3 sticky top-0 z-40 transition-all">
        <div class="max-w-7xl mx-auto flex items-center justify-between gap-6">

            <!-- Left: StatSkill AI Minimal Logo & Wordmark -->
            <div class="flex items-center gap-3 cursor-pointer group select-none" onclick="store.navigate('learner-dash')">
                <div class="w-9 h-9 rounded-xl bg-navy-900 flex items-center justify-center text-teal-400 shadow-sm border border-slate-700/40 group-hover:border-teal-500/50 transition-all flex-shrink-0" style="background: #0B1B2B;">
                    <i class="fa-solid fa-layer-group text-sm text-teal-400"></i>
                </div>
                <div class="leading-none">
                    <span class="text-lg sm:text-xl font-bold tracking-tight text-slate-950 font-sans" style="color: #0B1B2B;">
                        StatSkill <span class="text-teal-600 font-extrabold">AI</span>
                    </span>
                    <span class="block text-[10px] font-medium tracking-wider uppercase text-slate-400 mt-0.5">
                        Workforce Intelligence
                    </span>
                </div>
            </div>

            <!-- Right: Accessibility, Language, and Authentication Pill -->
            <div class="flex items-center gap-3">

                <!-- Accessibility Trigger -->
                <button onclick="window.toggleAccessibilityPanel(event)" class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100/80 border border-slate-200/60 transition-all cursor-pointer" title="Accessibility preferences">
                    <i class="fa-solid fa-universal-access text-teal-600 text-xs"></i>
                    <span class="hidden lg:inline text-[11px]">${labels.a11y}</span>
                </button>

                <!-- Language Selector -->
                <div class="flex items-center gap-1 bg-white px-2.5 py-1.5 rounded-lg border border-slate-200/60 text-xs shadow-2xs">
                    <i class="fa-solid fa-globe text-slate-400 text-xs"></i>
                    <select aria-label="Change language" onchange="store.setLanguage(this.value)" class="bg-transparent font-medium text-slate-700 focus:outline-none cursor-pointer text-xs">
                        <option value="en" ${lang === 'en' ? 'selected' : ''}>English</option>
                        <option value="hi" ${lang === 'hi' ? 'selected' : ''}>हिन्दी</option>
                    </select>
                </div>

                <!-- User Session Pill or Login/Register CTA -->
                ${user ? `
                    <div class="flex items-center gap-2 pl-1 border-l border-slate-200/80">
                        <button onclick="store.navigate('profile')" class="flex items-center gap-2 bg-slate-50 hover:bg-slate-100 px-2.5 py-1.5 rounded-xl border border-slate-200/80 text-xs transition-all cursor-pointer shadow-xs" title="View Profile">
                            ${avatarUrl ? `
                                <img src="${avatarUrl}" alt="${displayName}" class="w-6 h-6 rounded-full object-cover border border-teal-500/40">
                            ` : `
                                <div class="w-6 h-6 rounded-full bg-navy-900 text-teal-300 flex items-center justify-center font-bold text-[11px]">
                                    ${displayName.charAt(0).toUpperCase()}
                                </div>
                            `}
                            <div class="text-left hidden sm:block leading-tight">
                                <div class="font-semibold text-slate-900 text-xs max-w-[110px] truncate">${displayName}</div>
                                ${displayUsername ? `<div class="text-[10px] text-slate-400 font-mono">${displayUsername}</div>` : ''}
                            </div>
                        </button>
                        <button onclick="store.logout()" aria-label="${tr('Sign out')}" class="text-slate-400 hover:text-rose-600 p-2 text-xs font-semibold transition-all cursor-pointer" title="${labels.logout}">
                            <i class="fa-solid fa-arrow-right-from-bracket"></i>
                        </button>
                    </div>
                ` : `
                    <button onclick="store.openAuthModal('login')" class="btn btn-secondary text-xs py-1.5 px-3.5 border-slate-200/80 text-slate-700 hover:text-slate-950 font-semibold cursor-pointer">
                        <span>Sign In</span>
                    </button>
                    <button onclick="store.openAuthModal('register')" class="btn btn-primary text-xs py-1.5 px-4 bg-navy-900 text-white rounded-lg font-semibold shadow-xs hover:bg-navy-800 cursor-pointer">
                        <span>Register</span>
                    </button>
                `}
            </div>

        </div>

    </header>
    `;
}

window.renderNavbar = renderNavbar;
