"""Tiny OpenAI-compatible client for the local LM Studio server."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import httpx

from .config import Config


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
    ) -> str:
        payload = {
            "model": model or self.cfg.lm_studio_model,
            "messages": [m.to_dict() if isinstance(m, ChatMessage) else m for m in messages],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        try:
            r = self._client.post("/chat/completions", json=payload)
        except httpx.HTTPError as e:
            raise LMStudioError(f"LM Studio HTTP error: {e}") from e
        if r.status_code >= 400:
            raise LMStudioError(f"LM Studio {r.status_code}: {r.text[:300]}")
        data = r.json()
        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError) as e:
            raise LMStudioError(f"Malformed LM Studio response: {data}") from e
