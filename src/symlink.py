from pathlib import Path
from adapters import ALL_ADAPTERS
from src.config import KIT_DIR, CACHE_DIR, load_manifest, load_state, load_local_state

def resolve_skill_path(skill_item):
    source_type = skill_item.get("source", "local")
    name = skill_item.get("name")
    
    if source_type == "local":
        path_str = skill_item.get("path")
        path_obj = Path(path_str).expanduser()
        if path_obj.is_absolute():
            return path_obj
        return KIT_DIR / path_str
    elif source_type == "github":
        return CACHE_DIR / "fetched" / name
    return None

def sync_active_skills(cwd=None):
    if cwd is None:
        cwd = Path.cwd()

    manifest = load_manifest()
    state = load_state()
    local_state = load_local_state(cwd)

    global_enabled_optionals = state.get("enabled_optionals", [])
    local_enabled_optionals = local_state.get("enabled_optionals", [])

    results = []

    # 1. Core skills -> Always Global
    for item in manifest.get("core", []):
        name = item.get("name")
        path = resolve_skill_path(item)
        if path and path.exists():
            for adapter in ALL_ADAPTERS:
                _, msg = adapter.link_skill(name, path, is_local=False)
                results.append(msg)

    # 2. Optional skills -> Link to Global or Local pwd
    for item in manifest.get("optional", []):
        name = item.get("name")
        is_default = item.get("default_enabled", False)
        path = resolve_skill_path(item)

        if not path or not path.exists():
            continue

        # Check if enabled locally in pwd
        is_local_active = name in local_enabled_optionals
        
        # Check if enabled globally
        is_global_active = (name in global_enabled_optionals) or (is_default and name not in state.get("disabled_optionals", []))

        if is_local_active:
            for adapter in ALL_ADAPTERS:
                _, msg = adapter.link_skill(name, path, is_local=True, cwd=cwd)
                results.append(msg)
        elif is_global_active:
            for adapter in ALL_ADAPTERS:
                _, msg = adapter.link_skill(name, path, is_local=False)
                results.append(msg)

    return results
