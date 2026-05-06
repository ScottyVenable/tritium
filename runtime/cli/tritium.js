#!/usr/bin/env node
// `tritium-os` CLI — Tritium OS
//
// Commands:
//   serve / start                                 — start the runtime server
//   stop                                          — stop the running server
//   restart                                       — restart the server
//   status                                        — show server status (JSON)
//   open                                          — open the dashboard in a browser
//   agents                                        — list agents and stats
//   inbox check [--agent <name>] [--all]          — list unread IMs and recent emails
//   send-im --from <a> --to <b> --body "..."      — post an IM
//   send-email --from <a> --to <b> --subject "…" --body "…" [--attach <path>]
//   run-agent <name> --task "..."                 — adapter-side dispatch (stub)
//   doctor                                        — check system requirements
//   update / --update                             — pull latest from GitHub and reinstall
//   version / --version / -v                      — print version
//   help / --help / -h                            — show this help

import path from 'node:path';
import fs from 'node:fs';
import url from 'node:url';
import http from 'node:http';
import https from 'node:https';
import { spawn, spawnSync, execSync } from 'node:child_process';
import os from 'node:os';

const __dirname = path.dirname(url.fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..', '..');

// ─── ANSI colors ─────────────────────────────────────────────────────────────

const USE_COLOR = process.stdout.isTTY && !process.env.NO_COLOR && process.env.TERM !== 'dumb';
const C = USE_COLOR ? {
  reset: '\x1b[0m', bold: '\x1b[1m', dim: '\x1b[2m', italic: '\x1b[3m',
  red: '\x1b[31m', green: '\x1b[32m', yellow: '\x1b[33m',
  blue: '\x1b[34m', magenta: '\x1b[35m', cyan: '\x1b[36m', white: '\x1b[37m',
} : Object.fromEntries(
  ['reset','bold','dim','italic','red','green','yellow','blue','magenta','cyan','white']
    .map(k => [k, ''])
);

const ok  = (s) => `${C.green}${C.bold}✔${C.reset} ${s}`;
const err = (s) => `${C.red}${C.bold}✖${C.reset} ${s}`;
const info = (s) => `${C.cyan}${C.bold}›${C.reset} ${s}`;
const warn = (s) => `${C.yellow}${C.bold}!${C.reset} ${s}`;
const dim  = (s) => `${C.dim}${s}${C.reset}`;
const bold = (s) => `${C.bold}${s}${C.reset}`;

// ─── Version ─────────────────────────────────────────────────────────────────

function getVersion() {
  try {
    const pkg = JSON.parse(fs.readFileSync(path.join(ROOT, 'runtime', 'server', 'package.json'), 'utf8'));
    return pkg.version ?? '0.1.0';
  } catch { return '0.1.0'; }
}

const VERSION = getVersion();

// ─── Banner ──────────────────────────────────────────────────────────────────

function banner() {
  const logo = [
    `${C.cyan}${C.bold}  _____     _ _   _                 ___  ____${C.reset}`,
    `${C.cyan}${C.bold} |_   _| __(_) |_(_)_   _ _ __ ___ / _ \\/ ___|${C.reset}`,
    `${C.cyan}${C.bold}   | || '__| | __| | | | | '_ \` _ \\ | | \\___ \\${C.reset}`,
    `${C.cyan}${C.bold}   | || |  | | |_| | |_| | | | | | | |_| |___) |${C.reset}`,
    `${C.cyan}${C.bold}   |_||_|  |_|\\__|_|\\__,_|_| |_| |_|\\___/|____/${C.reset}`,
    `  ${C.dim}v${VERSION} — local-first multi-agent coordination layer${C.reset}`,
    '',
  ];
  console.log(logo.join('\n'));
}

// ─── Settings / port ─────────────────────────────────────────────────────────

function loadSettingsForPort() {
  const p = fs.existsSync(path.join(ROOT, 'SETTINGS.jsonc'))
    ? path.join(ROOT, 'SETTINGS.jsonc')
    : path.join(ROOT, 'SETTINGS.example.jsonc');
  try {
    const raw = fs.readFileSync(p, 'utf8');
    const m = raw.match(/dashboard_port"\s*:\s*(\d+)/);
    return m ? Number(m[1]) : 7330;
  } catch { return 7330; }
}

const PORT = loadSettingsForPort();

// ─── Argument parser ─────────────────────────────────────────────────────────

function parseArgs(argv) {
  const args = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith('--')) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (next == null || next.startsWith('--')) { args[key] = true; }
      else { args[key] = next; i++; }
    } else {
      args._.push(a);
    }
  }
  return args;
}

