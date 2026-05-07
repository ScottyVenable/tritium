import fs from 'node:fs';
import path from 'node:path';
import url from 'node:url';
import { createRequire } from 'node:module';

const __dirname = path.dirname(url.fileURLToPath(import.meta.url));
const SERVER_ROOT = path.resolve(__dirname, '..');
const REPO_ROOT = path.resolve(SERVER_ROOT, '..', '..');
const requireFromServer = createRequire(path.join(SERVER_ROOT, 'package.json'));
const REQUIRED_PACKAGES = ['ws', 'better-sqlite3'];

function isSharedStorage(repoRoot) {
  const normalized = repoRoot.replace(/\\/g, '/');
  return normalized.startsWith('/storage/')
    || normalized.startsWith('/sdcard/')
    || normalized.startsWith('/mnt/sdcard/');
}

function findMissingPackages() {
  const missing = [];
  for (const name of REQUIRED_PACKAGES) {
    try {
      requireFromServer.resolve(`${name}/package.json`);
    } catch {
      missing.push(name);
    }
  }
  return missing;
}

export function checkRuntimeInstall(repoRoot = REPO_ROOT) {
  const nodeModulesDir = path.join(SERVER_ROOT, 'node_modules');
  const missingPackages = findMissingPackages();
  const sharedStorage = isSharedStorage(repoRoot);

  return {
    ok: missingPackages.length === 0,
    repoRoot,
    serverRoot: SERVER_ROOT,
    nodeModulesPresent: fs.existsSync(nodeModulesDir),
    missingPackages,
    sharedStorage,
  };
}

export function formatRuntimeInstallHelp(result) {
  const lines = [
    `error: Tritium runtime dependencies are not installed or not loadable from ${result.serverRoot}.`,
  ];

  if (!result.nodeModulesPresent) {
    lines.push('node_modules/ is missing.');
  } else if (result.missingPackages.length > 0) {
    lines.push(`missing packages: ${result.missingPackages.join(', ')}`);
  }

  lines.push(
    'run:',
    '  cd runtime/server',
    '  npm ci'
  );

  if (result.sharedStorage) {
    lines.push(
      '',
      'This checkout appears to be on shared storage.',
      'npm needs to create node_modules/.bin symlinks there, and that often fails with:',
      '  EACCES: permission denied, symlink ... node_modules/.bin/...',
      'Move the repo to a Linux-native writable path such as ~/Coding/tritium_os,',
      'then rerun npm ci.'
    );
  }

  lines.push(
    '',
    'If better-sqlite3 later reports a binary mismatch, run:',
    '  npm rebuild better-sqlite3'
  );

  return lines.join('\n');
}

if (import.meta.url === url.pathToFileURL(process.argv[1] ?? '').href) {
  const result = checkRuntimeInstall();
  if (result.ok) {
    console.log(`[tritium] runtime preflight OK (${REQUIRED_PACKAGES.join(', ')})`);
    process.exit(0);
  }

  console.error(formatRuntimeInstallHelp(result));
  process.exit(2);
}
