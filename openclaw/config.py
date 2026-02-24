import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Config:
    anthropic_api_key: str = ""
    github_token: str = ""
    github_repo: str = "faegents/conductor-workspace"
    github_branch: str = "main"


def load_config() -> Config:
    """Load config from ~/.openclaw/config.json and/or environment variables."""
    data: dict = {}
    config_path = Path.home() / ".openclaw" / "config.json"
    if config_path.exists():
        try:
            with open(config_path) as f:
                data = json.load(f)
        except Exception:
            pass

    return Config(
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY") or data.get("anthropic_api_key", ""),
        github_token=os.environ.get("GITHUB_TOKEN") or data.get("github_token", ""),
        github_repo=os.environ.get("OPENCLAW_REPO") or data.get("github_repo", "faegents/conductor-workspace"),
        github_branch=os.environ.get("OPENCLAW_BRANCH") or data.get("github_branch", "main"),
    )


def save_config(config: Config) -> None:
    """Save config to ~/.openclaw/config.json."""
    config_path = Path.home() / ".openclaw" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(
            {
                "anthropic_api_key": config.anthropic_api_key,
                "github_token": config.github_token,
                "github_repo": config.github_repo,
                "github_branch": config.github_branch,
            },
            f,
            indent=2,
        )