// ─── HTTP helpers ─────────────────────────────────────────────────────────────

function apiFetch(method, path_, body) {
  const data = body ? JSON.stringify(body) : null;
  return new Promise((resolve, reject) => {
    const req = http.request({
      hostname: '127.0.0.1', port: PORT, path: path_, method,
      headers: data ? { 'content-type': 'application/json', 'content-length': Buffer.byteLength(data) } : {},
    }, (res) => {
      let buf = '';
      res.on('data', (c) => buf += c);
      res.on('end', () => {
        try { resolve({ status: res.statusCode, json: buf ? JSON.parse(buf) : null }); }
        catch { resolve({ status: res.statusCode, raw: buf }); }
      });
    });
    req.on('error', reject);
    if (data) req.write(data);
    req.end();
  });
}

function httpsGet(url_) {
  return new Promise((resolve, reject) => {
    const req = https.get(url_, { headers: { 'user-agent': `tritium-os/${VERSION}` } }, (res) => {
      let buf = '';
      res.on('data', (c) => buf += c);
      res.on('end', () => {
        try { resolve({ status: res.statusCode, json: JSON.parse(buf) }); }
        catch { resolve({ status: res.statusCode, raw: buf }); }
      });
    });
    req.on('error', reject);
    req.end();
  });
}

async function ensureRunning() {
  try {
    const r = await apiFetch('GET', '/api/health');
    if (r.status === 200) return true;
  } catch {}
  console.error(err(`tritium runtime not reachable at http://localhost:${PORT}`));
  console.error(dim('  start it with: tritium-os serve'));
  process.exit(2);
}

// ─── Update check ────────────────────────────────────────────────────────────

const TRITIUM_HOME = process.env.TRITIUM_HOME ?? path.join(os.homedir(), '.tritium-os');
const UPDATE_CHECK_FILE = path.join(TRITIUM_HOME, 'state', '.update-check');
const REPO_API = 'https://api.github.com/repos/ScottyVenable/tritium-os/commits/main';
const ONE_DAY_MS = 86_400_000;

async function checkForUpdate(silent = false) {
  try {
    // Rate-limit to once per day.
    if (fs.existsSync(UPDATE_CHECK_FILE)) {
      const lastCheck = Number(fs.readFileSync(UPDATE_CHECK_FILE, 'utf8').trim());
      if (!Number.isNaN(lastCheck) && Date.now() - lastCheck < ONE_DAY_MS) return;
    }

    // Get current HEAD SHA (best-effort).
    let localSha = '';
    try { localSha = execSync('git rev-parse HEAD', { cwd: ROOT, stdio: ['ignore','pipe','ignore'] }).toString().trim(); } catch {}

    const r = await httpsGet(REPO_API);
    if (r.status !== 200 || !r.json?.sha) return;

    // Record the check time.
    fs.mkdirSync(path.dirname(UPDATE_CHECK_FILE), { recursive: true });
    fs.writeFileSync(UPDATE_CHECK_FILE, String(Date.now()));

    if (localSha && r.json.sha !== localSha) {
      if (!silent) {
        console.log(warn(`Update available!  Run ${bold('tritium-os update')} to upgrade.`));
        console.log(dim(`  local  : ${localSha.slice(0, 10)}`));
        console.log(dim(`  remote : ${r.json.sha.slice(0, 10)}  (${r.json.commit?.author?.date?.slice(0,10) ?? ''})`));
        console.log();
      }
    }
  } catch { /* network unavailable — silently ignore */ }
}

// ─── Help ────────────────────────────────────────────────────────────────────

