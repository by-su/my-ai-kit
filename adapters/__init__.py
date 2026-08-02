from .base import BaseAdapter
from pathlib import Path

class AntigravityAdapter(BaseAdapter):
    def __init__(self):
        super().__init__(
            "Antigravity/Gemini",
            Path.home() / ".gemini" / "antigravity-cli" / "skills",
            Path(".gemini") / "skills",
            Path.home() / ".gemini" / "antigravity-cli" / "agents",
            Path(".gemini") / "agents"
        )

class ClaudeCodeAdapter(BaseAdapter):
    def __init__(self):
        super().__init__(
            "Claude Code",
            Path.home() / ".claude" / "skills",
            Path(".claude") / "skills",
            Path.home() / ".claude" / "agents",
            Path(".claude") / "agents"
        )

class CodexAdapter(BaseAdapter):
    def __init__(self):
        super().__init__(
            "OpenAI Codex",
            Path.home() / ".codex" / "skills",
            Path(".codex") / "skills",
            Path.home() / ".codex" / "agents",
            Path(".codex") / "agents"
        )

ALL_ADAPTERS = [
    AntigravityAdapter(),
    ClaudeCodeAdapter(),
    CodexAdapter()
]
