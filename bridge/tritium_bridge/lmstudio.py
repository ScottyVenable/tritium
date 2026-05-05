"""Tiny OpenAI-compatible client for the local LM Studio server.

Supports an optional tool-call loop (OpenAI tools format). When the loaded
model emits `tool_calls`, the client executes them locally via
``tritium_bridge.tools`` and feeds the results back as ``role=tool``
messages, looping up to ``MAX_TOOL_ITERATIONS`` times before falling
through to the visible content.

Models that do not support tool calling will simply return content with
no ``tool_calls`` field; the code logs ``tool_calls unsupported,
falling back`` once per process and behaves identically to the legacy
context-injection path.

A best-effort ``<think>...</think>`` stripper is always applied to the
final visible content, since several local models (qwen3-thinking,
deepseek-r1 distills) emit hidden reasoning inline.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Iterable

import httpx

from .config import Config

log = logging.getLogger("tritium_bridge.lmstudio")

MAX_TOOL_ITERATIONS = 3
_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_TOOL_UNSUPPORTED_LOGGED = False


def _strip_think(text: str) -> str:
    if not text:
        return text
    return _THINK_BLOCK.sub("", text).strip()


@dataclass
class ChatMessage:
    role: str  # 'system' | 'user' | 'assistant'
    content: str

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


class LMStudioError(RuntimeError):
    pass


class LMStudioClient:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self._client = httpx.Client(
            base_url=cfg.lm_studio_url,
            timeout=cfg.lm_studio_timeout,
            headers={"Authorization": "Bearer lm-studio"},
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def list_models(self) -> list[str]:
        r = self._client.get("/models")
        r.raise_for_status()
        return [m["id"] for m in r.json().get("data", [])]

    def ping(self) -> bool:
        try:
            self.list_models()
            return True
        except Exception:
            return False

    def chat(
        self,
        messages: Iterable[ChatMessage | dict],
        max_tokens: int = 600,
        temperature: float = 0.7,
        model: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_executor=None,
    ) -> str:
        """Run a chat completion.

        If ``tools`` and ``tool_executor`` are both provided, the client will
        loop on ``tool_calls`` (calling ``tool_executor(name, args_json) ->
        str`` for each) up to ``MAX_TOOL_ITERATIONS`` times, then return the
        final visible content. Tool support is best-effort: if the loaded
        model returns no ``tool_calls`` field, the loop exits immediately
        and we return the plain content (logged once per process).

        ``<think>...</think>`` blocks are always stripped from the final
        return value.
        """
        # Normalize input messages into plain dicts so we can append
        # assistant-with-tool_calls and role=tool entries on each iteration.
        msg_list: list[dict[str, Any]] = [
            m.to_dict() if isinstance(m, ChatMessage) else dict(m)
            for m in messages
        ]

        use_tools = bool(tools) and tool_executor is not None
        iterations = MAX_TOOL_ITERATIONS if use_tools else 1

        # Thinking models (qwen3-thinking, nemotron, deepseek-r1 distills)
        # spend a large slice of completion budget on hidden reasoning. When
        # tools are attached they reason even more (about which tool to use).
        # Bump the per-call ceiling so the model can finish thinking AND
        # still emit either a tool_call or visible content.
        effective_max = max(max_tokens, 2000) if use_tools else max_tokens

        for i in range(iterations):
            payload: dict[str, Any] = {
                "model": model or self.cfg.lm_studio_model,
                "messages": msg_list,
                "max_tokens": effective_max,
                "temperature": temperature,
            }
            if use_tools:
                payload["tools"] = tools
                payload["tool_choice"] = "auto"

            try:
                r = self._client.post("/chat/completions", json=payload)
            except httpx.HTTPError as e:
                raise LMStudioError(f"LM Studio HTTP error: {e}") from e
            if r.status_code >= 400:
                raise LMStudioError(f"LM Studio {r.status_code}: {r.text[:300]}")
            data = r.json()
            try:
                msg = data["choices"][0]["message"]
            except (KeyError, IndexError) as e:
                raise LMStudioError(f"Malformed LM Studio response: {data}") from e

            tool_calls = msg.get("tool_calls") or []
            finish_reason = data["choices"][0].get("finish_reason", "")
            if use_tools and tool_calls:
                # Echo the assistant's tool_call message into history (OpenAI
                # tool-loop convention) before appending tool results.
                msg_list.append({
                    "role": "assistant",
                    "content": msg.get("content") or "",
                    "tool_calls": tool_calls,
                })
                names = []
                for call in tool_calls:
                    fn = call.get("function") or {}
                    name = fn.get("name", "")
                    args_json = fn.get("arguments", "") or ""
                    names.append(name)
                    try:
                        result = tool_executor(name, args_json)
                    except Exception as e:  # defensive
                        log.exception("tool executor crashed for %s", name)
                        result = f"[tool error] {name}: {e}"
                    msg_list.append({
                        "role": "tool",
                        "tool_call_id": call.get("id", ""),
                        "name": name,
                        "content": result,
                    })
                log.info("tool_calls iter=%d names=%s", i + 1, ",".join(names))
                continue  # next iteration calls model again with tool results

            # No tool calls -> we have final content
            content = (msg.get("content") or "").strip()
            if use_tools and i == 0 and not tool_calls:
                global _TOOL_UNSUPPORTED_LOGGED
                if not _TOOL_UNSUPPORTED_LOGGED:
                    log.info("tool_calls unsupported, falling back")
                    _TOOL_UNSUPPORTED_LOGGED = True
            stripped = _strip_think(content)
            # If the model burned its budget thinking and produced no visible
            # text, retry once without tools at the original (smaller) budget.
            if use_tools and not stripped and finish_reason == "length":
                log.info("empty content with finish=length; retrying without tools")
                payload_retry = {
                    "model": model or self.cfg.lm_studio_model,
                    "messages": msg_list,
                    "max_tokens": max(max_tokens, 3500),
                    "temperature": temperature,
                }
                try:
                    rr = self._client.post("/chat/completions", json=payload_retry)
                    rr.raise_for_status()
                    dd = rr.json()
                    return _strip_think(
                        (dd["choices"][0]["message"].get("content") or "").strip()
                    )
                except Exception as e:
                    log.warning("no-tools retry failed: %s", e)
            return stripped

        # Hit MAX_TOOL_ITERATIONS without final content. Force one more
        # call without tools to extract a clean answer.
        payload = {
            "model": model or self.cfg.lm_studio_model,
            "messages": msg_list,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        try:
            r = self._client.post("/chat/completions", json=payload)
            r.raise_for_status()
            data = r.json()
            return _strip_think((data["choices"][0]["message"].get("content") or "").strip())
        except Exception as e:
            log.warning("tool loop exhausted and final flush failed: %s", e)
            return ""
