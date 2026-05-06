// REST helpers — pure functions over the db handle.

import { seedAgents } from './db.js';

const MAX_BODY = 32_000;          // hard cap on IM body length
const MAX_EMAIL_BODY = 200_000;   // hard cap on email body length
const MAX_SUBJECT = 300;

function nowIso() { return new Date().toISOString().replace('T', ' ').replace('Z', '').slice(0, 19); }

function clip(s, max) {
  if (typeof s !== 'string') return '';
  if (s.length > max) return s.slice(0, max);
  return s;
}

function requireString(name, value) {
  if (typeof value !== 'string' || !value.trim()) {
    const err = new Error(`${name} is required`);
    err.statusCode = 400;
    throw err;
  }
  return value.trim();
}

export function createApi({ db, settings }) {
  // Seed agent rows from settings on boot.
  const rows = Object.entries(settings.agents).map(([name, s]) => ({
    name,
    role: s.role ?? null,
    enabled: s.enabled ? 1 : 0,
  }));
  seedAgents(db, rows);

  const stmts = {
    listAgents: db.prepare(`SELECT name, role, enabled, current_task, last_heartbeat FROM agents ORDER BY name`),

    insertIm: db.prepare(`INSERT INTO im_messages (thread_id, sender, recipient, body) VALUES (?, ?, ?, ?)`),
    getImById: db.prepare(`SELECT * FROM im_messages WHERE id = ?`),
    listImAll: db.prepare(`SELECT * FROM im_messages ORDER BY id DESC LIMIT 200`),
    listImByAgent: db.prepare(`
      SELECT * FROM im_messages
      WHERE recipient = ? OR sender = ?
      ORDER BY id DESC LIMIT 200
    `),
    listImUnread: db.prepare(`
      SELECT m.* FROM im_messages m
      WHERE m.recipient = ?
        AND NOT EXISTS (
          SELECT 1 FROM read_receipts r
          WHERE r.kind = 'im' AND r.message_id = m.id AND r.reader = ?
        )
      ORDER BY m.id DESC LIMIT 200
    `),

    insertEmail: db.prepare(`INSERT INTO email (sender, recipient, subject, body) VALUES (?, ?, ?, ?)`),
    insertAttachment: db.prepare(`INSERT INTO email_attachments (email_id, kind, name, ref) VALUES (?, ?, ?, ?)`),
    getEmailById: db.prepare(`SELECT * FROM email WHERE id = ?`),
    listAttachments: db.prepare(`SELECT id, kind, name, ref FROM email_attachments WHERE email_id = ?`),
    listEmailAll: db.prepare(`SELECT * FROM email ORDER BY id DESC LIMIT 200`),
    listEmailByAgent: db.prepare(`
      SELECT * FROM email
      WHERE recipient = ? OR sender = ?
      ORDER BY id DESC LIMIT 200
    `),

    markReadIm: db.prepare(`
      INSERT OR IGNORE INTO read_receipts (kind, message_id, reader) VALUES ('im', ?, ?)
    `),

    insertThread: db.prepare(`INSERT INTO threads (subject) VALUES (?)`),

    heartbeat: db.prepare(`
      UPDATE agents SET current_task = ?, last_heartbeat = datetime('now') WHERE name = ?
    `),

    timeline: db.prepare(`
      SELECT 'im' AS kind, id, sender, recipient, NULL AS subject, body, created_at FROM im_messages
      UNION ALL
      SELECT 'email' AS kind, id, sender, recipient, subject, body, created_at FROM email
      ORDER BY created_at DESC LIMIT 100
    `),
  };

  function listAgents() {
    return stmts.listAgents.all().map((r) => ({
      ...r,
      enabled: !!r.enabled,
      stats: settings.agents[r.name] ?? null,
    }));
  }

  function sendIm(payload) {
    const from = requireString('from', payload?.from);
    const to = requireString('to', payload?.to);
    const body = clip(requireString('body', payload?.body), MAX_BODY);
    let threadId = payload?.threadId ?? null;
    if (threadId != null) threadId = Number(threadId);
    if (threadId === null && payload?.subject) {
      threadId = Number(stmts.insertThread.run(clip(payload.subject, MAX_SUBJECT)).lastInsertRowid);
    }
    const info = stmts.insertIm.run(threadId, from, to, body);
    return stmts.getImById.get(Number(info.lastInsertRowid));
  }

  function listIm({ agent, unreadOnly } = {}) {
    if (unreadOnly && agent) {
      return stmts.listImUnread.all(agent, agent);
    }
    if (agent) {
      return stmts.listImByAgent.all(agent, agent);
    }
    return stmts.listImAll.all();
  }

  function markImRead(id, reader) {
    stmts.markReadIm.run(Number(id), requireString('reader', reader));
  }

  function sendEmail(payload) {
    const from = requireString('from', payload?.from);
    const to = requireString('to', payload?.to);
    const subject = clip(requireString('subject', payload?.subject), MAX_SUBJECT);
    const body = clip(requireString('body', payload?.body), MAX_EMAIL_BODY);

    const txn = db.transaction(() => {
      const info = stmts.insertEmail.run(from, to, subject, body);
      const emailId = Number(info.lastInsertRowid);
      const attachments = Array.isArray(payload?.attachments) ? payload.attachments : [];
      for (const a of attachments) {
        if (!a || !a.kind || !a.name || !a.ref) continue;
        if (a.kind !== 'path' && a.kind !== 'inline') continue;
        stmts.insertAttachment.run(emailId, a.kind, clip(a.name, 200), clip(String(a.ref), 100_000));
      }
      return emailId;
    });
    const id = txn();
    const row = stmts.getEmailById.get(id);
    row.attachments = stmts.listAttachments.all(id);
    return row;
  }

  function listEmail({ agent } = {}) {
    const rows = agent ? stmts.listEmailByAgent.all(agent, agent) : stmts.listEmailAll.all();
    return rows.map((r) => ({ ...r, attachments: stmts.listAttachments.all(r.id) }));
  }

  function heartbeat(payload) {
    const agent = requireString('agent', payload?.agent);
    const task = clip(payload?.currentTask ?? '', 500);
    stmts.heartbeat.run(task, agent);
  }

  function timeline() {
    return stmts.timeline.all();
  }

  return { listAgents, sendIm, listIm, markImRead, sendEmail, listEmail, heartbeat, timeline };
}
