/**
 * StatSkill AI — Accessibility Manager (v2.0 Bulletproof)
 * iGOT Karmayogi UserWay-Parity Accessibility Suite
 * Completely self-contained. Zero external dependencies.
 */

(function () {
    'use strict';

    /* ── Constants ────────────────────────────────────────── */
    var STORAGE_KEY = 'statskillA11ySettings';

    var DEFAULTS = {
        contrastLevel: 0,       // 0=off, 1=high, 2=yellow-black, 3=cream-blue
        highlightLinks: false,
        biggerText: false,
        textSpacing: false,
        pauseAnimations: false,
        hideImages: false,
        dyslexiaFriendly: false,
        largeCursor: false,
        tooltips: false,
        lineHeight: false,
        alignLeft: false,
        saturation: 0           // 0=normal, 1=low, 2=grayscale
    };


    /* ── State ────────────────────────────────────────────── */
    var settings = loadSettings();
    var panelOpen = false;
    var tooltipEl = null;

    /* ── Persistence ──────────────────────────────────────── */
    function loadSettings() {
        try {
            var raw = localStorage.getItem(STORAGE_KEY);
            if (raw) {
                var parsed = JSON.parse(raw);
                var out = {};
                for (var k in DEFAULTS) out[k] = (parsed[k] !== undefined ? parsed[k] : DEFAULTS[k]);
                return out;
            }
        } catch (e) { /* ignore */ }
        var copy = {};
        for (var k in DEFAULTS) copy[k] = DEFAULTS[k];
        return copy;
    }

    function saveSettings() {
        try { localStorage.setItem(STORAGE_KEY, JSON.stringify(settings)); } catch (e) { /* ignore */ }
    }

    /* ── CSS Injection ────────────────────────────────────── */
    function injectCSS() {
        if (document.getElementById('a11yMgrCSS')) return;
        var s = document.createElement('style');
        s.id = 'a11yMgrCSS';
        s.textContent = [
            /* 1. High Contrast (Black & White) */
            'body.a11y-contrast-1{background:#000!important;color:#fff!important}',
            'body.a11y-contrast-1 *:not(#a11yWidget):not(#a11yWidget *){background-color:#000!important;color:#fff!important;border-color:#666!important}',

            /* 2. Yellow on Black */
            'body.a11y-contrast-2{background:#000!important;color:#fde047!important}',
            'body.a11y-contrast-2 *:not(#a11yWidget):not(#a11yWidget *){background-color:#000!important;color:#fde047!important;border-color:#ca8a04!important}',

            /* 3. Blue on Cream */
            'body.a11y-contrast-3{background:#fdf6e2!important;color:#0b2545!important}',
            'body.a11y-contrast-3 *:not(#a11yWidget):not(#a11yWidget *){background-color:#fdf6e2!important;color:#0b2545!important;border-color:#d3c29e!important}',

            /* 4. BULLETPROOF Highlight Links (Targets a, button, role=button, onclick) */
            'body.a11y-hl a:not(#a11yWidget *), body.a11y-hl button:not(#a11yWidget *), body.a11y-hl [role="button"]:not(#a11yWidget *), body.a11y-hl [onclick]:not(#a11yWidget *){' +
                'outline:3px solid #f97316!important;' +
                'outline-offset:2px!important;' +
                'text-decoration:underline!important;' +
                'background-color:rgba(249,115,22,0.25)!important;' +
                'box-shadow:0 0 0 2px #f97316!important;' +
            '}',
            'body.a11y-hl a:not(#a11yWidget *) *, body.a11y-hl button:not(#a11yWidget *) *{text-decoration:underline!important}',

            /* 5. Bigger Text */
            'body.a11y-bigger-text{font-size:125%!important}',
            'body.a11y-bigger-text *:not(#a11yWidget *){font-size:115%!important}',

            /* 6. Text Spacing */
            'body.a11y-spacing *:not(#a11yWidget *){letter-spacing:.12em!important;word-spacing:.18em!important}',

            /* 7. Pause Animations */
            'body.a11y-pause-anim *,body.a11y-pause-anim ::before,body.a11y-pause-anim ::after{animation:none!important;transition:none!important}',

            /* 8. Hide Images */
            'body.a11y-hide-img img,body.a11y-hide-img picture,body.a11y-hide-img svg:not(.a11y-keep):not(#a11yWidget *){opacity:0!important;visibility:hidden!important}',

            /* 9. Dyslexia Font */
            'body.a11y-dyslexia,body.a11y-dyslexia *:not(#a11yWidget *){font-family:OpenDyslexic,"Comic Sans MS",Lexend,sans-serif!important;letter-spacing:.05em!important;word-spacing:.1em!important}',

            /* 10. Large Cursor */
            "body.a11y-cursor,body.a11y-cursor *{cursor:url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 24 24' fill='%23F97316' stroke='%230B2545' stroke-width='1.5'%3E%3Cpath d='M4.5 3.5l14 10-6 1.5 4.5 7.5-2.5 1.5-4.5-7.5-5.5 5.5z'/%3E%3C/svg%3E\") 0 0,auto!important}",

            /* 11. Line Height */
            'body.a11y-lh *:not(#a11yWidget *){line-height:2!important}',

            /* 12. Align Left */
            'body.a11y-left *:not(#a11yWidget *){text-align:left!important}',

            /* 13. Saturation (scoped to #app) */
            'body.a11y-sat-1 #app{filter:saturate(0.4)!important}',
            'body.a11y-sat-2 #app{filter:grayscale(1)!important}',

            /* Widget Styling */
            '#a11yWidget{font-family:Inter,system-ui,sans-serif!important;box-sizing:border-box!important}',
            '#a11yWidget *{box-sizing:border-box!important}',
            '#a11yWidget button{cursor:pointer}',
        ].join('\n');
        (document.head || document.documentElement).appendChild(s);
    }

    /* ── Apply Settings to DOM ────────────────────────────── */
    function applyAll() {
        var b = document.body;
        if (!b) return;

        b.classList.remove(
            'a11y-contrast-1','a11y-contrast-2','a11y-contrast-3',
            'a11y-hl','a11y-bigger-text','a11y-spacing',
            'a11y-pause-anim','a11y-hide-img','a11y-dyslexia',
            'a11y-cursor','a11y-lh','a11y-left',
            'a11y-sat-1','a11y-sat-2','a11y-tooltips'
        );

        if (settings.contrastLevel > 0) b.classList.add('a11y-contrast-' + settings.contrastLevel);
        if (settings.highlightLinks)    b.classList.add('a11y-hl');
        if (settings.biggerText)        b.classList.add('a11y-bigger-text');
        if (settings.textSpacing)       b.classList.add('a11y-spacing');
        if (settings.pauseAnimations)   b.classList.add('a11y-pause-anim');
        if (settings.hideImages)        b.classList.add('a11y-hide-img');
        if (settings.dyslexiaFriendly)  b.classList.add('a11y-dyslexia');
        if (settings.largeCursor)       b.classList.add('a11y-cursor');
        if (settings.lineHeight)        b.classList.add('a11y-lh');
        if (settings.alignLeft)         b.classList.add('a11y-left');
        if (settings.saturation > 0)    b.classList.add('a11y-sat-' + settings.saturation);
        if (settings.tooltips)          b.classList.add('a11y-tooltips');

        updatePanelUI();
        saveSettings();
    }

    /* ── Tooltips Engine ───────────────────────────────────── */
    function initTooltipEngine() {
        if (window._a11yTooltipEngineBound) return;
        window._a11yTooltipEngineBound = true;

        tooltipEl = document.createElement('div');
        tooltipEl.id = 'a11yTooltipBadge';
        tooltipEl.style.cssText = 'position:fixed;z-index:999999;pointer-events:none;display:none;background:#0b2545;color:#ffffff;' +
            'padding:6px 12px;border-radius:8px;font-size:12px;font-weight:700;box-shadow:0 10px 25px rgba(0,0,0,0.5);' +
            'border:1px solid #f97316;max-width:280px;line-height:1.3;text-align:center;';
        (document.body || document.documentElement).appendChild(tooltipEl);

        function showTooltip(target, text, e) {
            if (!settings.tooltips || !text) return;
            tooltipEl.textContent = text;
            tooltipEl.style.display = 'block';

            var x = (e && e.clientX) ? e.clientX + 12 : 20;
            var y = (e && e.clientY) ? e.clientY + 18 : 20;

            // Keep within viewport
            if (x + 200 > window.innerWidth) x = window.innerWidth - 210;
            if (y + 40 > window.innerHeight) y = e.clientY - 35;

            tooltipEl.style.left = x + 'px';
            tooltipEl.style.top = y + 'px';
        }

        function hideTooltip() {
            if (tooltipEl) tooltipEl.style.display = 'none';
        }

        document.addEventListener('mouseover', function (e) {
            if (!settings.tooltips) return;
            var el = e.target.closest('[title], [aria-label], [alt], [placeholder]');
            if (!el || el.closest('#a11yWidget')) return;

            var txt = el.getAttribute('aria-label') || el.getAttribute('title') || el.getAttribute('alt') || el.getAttribute('placeholder');
            if (txt && txt.trim()) showTooltip(el, txt.trim(), e);
        });

        document.addEventListener('mousemove', function (e) {
            if (!settings.tooltips || tooltipEl.style.display === 'none') return;
            var x = e.clientX + 12;
            var y = e.clientY + 18;
            if (x + 200 > window.innerWidth) x = window.innerWidth - 210;
            if (y + 40 > window.innerHeight) y = e.clientY - 35;

            tooltipEl.style.left = x + 'px';
            tooltipEl.style.top = y + 'px';
        });

        document.addEventListener('mouseout', function (e) {
            if (settings.tooltips) hideTooltip();
        });
    }

    /* ── Build Widget HTML ─────────────────────────────────── */
    function buildWidget() {
        if (document.getElementById('a11yWidget')) return;
        var parent = document.body || document.documentElement;
        if (!parent) return;

        var root = document.createElement('div');
        root.id = 'a11yWidget';
        root.style.cssText = 'position:fixed;bottom:0;left:0;z-index:99999;pointer-events:none;';
        root.innerHTML = buildTriggerHTML() + buildPanelHTML();
        parent.appendChild(root);

        bindWidgetEvents();
        initTooltipEngine();
    }

    function buildTriggerHTML() {
        return '<button id="a11yTrigger" type="button" aria-label="Open Accessibility Menu" aria-expanded="false" aria-controls="a11yPanel" ' +
            'style="pointer-events:auto;position:fixed;bottom:24px;left:24px;z-index:99999;width:56px;height:56px;border-radius:50%;' +
            'background:#0B2545;border:2px solid #F97316;color:#F97316;font-size:24px;display:flex;align-items:center;justify-content:center;' +
            'box-shadow:0 8px 32px rgba(0,0,0,.4);cursor:pointer;transition:transform .15s, background-color .15s;" ' +
            'title="Accessibility Menu (CTRL+U or ALT+A)">' +
            '<i class="fa-solid fa-universal-access"></i></button>';
    }

    function buildPanelHTML() {
        var card = function(id, icon, label) {
            return '<button id="' + id + '" type="button" class="a11y-card" ' +
                'style="pointer-events:auto;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;' +
                'padding:14px 4px;border-radius:16px;border:1px solid #334155;background:#1e293b;color:#cbd5e1;font-size:11px;font-weight:700;' +
                'text-align:center;transition:background .15s,border-color .15s,color .15s;cursor:pointer;position:relative;" ' +
                'aria-label="' + label + '">' +
                '<span style="font-size:22px;line-height:1;">' + icon + '</span>' +
                '<span style="line-height:1.2;">' + label + '</span>' +
                '</button>';
        };

        return '<div id="a11yPanel" role="dialog" aria-modal="true" aria-labelledby="a11yPanelTitle" ' +
            'style="pointer-events:auto;display:none;position:fixed;bottom:90px;left:24px;z-index:99999;width:320px;max-height:85vh;' +
            'overflow-y:auto;background:#0f172a;border:1px solid #334155;border-radius:20px;box-shadow:0 24px 64px rgba(0,0,0,.5);' +
            'padding:20px 16px 16px;color:#e2e8f0;">' +

            /* Header */
            '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">' +
                '<div id="a11yPanelTitle" style="font-size:14px;font-weight:800;color:#f8fafc;display:flex;align-items:center;gap:8px;">' +
                    '<i class="fa-solid fa-universal-access" style="color:#F97316;font-size:18px;"></i>' +
                    'Accessibility Menu <span style="font-size:10px;color:#94a3b8;font-weight:600;">(CTRL+U)</span>' +
                '</div>' +
                '<button id="a11yCloseBtn" type="button" aria-label="Close Accessibility Menu" ' +
                    'style="pointer-events:auto;background:none;border:none;color:#94a3b8;font-size:18px;cursor:pointer;padding:4px;">' +
                    '<i class="fa-solid fa-xmark"></i></button>' +
            '</div>' +

            /* Grid */
            '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">' +
                card('a11yCardContrast',   '<i class="fa-solid fa-circle-half-stroke"></i>', 'Contrast +') +
                card('a11yCardHL',         '<i class="fa-solid fa-link"></i>',               'Highlight Links') +
                card('a11yCardBigText',    '<span style="font-size:26px;font-weight:900;font-family:serif;">TT</span>', 'Bigger Text') +
                card('a11yCardSpacing',    '<i class="fa-solid fa-arrows-left-right"></i>',  'Text Spacing') +
                card('a11yCardPause',      '<i class="fa-solid fa-circle-pause"></i>',       'Pause Animations') +
                card('a11yCardHideImg',    '<i class="fa-solid fa-image"></i>',              'Hide Images') +
                card('a11yCardDyslexia',   '<span style="font-size:22px;font-weight:900;">Df</span>', 'Dyslexia Friendly') +
                card('a11yCardCursor',     '<i class="fa-solid fa-arrow-pointer"></i>',      'Cursor') +
                card('a11yCardTooltips',   '<i class="fa-solid fa-message"></i>',            'Tooltips') +
                card('a11yCardLineHeight', '<i class="fa-solid fa-text-height"></i>',        'Line Height') +
                card('a11yCardAlignLeft',  '<i class="fa-solid fa-align-left"></i>',         'Align Left') +
                card('a11yCardSaturation', '<i class="fa-solid fa-droplet"></i>',            'Saturation') +
            '</div>' +

            /* Footer */
            '<div style="display:flex;justify-content:space-between;align-items:center;margin-top:14px;padding-top:12px;border-top:1px solid #334155;">' +
                '<button id="a11yResetBtn" type="button" style="pointer-events:auto;background:#1e293b;border:1px solid #475569;color:#e2e8f0;padding:6px 14px;' +
                    'border-radius:10px;font-size:11px;font-weight:700;cursor:pointer;" aria-label="Reset Accessibility Settings">Reset</button>' +
                '<span style="font-size:10px;color:#64748b;font-weight:600;display:flex;align-items:center;gap:4px;">' +
                    '<i class="fa-solid fa-shield-check" style="color:#10b981;"></i> StatSkill AI Accessible</span>' +
            '</div>' +

        '</div>';
    }

    /* ── Update Panel Card States ──────────────────────────── */
    function updatePanelUI() {
        var ACTIVE_BG     = '#1d4ed8';
        var ACTIVE_BORDER = '#60a5fa';
        var ACTIVE_COLOR  = '#ffffff';
        var OFF_BG        = '#1e293b';
        var OFF_BORDER    = '#334155';
        var OFF_COLOR     = '#cbd5e1';

        function setCard(id, active, extraLabel, badgeStyle, customBg, customColor, customBorder, customCheckBg, customCheckColor) {
            var el = document.getElementById(id);
            if (!el) return;
            el.style.background  = active ? (customBg || ACTIVE_BG) : OFF_BG;
            el.style.borderColor = active ? (customBorder || ACTIVE_BORDER) : OFF_BORDER;
            el.style.color       = active ? (customColor || ACTIVE_COLOR) : OFF_COLOR;

            var check = el.querySelector('.a11y-check');
            if (active && !check) {
                var c = document.createElement('span');
                c.className = 'a11y-check';
                c.style.cssText = 'position:absolute;top:4px;right:4px;width:20px;height:20px;border-radius:50%;background:' + (customCheckBg || '#10b981') + ';color:' + (customCheckColor || '#ffffff') + ';font-size:10px;font-weight:900;display:flex;align-items:center;justify-content:center;box-shadow:0 0 10px ' + (customCheckBg || '#10b981') + ';border:2px solid ' + (customCheckColor || '#ffffff') + ';z-index:2;';
                c.innerHTML = '<i class="fa-solid fa-check"></i>';
                el.appendChild(c);
            } else if (active && check) {
                check.style.background = customCheckBg || '#10b981';
                check.style.color = customCheckColor || '#ffffff';
                check.style.borderColor = customCheckColor || '#ffffff';
            } else if (!active && check) {
                check.remove();
            }

            var lab = el.querySelector('.a11y-sublabel');
            if (extraLabel) {
                if (!lab) {
                    lab = document.createElement('span');
                    lab.className = 'a11y-sublabel';
                    el.appendChild(lab);
                }
                var baseStyle = 'font-size:10px;font-weight:900;margin-top:4px;padding:3px 8px;border-radius:12px;display:inline-flex;align-items:center;gap:5px;line-height:1.2;';
                lab.style.cssText = baseStyle + (badgeStyle || 'background:rgba(255,255,255,0.25);color:#ffffff;border:1px solid rgba(255,255,255,0.4);');
                lab.innerHTML = '<span style="width:8px;height:8px;border-radius:50%;background:currentColor;display:inline-block;flex-shrink:0;box-shadow:0 0 6px currentColor;"></span><span>' + extraLabel + '</span>';
            } else if (lab) {
                lab.remove();
            }
        }

        if (settings.contrastLevel === 1) {
            setCard('a11yCardContrast', true, 'High Contrast', 'background:#000000;color:#ffffff;border:1px solid #ffffff;', '#ffffff', '#000000', '#ffffff', '#000000', '#ffffff');
        } else if (settings.contrastLevel === 2) {
            setCard('a11yCardContrast', true, 'Yellow on Black', 'background:#000000;color:#fde047;border:1px solid #fde047;', '#fde047', '#000000', '#fde047', '#000000', '#fde047');
        } else if (settings.contrastLevel === 3) {
            setCard('a11yCardContrast', true, 'Blue on Cream', 'background:#0b2545;color:#fdf6e2;border:1px solid #0b2545;', '#fdf6e2', '#0b2545', '#0b2545', '#0b2545', '#fdf6e2');
        } else {
            setCard('a11yCardContrast', false);
        }

        setCard('a11yCardHL',         settings.highlightLinks);
        setCard('a11yCardBigText',    settings.biggerText);
        setCard('a11yCardSpacing',    settings.textSpacing);
        setCard('a11yCardPause',      settings.pauseAnimations);
        setCard('a11yCardHideImg',    settings.hideImages);
        setCard('a11yCardDyslexia',   settings.dyslexiaFriendly);
        setCard('a11yCardCursor',     settings.largeCursor);
        setCard('a11yCardTooltips',   settings.tooltips);
        setCard('a11yCardLineHeight', settings.lineHeight);
        setCard('a11yCardAlignLeft',  settings.alignLeft);
        setCard('a11yCardSaturation', settings.saturation > 0, settings.saturation === 1 ? 'Low Saturation' : (settings.saturation === 2 ? 'Grayscale' : null), 'background:#f97316;color:#ffffff;');

        // Active indicator badge dot on trigger button & navbar buttons
        var isAnyActive = (settings.contrastLevel > 0 || settings.highlightLinks || settings.biggerText || 
                           settings.textSpacing || settings.pauseAnimations || settings.hideImages || 
                           settings.dyslexiaFriendly || settings.largeCursor || settings.lineHeight || 
                           settings.alignLeft || settings.saturation > 0 || settings.tooltips);

        var trigger = document.getElementById('a11yTrigger');
        if (trigger) {
            var triggerDot = trigger.querySelector('.a11y-trigger-dot');
            if (isAnyActive && !triggerDot) {
                var d = document.createElement('span');
                d.className = 'a11y-trigger-dot';
                d.style.cssText = 'position:absolute;top:-2px;right:-2px;width:18px;height:18px;border-radius:50%;background:#10b981;border:2px solid #ffffff;box-shadow:0 0 10px #10b981;z-index:3;';
                trigger.appendChild(d);
            } else if (!isAnyActive && triggerDot) {
                triggerDot.remove();
            }
        }

        var navBtns = document.querySelectorAll('[onclick*="toggleAccessibilityPanel"]');
        for (var i = 0; i < navBtns.length; i++) {
            var btn = navBtns[i];
            var navDot = btn.querySelector('.a11y-nav-dot');
            if (isAnyActive && !navDot) {
                var nd = document.createElement('span');
                nd.className = 'a11y-nav-dot';
                nd.style.cssText = 'width:8px;height:8px;border-radius:50%;background:#10b981;display:inline-block;box-shadow:0 0 8px #10b981;margin-left:5px;border:1px solid #ffffff;vertical-align:middle;';
                btn.appendChild(nd);
            } else if (!isAnyActive && navDot) {
                navDot.remove();
            }
        }
    }

    /* ── Event Binding ─────────────────────────────────────── */
    function bindWidgetEvents() {
        var trigger  = document.getElementById('a11yTrigger');
        var closeBtn = document.getElementById('a11yCloseBtn');
        var resetBtn = document.getElementById('a11yResetBtn');

        if (trigger) trigger.addEventListener('click', function (e) { e.stopPropagation(); togglePanel(); });
        if (closeBtn) closeBtn.addEventListener('click', function (e) { e.stopPropagation(); closePanel(); });
        if (resetBtn) resetBtn.addEventListener('click', function (e) { e.stopPropagation(); resetAll(); });

        function bind(id, fn) {
            var el = document.getElementById(id);
            if (el) el.addEventListener('click', function (e) { e.stopPropagation(); fn(); });
        }

        bind('a11yCardContrast',   function () { settings.contrastLevel = (settings.contrastLevel + 1) % 4; applyAll(); });
        bind('a11yCardHL',         function () { settings.highlightLinks = !settings.highlightLinks; applyAll(); });
        bind('a11yCardBigText',    function () { settings.biggerText = !settings.biggerText; applyAll(); });
        bind('a11yCardSpacing',    function () { settings.textSpacing = !settings.textSpacing; applyAll(); });
        bind('a11yCardPause',      function () { settings.pauseAnimations = !settings.pauseAnimations; applyAll(); });
        bind('a11yCardHideImg',    function () { settings.hideImages = !settings.hideImages; applyAll(); });
        bind('a11yCardDyslexia',   function () { settings.dyslexiaFriendly = !settings.dyslexiaFriendly; applyAll(); });
        bind('a11yCardCursor',     function () { settings.largeCursor = !settings.largeCursor; applyAll(); });
        bind('a11yCardTooltips',   function () { settings.tooltips = !settings.tooltips; applyAll(); });
        bind('a11yCardLineHeight', function () { settings.lineHeight = !settings.lineHeight; applyAll(); });
        bind('a11yCardAlignLeft',  function () { settings.alignLeft = !settings.alignLeft; applyAll(); });
        bind('a11yCardSaturation', function () { settings.saturation = (settings.saturation + 1) % 3; applyAll(); });

    var justToggled = false;

    // Keyboard Shortcuts (CTRL+U or ALT+A)
    document.addEventListener('keydown', function (e) {
        if ((e.ctrlKey && e.key.toLowerCase() === 'u') || (e.altKey && e.key.toLowerCase() === 'a')) {
            e.preventDefault(); togglePanel();
        } else if (e.key === 'Escape' && panelOpen) {
            closePanel();
        }
    });

    // Click outside closes panel (ignores opening clicks)
    document.addEventListener('click', function (e) {
        if (!panelOpen || justToggled) return;
        var widget = document.getElementById('a11yWidget');
        if (e.target.closest && e.target.closest('[onclick*="toggleAccessibilityPanel"]')) return;
        if (widget && !widget.contains(e.target)) closePanel();
    });
}

/* ── Panel Open / Close ────────────────────────────────── */
function togglePanel(e) {
    if (e && e.stopPropagation) e.stopPropagation();
    panelOpen ? closePanel() : openPanel();
}

function openPanel() {
    buildWidget();
    var panel = document.getElementById('a11yPanel');
    var trigger = document.getElementById('a11yTrigger');
    if (panel) {
        panel.style.display = 'block';
        panelOpen = true;
        justToggled = true;
        setTimeout(function () { justToggled = false; }, 250);
    }
    if (trigger) trigger.setAttribute('aria-expanded', 'true');
    updatePanelUI();
}

function closePanel() {
    var panel = document.getElementById('a11yPanel');
    var trigger = document.getElementById('a11yTrigger');
    if (panel) { panel.style.display = 'none'; panelOpen = false; }
    if (trigger) trigger.setAttribute('aria-expanded', 'false');
}

    /* ── Reset All ─────────────────────────────────────────── */
    function resetAll() {
        for (var k in DEFAULTS) settings[k] = DEFAULTS[k];
        applyAll();
    }

    /* ── Global API Exports (Available IMMEDIATELY) ────────── */
    window.accessibilityManager = {
        togglePanel: togglePanel,
        openPanel: openPanel,
        closePanel: closePanel,
        resetAll: resetAll,
        getSettings: function () { return settings; }
    };

    window.toggleAccessibilityPanel = togglePanel;

    /* ── Boot ──────────────────────────────────────────────── */
    function boot() {
        injectCSS();
        buildWidget();
        applyAll();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }

})();