function help() {
  banner();
  const cmd = (c, d) => `  ${C.cyan}${C.bold}${c.padEnd(42)}${C.reset}${C.dim}${d}${C.reset}`;
  console.log(`${bold('USAGE')}`);
  console.log(`  tritium-os <command> [options]\n`);
  console.log(`${bold('SERVER')}`);
  console.log(cmd('serve, start',              'Start the runtime server'));
  console.log(cmd('stop',                      'Stop the running server'));
  console.log(cmd('restart',                   'Restart the server'));
  console.log(cmd('status',                    'Show server health (JSON)'));
  console.log(cmd('open',                      'Open the dashboard in a browser'));
  console.log();
  console.log(`${bold('AGENTS')}`);
  console.log(cmd('agents',                    'List agents and stats'));
  console.log(cmd('run-agent <name> --task "…"','Dispatch task to agent (stub)'));
  console.log();
  console.log(`${bold('MESSAGING')}`);
  console.log(cmd('inbox check [--agent <n>] [--all]', 'List unread IMs and email'));
  console.log(cmd('send-im --from <a> --to <b> --body "…"', 'Send an instant message'));
  console.log(cmd('send-email --from <a> --to <b>', 'Send an email'));
  console.log(cmd('  --subject "…" --body "…" [--attach <path>]', ''));
  console.log();
  console.log(`${bold('SYSTEM')}`);
  console.log(cmd('doctor',                    'Check system requirements'));
  console.log(cmd('update, --update',          'Pull latest from GitHub and reinstall'));
  console.log(cmd('version, --version, -v',    'Show version'));
  console.log(cmd('help, --help, -h',          'Show this help'));
  console.log();
  console.log(dim(`  The runtime must be running for inbox/send commands.`));
  console.log(dim(`  Start it with: tritium-os serve`));
  console.log();
}

// ─── Doctor ──────────────────────────────────────────────────────────────────

async function doctor() {
  banner();
  console.log(`${bold('SYSTEM CHECK')}\n`);

  const check = (label, fn) => {
    try {
      const result = fn();
      console.log(ok(`${label.padEnd(20)} ${C.dim}${result}${C.reset}`));
    } catch (e) {
      console.log(err(`${label.padEnd(20)} ${C.red}${e.message}${C.reset}`));
    }
  };

  const run = (cmd) => execSync(cmd, { stdio: ['ignore','pipe','ignore'] }).toString().trim();

  check('Node.js', () => {
    const v = run('node --version');
    const major = Number(v.replace(/^v/, '').split('.')[0]);
    if (major < 20) throw new Error(`${v} (need ≥ 20)`);
    return v;
  });
  check('npm', () => run('npm --version'));
  check('git', () => run('git --version'));
  check('Python 3', () => {
    for (const bin of ['python3', 'python']) {
      try {
        const v = execSync(`${bin} --version 2>&1`, { stdio: ['ignore','pipe','ignore'] }).toString().trim();
        return v;
      } catch {}
    }
    throw new Error('not found');
  });

  console.log();
  console.log(`${bold('RUNTIME')}\n`);

  // Runtime reachable?
  let runtimeUp = false;
  try {
    const r = await apiFetch('GET', '/api/health');
    runtimeUp = r.status === 200;
  } catch {}

  if (runtimeUp) {
    console.log(ok(`Runtime            http://localhost:${PORT}`));
    const r = await apiFetch('GET', '/api/health');
    console.log(dim(`  version: ${r.json?.version ?? '?'}`));
  } else {
    console.log(warn(`Runtime            not running  (start with: tritium-os serve)`));
  }

  // DB path
  const settingsPath = fs.existsSync(path.join(ROOT, 'SETTINGS.jsonc'))
    ? path.join(ROOT, 'SETTINGS.jsonc') : path.join(ROOT, 'SETTINGS.example.jsonc');
  const rawSettings = fs.existsSync(settingsPath) ? fs.readFileSync(settingsPath, 'utf8') : '';
  const dbPathMatch = rawSettings.match(/"db_path"\s*:\s*"([^"]+)"/);
  const dbPath = dbPathMatch ? path.resolve(ROOT, dbPathMatch[1]) : path.join(ROOT, '.tritium', 'tritium.db');
  if (fs.existsSync(dbPath)) {
    const stat = fs.statSync(dbPath);
    console.log(ok(`Database           ${dbPath}  ${C.dim}(${(stat.size / 1024).toFixed(1)} KB)${C.reset}`));
  } else {
    console.log(warn(`Database           not initialized  (will be created on first start)`));
  }

  // node_modules
  const nmPath = path.join(ROOT, 'runtime', 'server', 'node_modules');
  if (fs.existsSync(nmPath)) {
    console.log(ok('node_modules       runtime/server/node_modules exists'));
  } else {
    console.log(err('node_modules       missing — run: npm install inside runtime/server/'));
  }

  // Mailboxes
  const mbRoot = path.join(ROOT, 'world', 'social', 'mailbox');
  if (fs.existsSync(mbRoot)) {
    const boxes = fs.readdirSync(mbRoot, { withFileTypes: true }).filter(d => d.isDirectory()).length;
    console.log(ok(`Mailboxes          ${boxes} agent mailbox${boxes !== 1 ? 'es' : ''} found`));
  } else {
    console.log(warn('Mailboxes          world/social/mailbox/ not found'));
  }

  // Platform
  console.log();
  console.log(`${bold('PLATFORM')}\n`);
  const plat = os.platform();
  const isTermux = !!process.env.PREFIX?.includes('com.termux');
  console.log(info(`OS: ${os.type()} ${os.release()} (${plat})${isTermux ? ' [Termux]' : ''}`));
  console.log(info(`Arch: ${os.arch()}`));
  console.log(info(`Home: ${os.homedir()}`));
  console.log(info(`Tritium home: ${TRITIUM_HOME}`));
  console.log(info(`Repo root: ${ROOT}`));
  console.log();
}

