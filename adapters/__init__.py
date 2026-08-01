from .base import BaseAdapter
from pathlib import Path

class AntigravityAdapter(BaseAdapter):
    def __init__(self):
        super().__init__("Antigravity/Gemini", Path.home() / ".gemini" / "antigravity-cli" / "skills")

class ClaudeCodeAdapter(BaseAdapter):
    def __init__(self):
        super().__init__("Claude Code", Path.home() / ".claude" / "plugins")

class CodexAdapter(BaseAdapter):
    def __init__(self):
        super().__init__("OpenAI Codex", Path.home() / ".codex" / "skills")

ALL_ADAPTERS = [
    AntigravityAdapter(),
    ClaudeCodeAdapter(),
    CodexAdapter()
]
