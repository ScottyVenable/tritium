# Adapter: Gemini CLI

Drop-in `GEMINI.md` and per-agent prompts for [Google's Gemini CLI](https://github.com/google-gemini/gemini-cli).

## Install

```bash
bash ../../scripts/install.sh --target /path/to/repo --adapter gemini-cli
```

This copies `GEMINI.md`, `.gemini/settings.json`, and `agents/` into the target repo.

## How it works

Gemini CLI reads `GEMINI.md` from the project root, similar to `CLAUDE.md`. `.gemini/settings.json` configures tool permissions. Tritium's settings allow shell commands needed to run `tritium inbox check`, `git`, and editor operations.

## Live coordination

Same model as the other adapters: run the runtime separately and have the agent call `tritium inbox check` at its checkpoint cadence.
