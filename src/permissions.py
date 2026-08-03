import json
import os
from pathlib import Path
from src.config import load_manifest, KIT_DIR

HOME = Path.home()

CLAUDE_SETTINGS = HOME / ".claude" / "settings.json"
ANTIGRAVITY_PERMS = HOME / ".gemini" / "antigravity-cli" / "permissions.json"
GEMINI_PERMS = HOME / ".gemini" / "config" / "permissions.json"
CODEX_CONFIG = HOME / ".codex" / "config.toml"
CODEX_PERMS = HOME / ".codex" / "permissions.json"

def sync_auto_approve_permissions():
    manifest = load_manifest()
    cmds = manifest.get("auto_approve_commands", [])
    if not cmds:
        return ["No auto_approve_commands defined in manifest.yaml"]

    results = []

    # 1. Claude Code (~/.claude/settings.json)
    CLAUDE_SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    c_data = {}
    if CLAUDE_SETTINGS.exists():
        try:
            with open(CLAUDE_SETTINGS, 'r', encoding='utf-8') as f:
                c_data = json.load(f)
        except Exception:
            c_data = {}
    
    c_data["autoApproveCommands"] = cmds
    c_data["auto_mode"] = True
    with open(CLAUDE_SETTINGS, 'w', encoding='utf-8') as f:
        json.dump(c_data, f, indent=2, ensure_ascii=False)
    results.append(f"Configured {len(cmds)} auto-approve command(s) -> {CLAUDE_SETTINGS}")

    # 2. Antigravity / Gemini CLI (~/.gemini/antigravity-cli/permissions.json)
    for p_path in [ANTIGRAVITY_PERMS, GEMINI_PERMS]:
        p_path.parent.mkdir(parents=True, exist_ok=True)
        g_data = {}
        if p_path.exists():
            try:
                with open(p_path, 'r', encoding='utf-8') as f:
                    g_data = json.load(f)
            except Exception:
                g_data = {}
        
        g_data["auto_approved_commands"] = cmds
        g_data["allow_read_only_commands"] = True
        with open(p_path, 'w', encoding='utf-8') as f:
            json.dump(g_data, f, indent=2, ensure_ascii=False)
        results.append(f"Configured {len(cmds)} auto-approve command(s) -> {p_path}")

    # 3. OpenAI Codex (~/.codex/config.toml & permissions.json)
    CODEX_PERMS.parent.mkdir(parents=True, exist_ok=True)
    codex_data = {}
    if CODEX_PERMS.exists():
        try:
            with open(CODEX_PERMS, 'r', encoding='utf-8') as f:
                codex_data = json.load(f)
        except Exception:
            codex_data = {}

    codex_data["auto_approve_commands"] = cmds
    codex_data["approval_policy"] = "on_destructive_only"
    with open(CODEX_PERMS, 'w', encoding='utf-8') as f:
        json.dump(codex_data, f, indent=2, ensure_ascii=False)
    results.append(f"Configured {len(cmds)} auto-approve command(s) -> {CODEX_PERMS}")

    return results
