import json
import re
from pathlib import Path
from src.config import load_manifest, KIT_DIR

HOME = Path.home()

SESSION_HOOK_START_CMD = f"python3 {KIT_DIR / 'bin' / 'mykit'} session-hook start"
SESSION_HOOK_END_CMD = f"python3 {KIT_DIR / 'bin' / 'mykit'} session-hook end"

CLAUDE_SETTINGS = HOME / ".claude" / "settings.json"
ANTIGRAVITY_SETTINGS = HOME / ".gemini" / "antigravity-cli" / "settings.json"
CODEX_CONFIG = HOME / ".codex" / "config.toml"

CODEX_BEGIN_MARKER = "# BEGIN mykit managed"
CODEX_END_MARKER = "# END mykit managed"
CODEX_MANAGED_KEYS = ("sandbox_mode", "approval_policy")


def to_claude_pattern(cmd: str) -> str:
    return f"Bash({cmd}:*)"


def to_antigravity_pattern(cmd: str) -> str:
    return f"command({cmd})"


def read_json_file(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def write_json_file(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def merge_allow_patterns(existing: dict, new_patterns: list) -> dict:
    result = dict(existing)
    perms = dict(result.get("permissions", {}))
    allow = list(perms.get("allow", []))
    for pattern in new_patterns:
        if pattern not in allow:
            allow.append(pattern)
    perms["allow"] = allow
    result["permissions"] = perms
    return result


def sync_claude_permissions(cmds: list) -> str:
    patterns = [to_claude_pattern(c) for c in cmds]
    existing = read_json_file(CLAUDE_SETTINGS)
    merged = merge_allow_patterns(existing, patterns)
    write_json_file(CLAUDE_SETTINGS, merged)
    return f"Configured {len(patterns)} auto-approve pattern(s) -> {CLAUDE_SETTINGS}"


def sync_antigravity_permissions(cmds: list) -> str:
    patterns = [to_antigravity_pattern(c) for c in cmds]
    existing = read_json_file(ANTIGRAVITY_SETTINGS)
    merged = merge_allow_patterns(existing, patterns)
    write_json_file(ANTIGRAVITY_SETTINGS, merged)
    return f"Configured {len(patterns)} auto-approve pattern(s) -> {ANTIGRAVITY_SETTINGS}"


def render_codex_block(sandbox_mode: str, approval_policy: str) -> str:
    return (
        f'{CODEX_BEGIN_MARKER}\n'
        f'sandbox_mode = "{sandbox_mode}"\n'
        f'approval_policy = "{approval_policy}"\n'
        f'{CODEX_END_MARKER}'
    )


def neutralize_conflicting_keys(lines: list, keys: tuple) -> list:
    key_pattern = re.compile(r'^(' + '|'.join(re.escape(k) for k in keys) + r')\s*=')
    result = []
    inside_block = False
    for line in lines:
        stripped = line.strip()
        if stripped == CODEX_BEGIN_MARKER:
            inside_block = True
            result.append(line)
        elif stripped == CODEX_END_MARKER:
            inside_block = False
            result.append(line)
        elif not inside_block and key_pattern.match(stripped):
            result.append(f"# {line}  # neutralized by mykit, see managed block below")
        else:
            result.append(line)
    return result


def upsert_managed_block(content: str, block_body: str) -> str:
    pattern = re.compile(
        re.escape(CODEX_BEGIN_MARKER) + r".*?" + re.escape(CODEX_END_MARKER),
        re.DOTALL,
    )
    if pattern.search(content):
        return pattern.sub(block_body, content)
    if content and not content.endswith("\n"):
        content += "\n"
    if content:
        content += "\n"
    return content + block_body + "\n"


def sync_codex_config(sandbox_mode: str, approval_policy: str) -> str:
    CODEX_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    content = CODEX_CONFIG.read_text(encoding="utf-8") if CODEX_CONFIG.exists() else ""
    neutralized_lines = neutralize_conflicting_keys(content.splitlines(), CODEX_MANAGED_KEYS)
    neutralized = "\n".join(neutralized_lines)
    if content.endswith("\n") and neutralized and not neutralized.endswith("\n"):
        neutralized += "\n"
    block = render_codex_block(sandbox_mode, approval_policy)
    new_content = upsert_managed_block(neutralized, block)
    CODEX_CONFIG.write_text(new_content, encoding="utf-8")
    return f"Configured sandbox_mode/approval_policy -> {CODEX_CONFIG}"


def merge_hook_entries(existing: dict, event: str, command: str, timeout: int = 5) -> dict:
    result = dict(existing)
    hooks = dict(result.get("hooks", {}))
    groups = list(hooks.get(event, []))
    already_present = any(
        h.get("command") == command
        for group in groups
        for h in group.get("hooks", [])
    )
    if not already_present:
        groups.append({"matcher": "", "hooks": [{"type": "command", "command": command, "timeout": timeout}]})
    hooks[event] = groups
    result["hooks"] = hooks
    return result


def sync_session_hooks() -> str:
    existing = read_json_file(CLAUDE_SETTINGS)
    merged = merge_hook_entries(existing, "SessionStart", SESSION_HOOK_START_CMD)
    merged = merge_hook_entries(merged, "SessionEnd", SESSION_HOOK_END_CMD)
    write_json_file(CLAUDE_SETTINGS, merged)
    return f"Configured session tracking hooks -> {CLAUDE_SETTINGS}"


def merge_env_vars(existing: dict, new_env: dict) -> dict:
    result = dict(existing)
    env = dict(result.get("env", {}))
    for key, value in new_env.items():
        env.setdefault(key, value)
    result["env"] = env
    return result


def sync_claude_env_vars() -> str:
    manifest = load_manifest()
    env_defaults = manifest.get("claude_env_defaults", {})
    if not env_defaults:
        return "No claude_env_defaults defined in manifest.yaml"
    existing = read_json_file(CLAUDE_SETTINGS)
    merged = merge_env_vars(existing, env_defaults)
    write_json_file(CLAUDE_SETTINGS, merged)
    return f"Configured {len(env_defaults)} default env var(s) -> {CLAUDE_SETTINGS}"


def sync_auto_approve_permissions() -> list:
    manifest = load_manifest()
    cmds = manifest.get("auto_approve_commands", [])
    if not cmds:
        return ["No auto_approve_commands defined in manifest.yaml"]

    codex_cfg = manifest.get("global", {}).get("codex", {})
    sandbox_mode = codex_cfg.get("sandbox_mode", "workspace-write")
    approval_policy = codex_cfg.get("approval_policy", "on-request")

    return [
        sync_claude_permissions(cmds),
        sync_antigravity_permissions(cmds),
        sync_codex_config(sandbox_mode, approval_policy),
    ]

