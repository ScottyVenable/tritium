// Tritium OpenAI-compatible adapter.
//
// Reads SETTINGS.jsonc for global.dryRun and per-agent stats (independence,
// verbosity, model_preference, temperature). Composes a chat-completion
// request from agents/<name>/prompts/system.md + agents/<name>/agent.md,
// optionally calls the configured endpoint, and routes structured
// [[IM to=...]]...[[/IM]] blocks into the local Tritium runtime.

import fs from 'node:fs';
import path from 'node:path';
import url from 'node:url';
import http from 'node:http';
import https from 'node:https';

const __dirname = path.dirname(url.fileURLToPath(import.meta.url));
const PKG_ROOT = path.resolve(__dirname, '..', '..', '..'); // tritium/

function args() {
  const a = { _: [] };
  const v = process.argv.slice(2);
  for (let i = 0; i < v.length; i++) {
    const x = v[i];
    if (x.startsWith('--')) {
      const k = x.slice(2);
      const n = v[i + 1];
      if (n == null || n.startsWith('--')) a[k] = true;
      else { a[k] = n; i++; }
    } else a._.push(x);
  }
  return a;
}

function readFile(p) { return fs.readFileSync(p, 'utf8'); }
function readMaybe(p) { try { return readFile(p); } catch { return null; } }

function loadSettings() {
  const candidates = [
    path.join(PKG_ROOT, 'SETTINGS.jsonc'),
    path.join(PKG_ROOT, 'SETTINGS.example.jsonc'),
  ];
  for (const p of candidates) {
    if (fs.existsSync(p)) {
      // Reuse the runtime's parser if available; otherwise minimal strip.
      let raw = readFile(p);
      raw = raw
        .replace(/\/\*[\s\S]*?\*\//g, '')
        .replace(/^\s*\/\/.*$/gm, '')
        .replace(/,(\s*[}\]])/g, '$1');
      try { return JSON.parse(raw); } catch { return {}; }
    }
  }
  return {};
}

function postJson(targetUrl, body, headers = {}) {
  return new Promise((resolve, reject) => {
    const u = new URL(targetUrl);
    const lib = u.protocol === 'https:' ? https : http;
    const data = JSON.stringify(body);
    const req = lib.request({
      method: 'POST', hostname: u.hostname, port: u.port || (u.protocol === 'https:' ? 443 : 80),
      path: u.pathname + u.search,
      headers: { 'content-type': 'application/json', 'content-length': Buffer.byteLength(data), ...headers },
    }, (res) => {
      let buf = '';
      res.on('data', (c) => buf += c);
      res.on('end', () => {
        try { resolve({ status: res.statusCode, json: JSON.parse(buf) }); }
        catch { resolve({ status: res.statusCode, raw: buf }); }
      });
    });
    req.on('error', reject);
    req.write(data); req.end();
  });
}

function extractImBlocks(text) {
  // [[IM to=name]] body [[/IM]]
  const re = /\[\[IM to=([\w-]+)\]\]([\s\S]*?)\[\[\/IM\]\]/g;
  const out = [];
  let m;
  while ((m = re.exec(text))) out.push({ to: m[1], body: m[2].trim() });
  return out;
}

async function postIm(port, payload) {
  const target = `http://127.0.0.1:${port}/api/im`;
  try { return await postJson(target, payload); }
  catch (e) { return { error: e.message }; }
}

(async () => {
  const a = args();
  const agent = a.agent;
  const task = a.task ?? a._.join(' ');
  if (!agent || !task) {
    console.error('usage: node src/run.js --agent <name> --task "..."');
    process.exit(1);
  }

  const settings = loadSettings();
  const global = settings.global ?? {};
  const agentStats = settings.agents?.[agent] ?? {};
  const dryRun = global.dryRun !== false;
  const baseUrl = process.env.TRITIUM_BASE_URL ?? 'http://localhost:1234/v1';
  const apiKey  = process.env.TRITIUM_API_KEY  ?? '';
  const model   = process.env.TRITIUM_MODEL    ?? agentStats.model_preference ?? global.default_model ?? 'local-model';

  const sys1 = readMaybe(path.join(PKG_ROOT, 'agents', agent, 'prompts', 'system.md')) ?? '';
  const sys2 = readMaybe(path.join(PKG_ROOT, 'agents', agent, 'agent.md')) ?? '';
  const system = `${sys1}\n\n---\n\n${sys2}`;

  const independence = agentStats.independence ?? 6;
  const verbosity    = agentStats.verbosity ?? 3;
  const temperature  = agentStats.temperature ?? 0.3;

  const userMsg =
    `Task: ${task}\n` +
    `\nOperating context: independence=${independence}, verbosity=${verbosity}. ` +
    `If independence >= 7, prefer a documented decision over asking. ` +
    `To send an IM to another agent, emit:\n` +
    `[[IM to=<name>]]message body[[/IM]]\n` +
    `Sign your final output with "— ${agent[0].toUpperCase()}${agent.slice(1)}".`;

  const request = {
    model,
    messages: [
      { role: 'system', content: system },
      { role: 'user',   content: userMsg },
    ],
    temperature,
  };

  if (dryRun) {
    console.log('# DRY RUN — no API call will be made.');
    console.log(`# endpoint: ${baseUrl}/chat/completions`);
    console.log(`# model:    ${model}`);
    console.log(`# agent:    ${agent}`);
    console.log(`# system bytes: ${system.length}`);
    console.log(`# user:    ${userMsg.slice(0, 200)}…`);
    process.exit(0);
  }

  const r = await postJson(`${baseUrl}/chat/completions`, request,
    apiKey ? { authorization: `Bearer ${apiKey}` } : {});

  const content = r.json?.choices?.[0]?.message?.content ?? '';
  console.log(content);

  // Route any structured IM blocks into the runtime.
  const ims = extractImBlocks(content);
  if (ims.length > 0) {
    const port = global.dashboard_port ?? 7330;
    for (const im of ims) {
      const out = await postIm(port, { from: agent, to: im.to, body: im.body });
      console.error(`[tritium] forwarded IM to @${im.to}: status=${out.status ?? 'err'}`);
    }
  }
})().catch((e) => { console.error(e); process.exit(1); });
