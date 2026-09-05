/**
 * StatSkill AI Virtual Assistant Component
 * Floating RAG-powered chatbot providing grounded official statistics explanations and learning guidance.
 */

function renderAiAssistant(state) {
    const isChatOpen = state.isChatOpen;
    const messages = state.chatMessages;

    return `
    <!-- Floating AI Trigger Button -->
    <div class="floating-ai-btn">
        <button onclick="store.toggleChat()" aria-label="${tr('Ask learning assistant')}" class="w-14 h-14 rounded-full bg-navy-900 text-white flex items-center justify-center text-xl shadow-2xl border-2 border-orange-500 hover:scale-105 transition-all" style="background: #0B2545;" title="Ask StatSkill AI Assistant">
            <i class="fa-solid ${isChatOpen ? 'fa-xmark' : 'fa-robot'} text-orange-400"></i>
        </button>
    </div>

    <!-- Floating Chat Window -->
    <div class="ai-chat-window ${isChatOpen ? '' : 'hidden'}" id="aiChatWindow">
        <!-- Header -->
        <div class="p-4 bg-navy-900 text-white flex justify-between items-center border-b border-slate-700" style="background: #0B2545;">
            <div class="flex items-center gap-2.5">
                <div class="w-8 h-8 rounded-full bg-orange-500 text-white flex items-center justify-center text-sm shadow">
                    <i class="fa-solid fa-robot"></i>
                </div>
                <div>
                    <h3 class="text-xs font-black tracking-wide">StatSkill AI Assistant</h3>
                    <div class="flex items-center gap-1.5 text-[10px] text-emerald-400 font-bold">
                        <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> Learning support
                    </div>
                </div>
            </div>
            <button aria-label="Close assistant" onclick="store.toggleChat()" class="text-slate-400 hover:text-white text-base">
                <i class="fa-solid fa-xmark"></i>
            </button>
        </div>

        <!-- Prompt Suggestions Pills -->
        <div class="p-2.5 bg-slate-50 border-b border-slate-200 overflow-x-auto flex gap-1.5 text-[11px] whitespace-nowrap">
            <button onclick="sendQuickPrompt('What skills are required for my role?')" class="bg-white border border-slate-200 text-slate-700 px-2.5 py-1 rounded-full hover:bg-orange-50 hover:text-orange-700 hover:border-orange-300">
                ⚡ Skills for my role
            </button>
            <button onclick="sendQuickPrompt('Explain sampling in simple terms.')" class="bg-white border border-slate-200 text-slate-700 px-2.5 py-1 rounded-full hover:bg-orange-50 hover:text-orange-700 hover:border-orange-300">
                ⚡ Sampling in NSSO
            </button>
            <button onclick="sendQuickPrompt('Why was this course recommended?')" class="bg-white border border-slate-200 text-slate-700 px-2.5 py-1 rounded-full hover:bg-orange-50 hover:text-orange-700 hover:border-orange-300">
                ⚡ Why recommended?
            </button>
        </div>

        <!-- Chat Messages Body -->
        <div class="flex-1 p-4 overflow-y-auto space-y-4 text-xs bg-slate-50/50" id="chatMessagesWrapper" role="log" aria-live="polite">${!messages.length?empty("Ask about your learning or uploaded materials."):""}
            ${messages.map(msg => `
                <div class="flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'} space-y-1">
                    <div class="max-w-[85%] p-3 rounded-2xl ${msg.sender === 'user' ? 'bg-navy-900 text-white rounded-br-none' : 'bg-white text-slate-800 border border-slate-200 rounded-bl-none shadow-sm'}" style="${msg.sender === 'user' ? 'background: #0B2545;' : ''}">
                        <div class="leading-relaxed whitespace-pre-line">${formatAiText(msg.text)}</div>
                        ${sourceButtons(msg.sources || [])}

                    </div>
                    <span class="text-[9px] text-slate-400 px-1">${esc(msg.timestamp || 'Now')}</span>
                </div>
            `).join('')}
        </div>

        <!-- Disclaimer Bar -->
        <div class="px-3 py-1 bg-amber-50 border-t border-amber-100 text-[10px] text-amber-900 text-center font-medium">
            AI-generated responses should be verified against official training materials and applicable guidelines.
        </div>

        ${state.error ? `<p role="alert" class="live-error">${esc(userFacingError(state.error))}</p>` : ''}
        ${state.busy ? `<p role="status" class="live-status">${tr('Working…')}</p>` : ''}
        <!-- Chat Input Footer -->
        <div class="p-3 bg-white border-t border-slate-200 flex items-center gap-2">
            <input type="text" id="chatInputBox" aria-label="Message" onkeypress="handleChatKeyPress(event)" placeholder="Ask about competencies, NSSO surveys, courses..." class="flex-1 p-2 text-xs rounded-xl border border-slate-300 focus:outline-none focus:border-navy-900">
            <button aria-label="Send" ${state.busy?'disabled':''} onclick="submitChat()" class="w-9 h-9 rounded-xl bg-orange-600 hover:bg-orange-700 text-white flex items-center justify-center text-xs shadow-md">
                <i class="fa-solid fa-paper-plane"></i>
            </button>
        </div>
    </div>
    `;
}

function formatAiText(text) {
    // Basic Markdown support for bolding and code
    return esc(text).replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
}

function sendQuickPrompt(promptText) {
    window.store.sendChatMessage(promptText);
    scrollChatBottom();
}

function submitChat() {
    const input = document.getElementById('chatInputBox');
    if (input && input.value.trim()) {
        const text = input.value.trim();
        input.value = '';
        window.store.sendChatMessage(text);
        scrollChatBottom();
    }
}

function handleChatKeyPress(e) {
    if (e.key === 'Enter') {
        submitChat();
    }
}

function scrollChatBottom() {
    setTimeout(() => {
        const wrapper = document.getElementById('chatMessagesWrapper');
        if (wrapper) wrapper.scrollTop = wrapper.scrollHeight;
    }, 100);
}

window.renderAiAssistant = renderAiAssistant;
window.sendQuickPrompt = sendQuickPrompt;
window.submitChat = submitChat;
window.handleChatKeyPress = handleChatKeyPress;