// ─── Update ──────────────────────────────────────────────────────────────────

async function update() {
  console.log(`${bold('TRITIUM OS UPDATE')}\n`);

  // 1. git pull
  console.log(info('Pulling latest from GitHub…'));
  const pull = spawnSync('git', ['pull', 'origin', 'main'], { cwd: ROOT, stdio: 'inherit' });
  if (pull.status !== 0) {
    console.error(err('git pull failed. Resolve any conflicts and try again.'));
    process.exit(1);
  }

  // 2. npm install
  console.log();
  console.log(info('Reinstalling Node dependencies…'));
  const serverDir = path.join(ROOT, 'runtime', 'server');

  // Determine npm binary
  const npmBin = process.platform === 'win32' ? 'npm.cmd' : 'npm';

  // Try regular install first, then --build-from-source on failure.
  let ni = spawnSync(npmBin, ['install'], { cwd: serverDir, stdio: 'inherit', shell: false });
  if (ni.status !== 0) {
    console.log(warn('Normal install failed. Retrying with --build-from-source…'));
    ni = spawnSync(npmBin, ['install', '--build-from-source'], { cwd: serverDir, stdio: 'inherit', shell: false });
    if (ni.status !== 0) {
      console.error(err('npm install failed. See output above for details.'));
      process.exit(1);
    }
  }

  console.log();
  console.log(ok('Update complete!'));
  const newVer = getVersion();
  console.log(dim(`  now on: v${newVer}`));
  console.log(dim('  restart the server with: tritium-os restart'));
  console.log();
}

// ─── Open dashboard ──────────────────────────────────────────────────────────

async function openDashboard() {
  const dashUrl = `http://localhost:${PORT}`;
  const isTermux = !!process.env.PREFIX?.includes('com.termux');
  let opened = false;

  if (isTermux) {
    try {
      spawnSync('termux-open-url', [dashUrl], { stdio: 'ignore' });
      opened = true;
    } catch {}
  } else if (process.platform === 'darwin') {
    spawnSync('open', [dashUrl], { stdio: 'ignore' });
    opened = true;
  } else if (process.platform === 'win32') {
    spawnSync('start', [dashUrl], { stdio: 'ignore', shell: true });
    opened = true;
  } else {
    // Linux / WSL / other
    for (const browser of ['xdg-open', 'sensible-browser', 'x-www-browser', 'www-browser']) {
      try {
        execSync(`which ${browser}`, { stdio: 'ignore' });
        spawnSync(browser, [dashUrl], { stdio: 'ignore', detached: true });
        opened = true;
        break;
      } catch {}
    }
  }

  if (opened) {
    console.log(ok(`Opening ${C.cyan}${dashUrl}${C.reset}`));
  } else {
    console.log(info(`Dashboard URL: ${C.cyan}${C.bold}${dashUrl}${C.reset}`));
    console.log(dim('  (could not detect browser — open the URL above manually)'));
  }
}

// ─── Stop server ─────────────────────────────────────────────────────────────

async function stopServer() {
  // Look for a PID file written by the server, or use the API to request shutdown.
  const pidFile = path.join(ROOT, '.tritium', 'server.pid');
  if (fs.existsSync(pidFile)) {
    const pid = Number(fs.readFileSync(pidFile, 'utf8').trim());
    if (!Number.isNaN(pid) && pid > 0) {
      try {
        process.kill(pid, 'SIGTERM');
        console.log(ok(`Sent SIGTERM to server (PID ${pid})`));
        fs.unlinkSync(pidFile);
        return;
      } catch (e) {
        if (e.code === 'ESRCH') {
          console.log(warn('Server process not found (already stopped?)'));
          fs.unlinkSync(pidFile);
          return;
        }
        throw e;
      }
    }
  }

  // Fallback: probe via HTTP; the server handles SIGTERM on graceful shutdown
  // but there is no shutdown endpoint — tell the user.
  let runtimeUp = false;
  try {
    const r = await apiFetch('GET', '/api/health');
    runtimeUp = r.status === 200;
  } catch {}

  if (!runtimeUp) {
    console.log(warn('Runtime is not running.'));
  } else {
    console.log(warn(`No PID file found at ${pidFile}`));
    console.log(dim('  To stop: find the process with `ps aux | grep tritium` and kill it.'));
    console.log(dim('  Or start the server with `tritium-os serve` (it manages its own PID).'));
  }
}

