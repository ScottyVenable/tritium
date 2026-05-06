// SQLite database layer for Tritium.
//
// Tables:
//   agents          — registered agents and their last-known status.
//   im_messages     — short, threaded IM messages.
//   email           — longer structured messages.
//   email_attachments — file refs / inline blobs for emails.
//   threads         — IM thread metadata.
//   read_receipts   — per-(agent, message) read records.
//   settings        — key/value cache (mirrors SETTINGS.jsonc reads).
//
// Design choices:
//   - WAL mode for concurrent reads + writes.
//   - Foreign keys enforced.
//   - Timestamps as ISO-8601 strings (sqlite-friendly, human-readable).

import fs from 'node:fs';
import path from 'node:path';
import Database from 'better-sqlite3';

export function openDatabase(dbPath) {
  fs.mkdirSync(path.dirname(dbPath), { recursive: true });
  const db = new Database(dbPath);
  db.pragma('journal_mode = WAL');
  db.pragma('foreign_keys = ON');
  migrate(db);
  return db;
}

function migrate(db) {
  db.exec(`
    CREATE TABLE IF NOT EXISTS agents (
      name             TEXT PRIMARY KEY,
      role             TEXT,
      enabled          INTEGER NOT NULL DEFAULT 1,
      current_task     TEXT,
      last_heartbeat   TEXT
    );

    CREATE TABLE IF NOT EXISTS threads (
      id               INTEGER PRIMARY KEY AUTOINCREMENT,
      subject          TEXT,
      created_at       TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS im_messages (
      id               INTEGER PRIMARY KEY AUTOINCREMENT,
      thread_id        INTEGER REFERENCES threads(id) ON DELETE SET NULL,
      sender           TEXT NOT NULL,
      recipient        TEXT NOT NULL,
      body             TEXT NOT NULL,
      created_at       TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE INDEX IF NOT EXISTS idx_im_recipient ON im_messages(recipient);
    CREATE INDEX IF NOT EXISTS idx_im_thread    ON im_messages(thread_id);
    CREATE INDEX IF NOT EXISTS idx_im_created   ON im_messages(created_at);

    CREATE TABLE IF NOT EXISTS email (
      id               INTEGER PRIMARY KEY AUTOINCREMENT,
      sender           TEXT NOT NULL,
      recipient        TEXT NOT NULL,
      subject          TEXT NOT NULL,
      body             TEXT NOT NULL,
      created_at       TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE INDEX IF NOT EXISTS idx_email_recipient ON email(recipient);
    CREATE INDEX IF NOT EXISTS idx_email_created   ON email(created_at);

    CREATE TABLE IF NOT EXISTS email_attachments (
      id               INTEGER PRIMARY KEY AUTOINCREMENT,
      email_id         INTEGER NOT NULL REFERENCES email(id) ON DELETE CASCADE,
      kind             TEXT NOT NULL CHECK (kind IN ('path', 'inline')),
      name             TEXT NOT NULL,
      ref              TEXT NOT NULL    -- file path or inline blob (utf-8)
    );

    CREATE TABLE IF NOT EXISTS read_receipts (
      kind             TEXT NOT NULL CHECK (kind IN ('im', 'email')),
      message_id       INTEGER NOT NULL,
      reader           TEXT NOT NULL,
      read_at          TEXT NOT NULL DEFAULT (datetime('now')),
      PRIMARY KEY (kind, message_id, reader)
    );

    CREATE TABLE IF NOT EXISTS settings_cache (
      key              TEXT PRIMARY KEY,
      value            TEXT NOT NULL,
      updated_at       TEXT NOT NULL DEFAULT (datetime('now'))
    );
  `);
}

export function seedAgents(db, agents) {
  const stmt = db.prepare(
    `INSERT INTO agents (name, role, enabled) VALUES (@name, @role, @enabled)
     ON CONFLICT(name) DO UPDATE SET role = excluded.role, enabled = excluded.enabled`
  );
  const tx = db.transaction((rows) => { for (const r of rows) stmt.run(r); });
  tx(agents);
}
