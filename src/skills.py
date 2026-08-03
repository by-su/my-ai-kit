from pathlib import Path

from src.config import load_local_state, load_state


def get_active_skill_items(manifest, cwd=None, include_all=False):
    if include_all:
        return manifest.get("core", []) + manifest.get("optional", [])

    if cwd is None:
        cwd = Path.cwd()

    state = load_state()
    local_state = load_local_state(cwd)
    global_enabled = set(state.get("enabled_optionals", []))
    local_enabled = set(local_state.get("enabled_optionals", []))
    disabled = set(state.get("disabled_optionals", []))

    items = list(manifest.get("core", []))
    for item in manifest.get("optional", []):
        name = item.get("name")
        is_default = item.get("default_enabled", False)
        if name in local_enabled or name in global_enabled or (is_default and name not in disabled):
            items.append(item)
    return items
