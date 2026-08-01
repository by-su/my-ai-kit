from pathlib import Path
from adapters import ALL_ADAPTERS
from src.config import KIT_DIR, CACHE_DIR, load_manifest, load_state

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

def sync_active_skills():
    manifest = load_manifest()
    state = load_state()
    
    enabled_optionals = state.get("enabled_optionals", [])
    
    active_skills = []
    
    # Core skills are always active
    for item in manifest.get("core", []):
        path = resolve_skill_path(item)
        if path and path.exists():
            active_skills.append((item.get("name"), path))
            
    # Optional skills check
    for item in manifest.get("optional", []):
        name = item.get("name")
        is_default = item.get("default_enabled", False)
        
        if name in enabled_optionals or (is_default and name not in state.get("disabled_optionals", [])):
            path = resolve_skill_path(item)
            if path and path.exists():
                active_skills.append((name, path))

    results = []
    for adapter in ALL_ADAPTERS:
        for name, path in active_skills:
            success, msg = adapter.link_skill(name, path)
            results.append(msg)
            
    return results
