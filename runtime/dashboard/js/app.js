// Tritium dashboard SPA.
// Vanilla ES modules. No framework. No CDN.

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

const view = $('#view');
const status = $('#status');
const dbInfo = $('#db-info');

// ─── Safe rendering helpers (no innerHTML for untrusted data) ──────────────
function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === 'class') node.className = v;
    else if (k === 'dataset') Object.assign(node.dataset, v);
    else if (k.startsWith('on') && typeof v === 'function') node.addEventListener(k.slice(2), v);
    else if (v !== false && v !== null && v !== undefined) node.setAttribute(k, v);
  }
  for (const c of [].concat(children)) {
    if (c == null || c === false) continue;
    node.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
  }
  return node;
}
function text(s) { return document.createTextNode(s == null ? '' : String(s)); }

function fmtTime(s) {
  if (!s) return '';
  // SQLite returns "YYYY-MM-DD HH:MM:SS" in UTC.
  const d = new Date(s.replace(' ', 'T') + 'Z');
  if (isNaN(d.getTime())) return s;
  const now = new Date();
  const sameDay = d.toDateString() === now.toDateString();
  return sameDay
    ? d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : d.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

// ─── API client ────────────────────────────────────────────────────────────
const api = {
  async health()  { return (await fetch('/api/health')).json(); },
  async agents()  { return (await fetch('/api/agents')).json(); },
  async settings(){ return (await fetch('/api/settings')).json(); },
  async im(agent) {
    const q = agent ? `?agent=${encodeURIComponent(agent)}` : '';
    return (await fetch(`/api/im${q}`)).json();
  },
  async sendIm(payload) {
    const r = await fetch('/api/im', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(payload) });
    if (!r.ok) throw new Error(`send-im failed: ${r.status}`);
    return r.json();
  },
  async email(agent) {
    const q = agent ? `?agent=${encodeURIComponent(agent)}` : '';
    return (await fetch(`/api/email${q}`)).json();
  },
  async sendEmail(payload) {
    const r = await fetch('/api/email', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(payload) });
    if (!r.ok) throw new Error(`send-email failed: ${r.status}`);
    return r.json();
  },
  async timeline() { return (await fetch('/api/timeline')).json(); },
};

// ─── Routing ───────────────────────────────────────────────────────────────
const routes = { im: viewIm, email: viewEmail, agents: viewAgents, settings: viewSettings, timeline: viewTimeline };

function setActiveTab(name) {
  for (const t of $$('.tab')) t.setAttribute('aria-selected', String(t.dataset.route === name));
}

async function navigate(name) {
  setActiveTab(name);
  history.replaceState(null, '', `#${name}`);
  view.replaceChildren();
  view.appendChild(el('p', { class: 'muted' }, 'loading…'));
  try {
    const node = await routes[name]();
    view.replaceChildren(node);
    view.focus();
  } catch (err) {
    view.replaceChildren(el('div', { class: 'card' }, [
      el('h2', {}, 'Error'),
      el('p', {}, String(err.message ?? err)),
    ]));
  }
}

for (const t of $$('.tab')) t.addEventListener('click', () => navigate(t.dataset.route));

