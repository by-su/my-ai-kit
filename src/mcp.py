import json
import os
import re
from pathlib import Path
from src.config import load_manifest, KIT_DIR

HOME = Path.home()

MCP_TARGETS = [
    HOME / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
    HOME / ".gemini" / "antigravity-cli" / "mcp_config.json",
    HOME / ".gemini" / "config" / "mcp_config.json",
    HOME / ".codex" / "mcp_config.json"
]

def load_env_files():
    """Loads key-value pairs from .env files into os.environ."""
    env_paths = [KIT_DIR / ".env", Path.cwd() / ".env"]
    for p in env_paths:
        if p.exists():
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            k, v = line.split('=', 1)
                            k, v = k.strip(), v.strip().strip('"\'')
                            if k and k not in os.environ:
                                os.environ[k] = v
            except Exception:
                pass

def resolve_env_vars(obj):
    """Recursively replaces ${VAR_NAME} with os.environ.get(VAR_NAME)"""
    load_env_files()
    if isinstance(obj, str):
        def replacer(match):
            var_name = match.group(1)
            val = os.environ.get(var_name)
            return val if val else match.group(0)
        return re.sub(r'\$\{([^}]+)\}', replacer, obj)
    elif isinstance(obj, dict):
        return {k: resolve_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [resolve_env_vars(item) for item in obj]
    return obj

def check_mcp_health():
    load_env_files()
    manifest = load_manifest()
    mcps = manifest.get("global", {}).get("mcp_servers", {})
    health_report = []

    for name, conf in mcps.items():
        missing_vars = []
        raw_str = json.dumps(conf)
        placeholders = re.findall(r'\$\{([^}]+)\}', raw_str)

        for p in placeholders:
            if not os.environ.get(p):
                missing_vars.append(p)

        cmd = conf.get("command", "")
        cmd_ok = shutil_which(cmd) is not None

        if missing_vars:
            status = f"\033[1;33m⚠️ Missing Env Var(s): {', '.join(missing_vars)}\033[0m"
        elif not cmd_ok:
            status = f"\033[1;31m✗ Command '{cmd}' not found in PATH\033[0m"
        else:
            status = "\033[1;32m🟢 Ready\033[0m"

        health_report.append((name, cmd, status, missing_vars))

    return health_report

def shutil_which(cmd):
    import shutil
    return shutil.which(cmd)

def sync_mcp_servers():
    manifest = load_manifest()
    mcp_servers = manifest.get("global", {}).get("mcp_servers", {})
    
    if not mcp_servers:
        return ["No MCP servers defined in manifest.yaml"]

    resolved_mcp = resolve_env_vars(mcp_servers)
    results = []

    for target_path in MCP_TARGETS:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        
        if target_path.exists():
            try:
                with open(target_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
            except Exception:
                data = {}

        data.setdefault("mcpServers", {})
        data["mcpServers"].update(resolved_mcp)

        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        results.append(f"Merged {len(resolved_mcp)} MCP server(s) -> {target_path}")

    return results
