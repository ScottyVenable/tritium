"""Environment and path configuration for the bridge."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
DOTENV_PATH = REPO_ROOT / ".env"

# Fixed sub-paths inside the world tree. Brackets are part of the folder names
# on disk; they are NOT glob patterns. Always use Path() / pathlib (not glob).
AGENTS_SUBDIR = Path("[3] -- agents --") / "[3a] (agents) directory"
SOCIAL_HUB_SUBDIR = Path("[1] -- social hub --")


@dataclass(frozen=True)
class Config:
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_pass: str
    smtp_encryption: str

    imap_host: str
    imap_port: int
    imap_user: str
    imap_pass: str

    email_from_name_default: str
    email_to_scotty: str

    lm_studio_url: str
    lm_studio_model: str
    lm_studio_timeout: int

    world_root: Path
    project_name: str

    schedule_interval_minutes: int
    schedule_agents: list[str]
    schedule_actions: list[str]
    email_cap_per_agent: int
    email_cap_total: int

    repo_root: Path = REPO_ROOT

    @property
    def agents_root(self) -> Path:
        return self.world_root / AGENTS_SUBDIR

    @property
    def social_hub(self) -> Path:
        return self.world_root / SOCIAL_HUB_SUBDIR

    def agent_dir(self, name: str) -> Path:
        return self.agents_root / name.lower()


_REQUIRED = [
    "SMTP_HOST", "SMTP_USER", "SMTP_PASS",
    "IMAP_HOST", "IMAP_USER", "IMAP_PASS",
    "EMAIL_TO_SCOTTY",
    "LM_STUDIO_URL", "LM_STUDIO_MODEL",
    "WORLD_ROOT", "PROJECT_NAME",
]


def load() -> Config:
    load_dotenv(DOTENV_PATH)
    missing = [k for k in _REQUIRED if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"Missing required env vars: {', '.join(missing)}")

    def _split(name: str, default: str) -> list[str]:
        raw = os.getenv(name, default)
        return [p.strip() for p in raw.split(",") if p.strip()]

    return Config(
        smtp_host=os.environ["SMTP_HOST"],
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_user=os.environ["SMTP_USER"],
        smtp_pass=os.environ["SMTP_PASS"],
        smtp_encryption=os.getenv("SMTP_ENCRYPTION", "STARTTLS").upper(),

        imap_host=os.environ["IMAP_HOST"],
        imap_port=int(os.getenv("IMAP_PORT", "993")),
        imap_user=os.environ["IMAP_USER"],
        imap_pass=os.environ["IMAP_PASS"],

        email_from_name_default=os.getenv("EMAIL_FROM_NAME_DEFAULT", "Tritium Team"),
        email_to_scotty=os.environ["EMAIL_TO_SCOTTY"],

        lm_studio_url=os.environ["LM_STUDIO_URL"].rstrip("/"),
        lm_studio_model=os.environ["LM_STUDIO_MODEL"],
        lm_studio_timeout=int(os.getenv("LM_STUDIO_TIMEOUT_SECONDS", "120")),

        world_root=Path(os.environ["WORLD_ROOT"]),
        project_name=os.environ["PROJECT_NAME"],

        schedule_interval_minutes=int(os.getenv("SCHEDULE_INTERVAL_MINUTES", "30")),
        schedule_agents=_split("SCHEDULE_AGENTS", "Bridge,Sol,Jesse,Vex,Rook"),
        schedule_actions=_split("SCHEDULE_ACTIONS", "journal,message_board,email"),
        email_cap_per_agent=int(os.getenv("EMAIL_NIGHTLY_CAP_PER_AGENT", "3")),
        email_cap_total=int(os.getenv("EMAIL_NIGHTLY_CAP_TOTAL", "5")),
    )