// ─── Views ─────────────────────────────────────────────────────────────────
async function viewIm() {
  const root = el('div');
  root.appendChild(el('h2', {}, 'Instant Messages'));

  // Compose
  const fromEl = el('input', { placeholder: 'from (e.g. you)', value: 'you' });
  const toEl   = el('input', { placeholder: 'to (e.g. sol)' });
  const bodyEl = el('textarea', { placeholder: 'message' });
  const sendBtn = el('button', { class: 'primary' }, 'Send IM');

  const compose = el('div', { class: 'card' }, [
    el('div', { class: 'compose' }, [
      el('div', { class: 'row-fields' }, [fromEl, toEl]),
      bodyEl,
      el('div', { class: 'row' }, [sendBtn, el('span', { class: 'muted', id: 'im-send-status' }, '')]),
    ]),
  ]);
  root.appendChild(compose);

  const list = el('div', { class: 'card' });
  root.appendChild(list);

  async function refresh() {
    const items = await api.im();
    list.replaceChildren();
    if (items.length === 0) list.appendChild(el('p', { class: 'muted' }, 'No messages yet.'));
    for (const m of items) {
      list.appendChild(el('div', { class: 'msg' }, [
        el('div', { class: 'msg-meta' }, [
          el('span', { class: 'msg-from' }, `@${m.sender}`),
          text('→'),
          el('span', { class: 'msg-to' }, `@${m.recipient}`),
          el('span', { class: 'msg-time' }, fmtTime(m.created_at)),
        ]),
        el('p', { class: 'msg-body' }, m.body),
      ]));
    }
  }

  sendBtn.addEventListener('click', async () => {
    const from = fromEl.value.trim(), to = toEl.value.trim(), body = bodyEl.value.trim();
    if (!from || !to || !body) { $('#im-send-status').textContent = 'fill all fields'; return; }
    sendBtn.disabled = true;
    try {
      await api.sendIm({ from, to, body });
      bodyEl.value = '';
      $('#im-send-status').textContent = 'sent';
      await refresh();
    } catch (e) {
      $('#im-send-status').textContent = e.message;
    } finally { sendBtn.disabled = false; }
  });

  await refresh();
  // Live updates
  ws.onMessage = (m) => { if (m.type === 'im') refresh(); };
  return root;
}

async function viewEmail() {
  const root = el('div');
  root.appendChild(el('h2', {}, 'Email'));

  const fromEl = el('input', { placeholder: 'from', value: 'you' });
  const toEl   = el('input', { placeholder: 'to' });
  const subjEl = el('input', { placeholder: 'subject' });
  const bodyEl = el('textarea', { placeholder: 'body' });
  const sendBtn = el('button', { class: 'primary' }, 'Send Email');
  const statusEl = el('span', { class: 'muted' }, '');

  root.appendChild(el('div', { class: 'card' }, [
    el('div', { class: 'compose' }, [
      el('div', { class: 'row-fields' }, [fromEl, toEl]),
      subjEl, bodyEl,
      el('div', { class: 'row' }, [sendBtn, statusEl]),
    ]),
  ]));

  const list = el('div', { class: 'card' });
  root.appendChild(list);

  async function refresh() {
    const items = await api.email();
    list.replaceChildren();
    if (items.length === 0) list.appendChild(el('p', { class: 'muted' }, 'Inbox empty.'));
    for (const m of items) {
      const att = (m.attachments ?? []).map((a) =>
        el('span', { class: 'muted' }, ` [${a.kind}:${a.name}]`));
      list.appendChild(el('div', { class: 'msg' }, [
        el('div', { class: 'msg-meta' }, [
          el('span', { class: 'msg-from' }, `@${m.sender}`),
          text('→'),
          el('span', { class: 'msg-to' }, `@${m.recipient}`),
          el('span', { class: 'msg-time' }, fmtTime(m.created_at)),
        ]),
        el('div', { class: 'msg-subject' }, m.subject),
        el('p', { class: 'msg-body' }, m.body),
        el('div', {}, att),
      ]));
    }
  }

  sendBtn.addEventListener('click', async () => {
    const from = fromEl.value.trim(), to = toEl.value.trim(), subject = subjEl.value.trim(), body = bodyEl.value.trim();
    if (!from || !to || !subject || !body) { statusEl.textContent = 'fill all fields'; return; }
    sendBtn.disabled = true;
    try {
      await api.sendEmail({ from, to, subject, body });
      bodyEl.value = ''; subjEl.value = '';
      statusEl.textContent = 'sent';
      await refresh();
    } catch (e) { statusEl.textContent = e.message; }
    finally { sendBtn.disabled = false; }
  });

  await refresh();
  ws.onMessage = (m) => { if (m.type === 'email') refresh(); };
  return root;
}

