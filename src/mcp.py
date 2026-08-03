import json
import os
import re
from pathlib import Path
from src.config import load_manifest

HOME = Path.home()

MCP_TARGETS = [
    HOME / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
    HOME / ".gemini" / "antigravity-cli" / "mcp_config.json",
    HOME / ".gemini" / "config" / "mcp_config.json",
    HOME / ".codex" / "mcp_config.json"
]

def resolve_env_vars(obj):
    """Recursively replaces ${VAR_NAME} with os.environ.get(VAR_NAME)"""
    if isinstance(obj, str):
        def replacer(match):
            var_name = match.group(1)
            return os.environ.get(var_name, match.group(0))
        return re.sub(r'\$\{([^}]+)\}', replacer, obj)
    elif isinstance(obj, dict):
        return {k: resolve_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [resolve_env_vars(item) for item in obj]
    return obj

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
