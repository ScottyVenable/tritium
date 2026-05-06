# Adapter: OpenAI / LM Studio (any OpenAI-compatible endpoint)

A small Node runner that wires Tritium agents to **any OpenAI-compatible API**: OpenAI, LM Studio, Ollama (with its OpenAI shim), Anthropic via proxy, Gemini via proxy, etc.

## Install

```bash
cd adapters/openai-lmstudio
npm install
```

Set environment variables:

```bash
export TRITIUM_BASE_URL="http://localhost:1234/v1"   # LM Studio default
export TRITIUM_API_KEY="not-required-for-lm-studio"  # required for OpenAI
export TRITIUM_MODEL="local-model"                   # or e.g. "gpt-4o", "claude-sonnet-4.5"
```

Run an agent:

```bash
node src/run.js --agent sol --task "implement a thing"
```

## Defaults

- **`dryRun: true`** by default (from `SETTINGS.jsonc → global.dryRun`). The runner prints what it would send and does **not** call the API. Set `dryRun: false` to spend tokens.
- API keys are read from environment only. They are never written to the repo or zip.

## How it works

1. Loads `SETTINGS.jsonc` and the requested agent's `prompts/system.md`.
2. Composes a chat completion request: `system = system.md + agent.md`, `user = --task`.
3. If `dryRun`, prints the composed request and exits.
4. Otherwise, POSTs to `${TRITIUM_BASE_URL}/chat/completions` with the configured model.
5. After the response arrives, optionally calls `tritium inbox check --agent <name>` to surface any messages the agent received during the call.

## Live coordination

For inter-agent IM/email, run the Tritium runtime separately:

```bash
cd /path/to/tritium/core/runtime/server && npm i && npm start
```

The runner dispatches IMs via the runtime's REST API when the agent's response includes a structured `[[IM to=<agent>]]…[[/IM]]` block.