async function viewAgents() {
  const root = el('div');
  root.appendChild(el('h2', {}, 'Agents'));
  const grid = el('div', { class: 'agents-grid' });
  const agents = await api.agents();
  for (const a of agents) {
    const stats = a.stats ?? {};
    grid.appendChild(el('div', { class: 'card agent-card' }, [
      el('div', { class: 'name' }, [
        el('span', { class: `dot ${a.enabled ? 'on' : 'off'}`, 'aria-hidden': 'true' }),
        text(a.name),
      ]),
      el('div', { class: 'role' }, a.role || '—'),
      el('div', { class: 'stats' }, [
        text(`independence ${stats.independence ?? '?'} · `),
        text(`verbosity ${stats.verbosity ?? '?'} · `),
        text(`inbox/${stats.inbox_check_interval ?? '?'}`),
      ]),
      el('div', { class: 'heartbeat' }, [
        text(a.current_task ? `task: ${a.current_task}` : 'idle'),
        el('br'),
        text(a.last_heartbeat ? `last seen ${fmtTime(a.last_heartbeat)}` : 'no heartbeat yet'),
      ]),
    ]));
  }
  root.appendChild(grid);
  return root;
}

async function viewSettings() {
  const root = el('div');
  root.appendChild(el('h2', {}, 'Settings'));
  const s = await api.settings();
  root.appendChild(el('div', { class: 'card' }, [
    el('p', { class: 'muted' }, 'Read-only in v0.1. Edit SETTINGS.jsonc on disk and restart.'),
    el('pre', { class: 'settings-pre' }, JSON.stringify(s, null, 2)),
  ]));
  return root;
}

async function viewTimeline() {
  const root = el('div');
  root.appendChild(el('h2', {}, 'Timeline'));
  const items = await api.timeline();
  const list = el('div', { class: 'card' });
  if (items.length === 0) list.appendChild(el('p', { class: 'muted' }, 'No activity yet.'));
  for (const m of items) {
    list.appendChild(el('div', { class: 'timeline-row' }, [
      el('span', { class: 'kind' }, m.kind),
      el('span', { class: 'time' }, fmtTime(m.created_at)),
      el('span', {}, [
        el('strong', {}, `@${m.sender}`),
        text(' → '),
        el('strong', {}, `@${m.recipient}`),
        text(m.subject ? ` · ${m.subject}` : ''),
        el('br'),
        text((m.body || '').slice(0, 200)),
      ]),
    ]));
  }
  root.appendChild(list);
  return root;
}

// ─── WebSocket ─────────────────────────────────────────────────────────────
const ws = {
  socket: null,
  onMessage: null,
  connect() {
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    this.socket = new WebSocket(`${proto}//${location.host}/ws`);
    this.socket.addEventListener('open', () => { status.textContent = 'live'; status.classList.add('ok'); status.classList.remove('bad'); });
    this.socket.addEventListener('close', () => {
      status.textContent = 'reconnecting…';
      status.classList.remove('ok'); status.classList.add('bad');
      setTimeout(() => this.connect(), 2000);
    });
    this.socket.addEventListener('error', () => { /* will close + reconnect */ });
    this.socket.addEventListener('message', (ev) => {
      try {
        const m = JSON.parse(ev.data);
        if (typeof this.onMessage === 'function') this.onMessage(m);
      } catch {}
    });
  },
};

// ─── Boot ──────────────────────────────────────────────────────────────────
(async () => {
  try {
    const h = await api.health();
    if (h.ok) {
      status.textContent = `v${h.version}`;
      $('#version').textContent = `v${h.version}`;
    }
  } catch {
    status.textContent = 'offline'; status.classList.add('bad');
  }
  ws.connect();
  const initial = (location.hash || '#im').slice(1);
  navigate(routes[initial] ? initial : 'im');
})();
