import httpx
import base64
from typing import Optional


class WorkspaceFetcher:
    """Fetch workspace files from GitHub."""

    BASE = "https://api.github.com"

    def __init__(self, token: str, repo: str, branch: str = "main"):
        self.token = token
        self.repo = repo
        self.branch = branch
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def get_file(self, path: str) -> Optional[str]:
        """Fetch a file from the workspace repo. Returns decoded content or None."""
        url = f"{self.BASE}/repos/{self.repo}/contents/{path}"
        try:
            resp = httpx.get(
                url,
                headers=self.headers,
                params={"ref": self.branch},
                timeout=10,
            )
            if resp.status_code == 200:
                content = resp.json().get("content", "")
                return base64.b64decode(content).decode("utf-8")
        except Exception:
            pass
        return None

    def get_workspace_state(self) -> dict:
        """Fetch all key workspace files."""
        return {
            "memory": self.get_file("memory/MEMORY.md"),
            "todo": self.get_file("memory/todo.md"),
            "monitor_logs": self.get_file("memory/monitor_logs.md"),
            "lessons": self.get_file("memory/lessons_learned.md"),
        }
