/* Aura: minimal, accessible voice chat. No external JS or HTML injection dependencies. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const ns = 'http://www.w3.org/2000/svg';
  const storageGet = key => { try { return sessionStorage.getItem(key); } catch (_) { return null; } };
  const storageSet = (key,value) => { try { sessionStorage.setItem(key,value); } catch (_) {} };
  const state = {
    history: [], pending: false, listening: false, recognition: null,
    autoSpeak: storageGet('aura:speak') !== 'false',
    mode: 'demo', aborter: null, speechBuffer: '', currentReply: null,
    topics: null, profile: { education: '', interests: '', goals: '' }
  };
  let toastTimer;
  const node = (tag, cls = '', text) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = String(text);
    return e;
  };
  const svg = name => {
    const s = document.createElementNS(ns, 'svg');
    const use = document.createElementNS(ns, 'use');
    use.setAttribute('href', '#i-' + name); s.appendChild(use); return s;
  };
  const append = (parent, child) => (parent.appendChild(child), child);
  function toast(message) {
    $('toast').textContent = message;
    $('toast').classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => $('toast').classList.remove('show'), 4500);
  }
  function setMode(mode) {
    state.mode = mode;
    $('modeChip').className = 'mode-chip' + (mode === 'gemini' ? ' live' : mode === 'fallback' ? ' warning' : '');
    $('modeChip').textContent = mode === 'gemini' ? 'Gemini AI' : mode === 'fallback' ? 'Demo fallback' : 'Knowledge demo';
    $('systemStatus').textContent = mode === 'gemini' ? 'AI + RAG ready' : 'Knowledge demo ready';
  }
  async function checkHealth() {
    try {
      const r = await fetch('/api/health');
      if (!r.ok) throw new Error('Server error');
      const data = await r.json();
      setMode(data.mode);
      $('sidebarStatusDot').classList.remove('unavailable');
    } catch (_) {
      $('sidebarStatusDot').classList.add('unavailable');
      $('systemStatus').textContent = 'Server offline';
      $('modeChip').textContent = 'Offline';
      toast('Server not responding. Run start-windows.ps1 and reload.');
    }
  }
  function saveProfile() { storageSet('aura:profile', JSON.stringify(state.profile)); }
  function restoreProfile() {
    try {
      const p = JSON.parse(storageGet('aura:profile') || '{}');
      for (const key of Object.keys(state.profile)) state.profile[key] = typeof p[key] === 'string' ? p[key] : '';
    } catch (_) {}
  }
  function saveConversation() {
    storageSet('aura:conversation', JSON.stringify(state.history));
  }
  function restoreConversation() {
    try {
      const parsed = JSON.parse(storageGet('aura:conversation') || '[]');
      if (!Array.isArray(parsed)) return;
      state.history = parsed.filter(t => t && ['user', 'assistant'].includes(t.role) && typeof t.content === 'string')
        .slice(-12).map(t => ({ role: t.role, content: t.content.slice(0, 1600) }));
      state.history.forEach(t => {
        const msg = addMessage(t.role, false);
        if (t.role === 'user') msg.bubble.textContent = t.content;
        else renderMarkdown(msg.bubble, t.content);
      });
      if (state.history.length) $('emptyState').hidden = true;
    } catch (_) { state.history = []; }
  }
  function atBottom() {
    const c = $('chatScroll'); return c.scrollHeight - c.scrollTop - c.clientHeight < 170;
  }
  function scrollBottom(force = false) {
    if (force || atBottom()) $('chatScroll').scrollTop = $('chatScroll').scrollHeight;
  }
  function hideIntro() { $('emptyState').hidden = true; }
  function addMessage(role, streaming = false) {
    hideIntro();
    const wrap = append($('chatMessages'), node('article', 'message ' + role));
    const body = append(wrap, node('div', 'message-body'));
    if (role === 'assistant') {
      const head = append(body, node('div', 'assistant-head'));
      append(head, node('div', 'assistant-avatar', '✳'));
      append(head, node('span', '', 'Aura'));
    }
    const bubble = append(body, node('div', 'message-bubble' + (streaming ? ' streaming' : '')));
    const actions = role === 'assistant' ? append(body, node('div', 'message-actions')) : null;
    if (streaming) {
      const dots = append(bubble, node('span', 'waiting'));
      for (let i = 0; i < 3; i++) append(dots, node('i'));
    }
    scrollBottom(true);
    return { wrap, bubble, actions };
  }
  function inlineFormat(container, value) {
    const pattern = /(\*\*[^*\n]+\*\*|`[^`\n]+`|\[[^\]]+\]\(https?:\/\/[^)\s]+\))/g;
    let index = 0; let m;
    while ((m = pattern.exec(value))) {
      if (m.index > index) append(container, document.createTextNode(value.slice(index, m.index)));
      const part = m[0];
      if (part.startsWith('**')) append(container, node('strong', '', part.slice(2, -2)));
      else if (part.startsWith('`')) append(container, node('code', '', part.slice(1, -1)));
      else {
        const sep = part.indexOf('](');
        const link = node('a', '', part.slice(1, sep));
        link.href = part.slice(sep + 2, -1);
        link.target = '_blank'; link.rel = 'noopener noreferrer';
        append(container, link);
      }
      index = pattern.lastIndex;
    }
    if (index < value.length) append(container, document.createTextNode(value.slice(index)));
  }
  function renderMarkdown(root, text) {
    // Markdown-like formatting built solely with DOM/text nodes to avoid untrusted HTML.
    root.replaceChildren();
    let paragraph = [], currentList = null, codeLines = null;
    function flushParagraph() {
      if (!paragraph.length) return;
      const p = append(root, node('p'));
      inlineFormat(p, paragraph.join(' ').trim());
      paragraph = [];
    }
    function flushCode() {
      if (codeLines === null) return;
      const pre = append(root, node('pre'));
      append(pre, node('code', '', codeLines.join('\n')));
      codeLines = null;
    }
    for (const line of text.replace(/\r\n?/g,'\n').split('\n')) {
      if (/^\s*```/.test(line)) {
        flushParagraph(); currentList = null;
        if (codeLines === null) codeLines = []; else flushCode();
        continue;
      }
      if (codeLines !== null) { codeLines.push(line); continue; }
      const trimmed = line.trim();
      if (!trimmed) { flushParagraph(); currentList = null; continue; }
      const heading = /^(#{1,4})\s+(.+)$/.exec(trimmed);
      const bullet = /^([-*]|\d+[.)])\s+(.+)$/.exec(trimmed);
      if (heading) {
        flushParagraph(); currentList = null;
        inlineFormat(append(root,node(heading[1].length === 1 ? 'h2' : 'h3')),heading[2]);
      } else if (bullet) {
        flushParagraph();
        const kind = /^\d/.test(bullet[1]) ? 'ol' : 'ul';
        if (!currentList || currentList.tagName.toLowerCase() !== kind) currentList = append(root,node(kind));
        inlineFormat(append(currentList,node('li')),bullet[2]);
      } else if (/^>\s?/.test(trimmed)) {
        flushParagraph(); currentList = null;
        inlineFormat(append(root,node('blockquote')),trimmed.replace(/^>\s?/,''));
      } else { currentList = null; paragraph.push(trimmed); }
    }
    flushParagraph(); flushCode();
  }
  function addTool(container, name, label, onClick) {
    const button = append(container, node('button', 'mini-action'));
    button.type = 'button'; button.title = label; button.setAttribute('aria-label', label);
    button.appendChild(svg(name));
    button.addEventListener('click', onClick);
    return button;
  }
  function finishMessage(msg, data) {
    msg.bubble.classList.remove('streaming');
    renderMarkdown(msg.bubble, data.text.trim());
    if (!data.text.trim()) return;
    addTool(msg.actions,'copy','Copy answer',async () => {
      try { await navigator.clipboard.writeText(data.text.trim()); toast('Answer copied'); }
      catch (_) { toast('Clipboard unavailable. Select and copy the text.'); }
    });
    addTool(msg.actions, 'volume', 'Read this answer aloud', () => { stopSpeech(); speak(data.text.trim(), true); });
    if (data.sources.length) {
      const button = addTool(msg.actions, 'book', 'View retrieved career sources', () => {
        if (sourcePanel.hidden) { sourcePanel.hidden = false; button.title = 'Hide career sources'; }
        else { sourcePanel.hidden = true; button.title = 'View career sources'; }
      });
      append(button, node('span', '', data.sources.length + ' sources'));
      const sourcePanel = append(msg.actions.parentNode, node('div','inline-sources'));
      sourcePanel.hidden = true;
      append(sourcePanel,node('h4','','Career references used for this answer'));
      data.sources.forEach(s => {
        const line = append(sourcePanel,node('div','source-item',s.title || 'Career note'));
        append(line,node('small','',s.cluster || 'Career information'));
      });
    }
    if (typeof data.totalMs === 'number')
      append(msg.actions,node('span','message-metric', `${(data.totalMs/1000).toFixed(1)}s · ${data.mode==='gemini'?'Gemini + RAG':'Knowledge demo'}`));
    if (data.notice) {
      append(msg.actions,node('span','message-metric', data.notice));
      toast(data.notice);
    }
  }
  function setBusy(flag) {
    state.pending = flag;
    $('sendButton').hidden = flag; $('stopButton').hidden = !flag;
    $('sendButton').disabled = flag; $('micButton').disabled = flag;
    $('messageInput').disabled = flag;
    $('footerHint').textContent = flag ? 'Generating a response… use Stop to interrupt.' :
      'Answers use a career knowledge base. AI can make mistakes; verify important decisions.';
  }
  function stopSpeech() {
    state.speechBuffer = '';
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
  }
  function speak(text, force = false) {
    if ((!state.autoSpeak && !force) || !text.trim() || !('speechSynthesis' in window) || !('SpeechSynthesisUtterance' in window)) return;
    const u = new SpeechSynthesisUtterance(text.trim().replace(/[*#`_]/g, ''));
    u.lang = 'en-IN'; u.rate = 1.02;
    const voices = window.speechSynthesis.getVoices();
    u.voice = voices.find(v => v.lang.toLowerCase() === 'en-in') || voices.find(v => v.lang.toLowerCase().startsWith('en')) || null;
    window.speechSynthesis.speak(u);
  }
  function speakProgress(delta) {
    if (!state.autoSpeak) return;
    state.speechBuffer += delta;
    const sentence = /^([\s\S]*?[.!?])(?=\s|$)/;
    let match;
    while ((match = state.speechBuffer.match(sentence))) {
      speak(match[1]); state.speechBuffer = state.speechBuffer.slice(match[0].length).trimStart();
    }
  }
  function finishSpeech() {
    if (state.speechBuffer.trim()) speak(state.speechBuffer);
    state.speechBuffer = '';
  }
  function updateSpeechButton() {
    $('soundButton').replaceChildren(svg(state.autoSpeak ? 'volume' : 'mute'));
    $('soundButton').setAttribute('aria-label', state.autoSpeak ? 'Mute spoken replies' : 'Enable spoken replies');
    $('soundButton').title = state.autoSpeak ? 'Mute spoken replies' : 'Enable spoken replies';
  }
  function toggleSpeech() {
    state.autoSpeak = !state.autoSpeak;
    storageSet('aura:speak', String(state.autoSpeak));
    if (!state.autoSpeak) stopSpeech();
    updateSpeechButton(); toast(state.autoSpeak ? 'Voice replies on' : 'Voice replies muted');
  }
  function resizeInput() {
    const i = $('messageInput'); i.style.height = '26px';
    i.style.height = Math.min(i.scrollHeight,170) + 'px';
  }
  function consumeSSE(packet, onEvent) {
    let event = 'message', raw = [];
    for (const line of packet.split(/\r?\n/)) {
      if (line.startsWith('event:')) event = line.slice(6).trim();
      if (line.startsWith('data:')) raw.push(line.slice(5).trimStart());
    }
    if (raw.length) {
      try { onEvent(event, JSON.parse(raw.join('\n'))); }
      catch (_) { /* Ignore malformed provider event, surface missing done event later. */ }
    }
  }
  async function sendMessage(value) {
    const input = $('messageInput');
    const question = String(value === undefined ? input.value : value).trim();
    if (!question || state.pending) return;
    if (question.length > 1600) { toast('Max 1600 characters.'); return; }
    stopSpeech(); stopListening();
    input.value = ''; resizeInput();
    const user = addMessage('user'); user.bubble.textContent = question;
    const msg = addMessage('assistant', true);
    const result = {text:'',sources:[],totalMs:null,mode:state.mode,notice:null,done:false};
    const prior = state.history.slice(-12);
    let frameQueued = false;
    function paintLatest() {
      if (frameQueued) return;
      frameQueued = true;
      requestAnimationFrame(() => {
        frameQueued = false;
        if (state.currentReply !== msg) return;
        renderMarkdown(msg.bubble, result.text); scrollBottom();
      });
    }
    setBusy(true);
    state.currentReply = msg;
    state.aborter = new AbortController();
    const aborter = state.aborter;
    const handle = (type, data) => {
      if (type === 'sources') result.sources = data.sources || [];
      else if (type === 'delta') {
        result.text += String(data.text || '');
        paintLatest();
        speakProgress(String(data.text || ''));
      } else if (type === 'done') {
        result.done = true; result.mode = data.mode; result.notice = data.notice;
        result.totalMs = data.total_ms;
        if (typeof data.answer === 'string') result.text = data.answer;
      }
    };
    try {
      const r = await fetch('/api/chat/stream',{
        method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({message:question,history:prior,profile:state.profile}),signal:aborter.signal
      });
      if (!r.ok) {
        const b = await r.json().catch(() => ({}));
        throw Error(r.status === 429 ? 'Too many requests. Please wait a minute.' : b.detail || `Server error ${r.status}`);
      }
      if (!r.body) throw Error('Streaming is not available in this browser.');
      const reader = r.body.getReader(), decoder = new TextDecoder();
      let buffer = '';
      while (true) {
        const {value,done} = await reader.read();
        if (done) break;
        buffer += decoder.decode(value,{stream:true});
        let found;
        while ((found = /\r?\n\r?\n/.exec(buffer))) {
          consumeSSE(buffer.slice(0,found.index),handle);
          buffer = buffer.slice(found.index + found[0].length);
        }
      }
      buffer += decoder.decode();
      if (buffer.trim()) consumeSSE(buffer,handle);
      if (!result.done) throw Error('The server stopped before finishing this answer.');
      if (!result.text.trim()) throw Error('No answer was returned.');
      finishSpeech();
      setMode(result.mode);
      state.history.push({role:'user',content:question},{role:'assistant',content:result.text.trim()});
      state.history = state.history.slice(-12); saveConversation();
    } catch (e) {
      stopSpeech();
      if (e.name === 'AbortError') {
        result.notice = 'Stopped';
      } else {
        result.notice = e.message || 'Connection interrupted';
        toast('Response interrupted: ' + result.notice);
      }
      if (!result.text.trim()) result.text = e.name === 'AbortError' ? 'Response stopped.' :
        'I could not finish that reply. Please try asking again.';
      else {
        state.history.push({role:'user',content:question},{role:'assistant',content:result.text.trim()});
        state.history = state.history.slice(-12); saveConversation();
      }
    } finally {
      finishMessage(msg,result);
      if (state.aborter === aborter) { state.aborter = null; state.currentReply = null; }
      setBusy(false); scrollBottom(); input.focus();
    }
  }
  function stopGenerating() {
    if (state.aborter) state.aborter.abort();
    stopSpeech();
  }
  function stopListening() {
    const rec = state.recognition;
    state.recognition = null; state.listening = false;
    if (rec) { try { rec.abort(); } catch (_) {} }
    $('micButton').classList.remove('listening');
    $('micButton').setAttribute('aria-label','Start voice recording');
    $('listeningIndicator').hidden = true;
  }
  function startListening() {
    if (state.pending) return;
    if (state.listening) { stopListening(); return; }
    const Rec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Rec) { toast('Microphone transcription needs Chrome or Edge. You can also type your question.'); return; }
    if (!window.isSecureContext) { toast('Microphone requires HTTPS or localhost.'); return; }
    stopSpeech();
    const rec = new Rec(); state.recognition = rec;
    rec.lang = /^en/i.test(navigator.language) ? navigator.language : 'en-IN';
    rec.interimResults = true; rec.continuous = false; rec.maxAlternatives = 1;
    let transcript = '', failed = false;
    rec.onstart = () => {
      if (state.recognition !== rec) return;
      state.listening = true;
      $('micButton').classList.add('listening');
      $('micButton').setAttribute('aria-label','Stop voice recording');
      $('listeningIndicator').hidden = false;
    };
    rec.onresult = ev => {
      if (state.recognition !== rec) return;
      let partial = '';
      for (let i = 0; i < ev.results.length; i++) {
        const t = ev.results[i][0].transcript;
        if (ev.results[i].isFinal) transcript += (transcript ? ' ' : '') + t;
        else partial += (partial ? ' ' : '') + t;
      }
      $('messageInput').value = (transcript + ' ' + partial).trim(); resizeInput();
    };
    rec.onerror = e => {
      if (e.error === 'aborted') return;
      failed = true;
      const hints = {'not-allowed':'Allow microphone permission in your browser.', 'no-speech':'No speech detected. Try again.',
        network:'Browser speech recognition is unavailable. Try typing.'};
      toast(hints[e.error] || 'Speech recognition failed. Try typing.');
    };
    rec.onend = () => {
      if (state.recognition !== rec) return;
      state.recognition = null; state.listening = false;
      $('micButton').classList.remove('listening'); $('listeningIndicator').hidden = true;
      if (!failed && transcript.trim()) sendMessage(transcript.trim());
    };
    try { rec.start(); }
    catch (_) { stopListening(); toast('Could not start the microphone. Check permissions.'); }
  }
  function newChat() {
    if (state.pending) { toast('Stop the current reply before starting a new chat.'); return; }
    stopSpeech(); stopListening();
    state.history = []; saveConversation();
    $('chatMessages').replaceChildren(); $('emptyState').hidden = false;
    $('messageInput').value = ''; resizeInput(); closeSidebar(); $('messageInput').focus();
  }
  function openModal(title) {
    $('modalTitle').textContent = title; $('modalContent').replaceChildren();
    $('modalBackdrop').hidden = false;
    closeSidebar(); $('closeModal').focus();
    return $('modalContent');
  }
  function closeModal() { $('modalBackdrop').hidden = true; }
  function openProfile() {
    const area = openModal('Your career profile');
    append(area,node('p','','Optional details help Aura personalize career advice. They stay in your browser session; Gemini mode sends them to the AI provider when you ask a question.'));
    const fields = [ ['education','Education','e.g. BCA graduate',140], ['interests','Interests','e.g. AI, technology, design',180], ['goals','Career goal','e.g. Find my first job',180] ];
    for (const [key,label,placeholder,max] of fields) {
      const l = append(area,node('label','',label));
      const input = append(area,node('input'));
      input.id = 'profile-' + key; l.htmlFor = input.id;
      input.placeholder = placeholder; input.maxLength = max; input.value = state.profile[key];
      input.addEventListener('input',() => { state.profile[key] = input.value; saveProfile(); });
    }
    const done = append(area,node('button','dark-button','Save profile'));
    done.addEventListener('click',()=>{closeModal();toast('Profile saved for this session.');});
  }
  async function openExplore() {
    const area = openModal('Career library');
    append(area,node('p','','Explore the local career knowledge base and select a role to discuss.'));
    const search = append(area,node('input'));
    search.placeholder = 'Search by role or field...'; search.setAttribute('aria-label','Search careers');
    const list = append(area,node('div','topics'));
    if (!state.topics) {
      try {
        const r = await fetch('/api/topics'); if (!r.ok) throw Error('Could not load careers');
        state.topics = await r.json();
      } catch (_) { append(list,node('p','','Unable to load careers. Start the server and try again.')); return; }
    }
    function render() {
      list.replaceChildren();
      const q = search.value.toLowerCase();
      const matches = state.topics.filter(d => (d.title + ' ' + d.cluster).toLowerCase().includes(q));
      for (const d of matches) {
        const b = append(list,node('button','topic-item'));
        append(b,node('strong','',d.title)); append(b,node('small','',d.cluster));
        b.addEventListener('click',() => {closeModal();sendMessage(`Tell me about ${d.title}. What does the role involve, which skills do I need, and what are my first steps?`);});
      }
      if (!matches.length) append(list,node('p','','No matching careers.'));
    }
    search.addEventListener('input',render); render(); search.focus();
  }
  function openAbout() {
    const area = openModal('About Aura');
    [
      'Aura is a career guidance demonstration built for the MinuteHire AI Engineer assessment. It retrieves grounded career notes with hybrid TF-IDF + BM25 and rank fusion.',
      'With a configured Gemini API key, the AI generates responses as a live text stream. Without a key, Aura uses a clearly labelled knowledge-based demo; it is not a real LLM.',
      'Speech recognition and spoken answers use browser features; on some browsers speech recognition requires the vendor’s online service. Use Chrome or Edge on HTTPS/localhost.',
      'Conversation context is kept in this browser session rather than a server database. Gemini mode sends profile and conversation text to Google. Do not enter sensitive details.',
      'This is exploratory career advice, not guaranteed hiring, income, or admission advice.'
    ].forEach(t => append(area,node('p','',t)));
    const button = append(area,node('button','simple-button','Close'));
    button.addEventListener('click',closeModal);
  }
  function openSidebar() { $('sidebar').classList.add('open'); $('sidebarBackdrop').hidden = false; }
  function closeSidebar() { $('sidebar').classList.remove('open'); $('sidebarBackdrop').hidden = true; }
  function bind() {
    $('sendButton').addEventListener('click',() => sendMessage());
    $('stopButton').addEventListener('click',stopGenerating);
    $('messageInput').addEventListener('keydown',e => {
      if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {e.preventDefault();sendMessage();}
    });
    $('messageInput').addEventListener('input',resizeInput);
    $('micButton').addEventListener('click',startListening);
    $('soundButton').addEventListener('click',toggleSpeech);
    $('newChatButton').addEventListener('click',newChat);
    $('newChatTop').addEventListener('click',newChat);
    $('homeButton').addEventListener('click',() => {closeSidebar();$('messageInput').focus();});
    $('exploreButton').addEventListener('click',openExplore);
    $('profileButton').addEventListener('click',openProfile);
    $('aboutButton').addEventListener('click',openAbout);
    $('menuButton').addEventListener('click',openSidebar);
    $('closeSidebarButton').addEventListener('click',closeSidebar);
    $('sidebarBackdrop').addEventListener('click',closeSidebar);
    $('closeModal').addEventListener('click',closeModal);
    $('modalBackdrop').addEventListener('click',e => {if (e.target === $('modalBackdrop')) closeModal();});
    document.addEventListener('keydown',e => {if (e.key === 'Escape') {closeModal();closeSidebar();}});
    document.querySelectorAll('[data-question]').forEach(b => b.addEventListener('click',() => sendMessage(b.dataset.question)));
    updateSpeechButton(); resizeInput();
  }
  restoreProfile(); bind(); restoreConversation(); checkHealth();
})();