// ─── Main ────────────────────────────────────────────────────────────────────

const rawCmd = process.argv[2];
const args = parseArgs(process.argv.slice(3));

// Normalize --update, --version etc. to their bare command name
const cmd = (() => {
  if (rawCmd === '--update')  return 'update';
  if (rawCmd === '--version' || rawCmd === '-v') return 'version';
  if (rawCmd === '--help'    || rawCmd === '-h') return 'help';
  return rawCmd;
})();

// Trigger a background update check for interactive commands (non-blocking).
const updateCheckCommands = new Set(['serve','start','agents','status','inbox','open','doctor','help',undefined]);
if (updateCheckCommands.has(cmd)) {
  checkForUpdate(false).catch(() => {});
}

(async () => {
  switch (cmd) {
    // ── Server ─────────────────────────────────────────────────────────────
    case 'serve':
    case 'start': {
      banner();
      console.log(info(`Starting Tritium OS runtime on http://localhost:${PORT}…`));
      console.log(dim('  Press Ctrl+C to stop.\n'));

      const serverDir = path.join(ROOT, 'runtime', 'server');
      const pidFile   = path.join(ROOT, '.tritium', 'server.pid');

      const child = spawn(process.execPath, [path.join(serverDir, 'src', 'index.js')], {
        stdio: 'inherit',
        cwd: serverDir,
      });

      // Write PID file so `tritium-os stop` can find the process.
      fs.mkdirSync(path.dirname(pidFile), { recursive: true });
      fs.writeFileSync(pidFile, String(child.pid));

      child.on('exit', (code) => {
        try { if (fs.existsSync(pidFile)) fs.unlinkSync(pidFile); } catch {}
        process.exit(code ?? 0);
      });
      break;
    }

    case 'stop': {
      await stopServer();
      break;
    }

    case 'restart': {
      await stopServer();
      // Small pause then re-serve in a detached child so this process exits cleanly.
      await new Promise(r => setTimeout(r, 500));
      const child = spawn(process.execPath, [process.argv[1], 'serve'], {
        stdio: 'inherit', detached: false,
      });
      child.on('exit', (code) => process.exit(code ?? 0));
      break;
    }

    case 'open': {
      await openDashboard();
      break;
    }

    // ── Inbox ─────────────────────────────────────────────────────────────
    case 'inbox': {
      const sub = args._[0];
      if (sub !== 'check') { help(); process.exit(1); }
      const agent = args.agent;
      if (!agent && !args.all) {
        console.error(err('--agent <name> required (or pass --all)'));
        process.exit(1);
      }

      let apiUp = false;
      try {
        const h = await apiFetch('GET', '/api/health');
        apiUp = (h.status === 200);
      } catch { apiUp = false; }

      if (!apiUp) {
        const targets = agent ? [agent] : (() => {
          const mbRoot = path.join(ROOT, 'world', 'social', 'mailbox');
          if (!fs.existsSync(mbRoot)) return [];
          return fs.readdirSync(mbRoot, { withFileTypes: true })
            .filter(d => d.isDirectory() && !d.name.startsWith('['))
            .map(d => d.name);
        })();
        console.log(`${C.yellow}# IM${C.reset} ${C.dim}(API unavailable — showing file mailbox)${C.reset}`);
        for (const a of targets) {
          const dir = path.join(ROOT, 'world', 'social', 'mailbox', a);
          if (!fs.existsSync(dir)) continue;
          const entries = fs.readdirSync(dir, { withFileTypes: true })
            .filter(d => d.isFile() && d.name !== '.gitkeep')
            .map(d => {
              const full = path.join(dir, d.name);
              return { name: d.name, mtime: fs.statSync(full).mtimeMs };
            })
            .sort((a, b) => b.mtime - a.mtime);
          for (const e of entries) {
            console.log(`  ${C.cyan}world/social/mailbox/${a}/${e.name}${C.reset}`);
          }
        }
        break;
      }

      const q = agent ? `?agent=${encodeURIComponent(agent)}&unreadOnly=1` : '';
      const r = await apiFetch('GET', `/api/im${q}`);
      console.log(`${C.bold}# IM${C.reset} ${C.dim}(${r.json.length})${C.reset}`);
      for (const m of r.json) {
        console.log(`  ${C.dim}[${m.id}]${C.reset} ${C.dim}${m.created_at}${C.reset}  ${C.cyan}@${m.sender}${C.reset} → ${C.cyan}@${m.recipient}${C.reset}: ${m.body}`);
      }
      const eq = agent ? `?agent=${encodeURIComponent(agent)}` : '';
      const e = await apiFetch('GET', `/api/email${eq}`);
      console.log(`${C.bold}# Email${C.reset} ${C.dim}(${e.json.length})${C.reset}`);
      for (const m of e.json) {
        console.log(`  ${C.dim}[${m.id}]${C.reset} ${C.dim}${m.created_at}${C.reset}  ${C.cyan}@${m.sender}${C.reset} → ${C.cyan}@${m.recipient}${C.reset}: ${C.bold}${m.subject}${C.reset}`);
      }
      break;
    }

    // ── Messaging ─────────────────────────────────────────────────────────
    case 'send-im': {
      await ensureRunning();
      const payload = { from: args.from, to: args.to, body: args.body, subject: args.subject };
      const r = await apiFetch('POST', '/api/im', payload);
      if (r.status >= 400) { console.error(err(JSON.stringify(r.json ?? r.raw))); process.exit(1); }
      console.log(ok(`IM sent  ${C.dim}id=${r.json.id}${C.reset}`));
      break;
    }

    case 'send-email': {
      await ensureRunning();
      const attachments = [];
      if (args.attach) {
        const p = path.resolve(args.attach);
        if (!fs.existsSync(p)) { console.error(err(`attachment not found: ${p}`)); process.exit(1); }
        attachments.push({ kind: 'path', name: path.basename(p), ref: p });
      }
      const r = await apiFetch('POST', '/api/email', {
        from: args.from, to: args.to, subject: args.subject, body: args.body, attachments,
      });
      if (r.status >= 400) { console.error(err(JSON.stringify(r.json ?? r.raw))); process.exit(1); }
      console.log(ok(`Email sent  ${C.dim}id=${r.json.id}${C.reset}`));
      break;
    }

    // ── Agents ────────────────────────────────────────────────────────────
    case 'run-agent': {
      const name = args._[0];
      if (!name) { console.error(err('agent name required')); process.exit(1); }
      console.log(info(`run-agent ${C.bold}${name}${C.reset} ${C.dim}(stub — wire your adapter in adapters/<provider>/)${C.reset}`));
      console.log(dim(`  task    : ${args.task ?? '(none)'}`));
      console.log(dim(`  dryRun  : ${!!args.dry}`));
      break;
    }

    case 'agents': {
      await ensureRunning();
      const r = await apiFetch('GET', '/api/agents');
      console.log(`${bold('AGENTS')}\n`);
      for (const a of r.json) {
        const stats = a.stats ?? {};
        const bullet = a.enabled ? `${C.green}●${C.reset}` : `${C.dim}○${C.reset}`;
        console.log(
          `  ${bullet} ${C.bold}${a.name.padEnd(10)}${C.reset}` +
          `${C.dim}${(a.role ?? '').padEnd(32)}${C.reset}` +
          `${C.dim}ind=${stats.independence ?? '?'}  verb=${stats.verbosity ?? '?'}  inbox/${stats.inbox_check_interval ?? '?'}${C.reset}`
        );
      }
      console.log();
      break;
    }

    case 'status': {
      await ensureRunning();
      const r = await apiFetch('GET', '/api/health');
      console.log(JSON.stringify(r.json, null, 2));
      break;
    }

    // ── System ────────────────────────────────────────────────────────────
    case 'doctor': {
      await doctor();
      break;
    }

    case 'update': {
      await update();
      break;
    }

    case 'version': {
      console.log(`tritium-os v${VERSION}`);
      break;
    }

    case undefined:
    case 'help': {
      help();
      break;
    }

    default:
      console.error(err(`unknown command: ${C.bold}${cmd}${C.reset}`));
      console.error(dim('  run: tritium-os help'));
      process.exit(1);
  }
})().catch((e) => { console.error(err(String(e?.message ?? e))); process.exit(1); });
