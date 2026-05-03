# Adapter: GitHub repo (remote, synced with GitHub.com)

`.github/` content for the GitHub-side of the repo: CI workflows, issue and PR templates, CODEOWNERS, labels, dependabot. This is what GitHub itself reads — separate from the local Copilot custom-agent files.

## Install

```bash
bash ../../scripts/install.sh --target /path/to/repo --adapter github-copilot-remote
```

## Files

- `.github/CODEOWNERS` — agent-keyed ownership.
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/ISSUE_TEMPLATE/` — bug, feature, agent-handoff, research-request.
- `.github/dependabot.yml`
- `.github/workflows/tritium-verify.yml` — runs the runtime smoke test on PRs that touch `tritium/`.
- `.github/labels.md` — canonical labels (Jesse maintains).
