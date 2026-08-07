from pathlib import Path

from src.config import get_active_profile, load_local_state, resolve_profile_binding
from src.pruner import get_profile_enable_optionals


def get_active_skill_items(manifest, cwd=None, include_all=False):
    if include_all:
        return manifest.get("core", []) + manifest.get("optional", [])

    if cwd is None:
        cwd = Path.cwd()

    local_state = load_local_state(cwd)
    local_enabled = set(local_state.get("enabled_optionals", []))

    # A skill a bound profile declares via `enable_optionals` is just as "active"
    # as one enabled with `mykit enable` - sync_active_skills() (symlink.py) treats
    # them the same way, so this must too or profile-driven skills never get fetched.
    is_bound = resolve_profile_binding(cwd) is not None
    profile_enabled = set(get_profile_enable_optionals(get_active_profile(cwd))) if is_bound else set()

    items = list(manifest.get("core", []))
    for item in manifest.get("optional", []):
        name = item.get("name")
        if name in local_enabled or name in profile_enabled:
            items.append(item)
    return items
