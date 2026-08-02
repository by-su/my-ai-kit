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

def find_sub_skills(base_path):
    """
    Finds all individual skill directories or skill files inside a skill package/repo.
    """
    if not base_path or not base_path.exists():
        return {}

    skills = {}

    # Case 1: Root itself is a valid skill
    if (base_path / "SKILL.md").exists():
        skills[base_path.name] = base_path
        return skills

    # Case 2: Standard subdirectories (skills/, agent-skills/)
    search_dirs = []
    if (base_path / "skills").exists():
        search_dirs.append(base_path / "skills")
    if (base_path / "agent-skills").exists():
        search_dirs.append(base_path / "agent-skills")
    
    if not search_dirs:
        search_dirs.append(base_path)

    for s_dir in search_dirs:
        for item in s_dir.rglob("*"):
            if item.is_dir():
                if (item / "SKILL.md").exists():
                    skills[item.name] = item
                elif not any(p.name in ("assets", "references", "scripts", ".git") for p in item.parents):
                    # Check if directory contains markdown skill files
                    md_files = [f for f in item.glob("*.md") if f.name not in ("README.md", "LICENSE.md", "CHANGELOG.md")]
                    if md_files:
                        skills[item.name] = item

    if not skills and base_path.exists():
        skills[base_path.name] = base_path

    return skills

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
            sub_map = find_skills_map(name, path)
            for s_name, s_path in sub_map.items():
                for adapter in ALL_ADAPTERS:
                    _, msg = adapter.link_skill(s_name, s_path, is_local=False)
                    results.append(msg)

    # 2. Optional skills -> Link to Global or Local pwd
    for item in manifest.get("optional", []):
        name = item.get("name")
        is_default = item.get("default_enabled", False)
        path = resolve_skill_path(item)

        if not path or not path.exists():
            continue

        is_local_active = name in local_enabled_optionals
        is_global_active = (name in global_enabled_optionals) or (is_default and name not in state.get("disabled_optionals", []))

        sub_map = find_skills_map(name, path)

        if is_local_active:
            for s_name, s_path in sub_map.items():
                for adapter in ALL_ADAPTERS:
                    _, msg = adapter.link_skill(s_name, s_path, is_local=True, cwd=cwd)
                    results.append(msg)
        elif is_global_active:
            for s_name, s_path in sub_map.items():
                for adapter in ALL_ADAPTERS:
                    _, msg = adapter.link_skill(s_name, s_path, is_local=False)
                    results.append(msg)

    # 3. Custom Subagents (agents/*.md) -> Always Global
    agents_dir = KIT_DIR / "agents"
    if agents_dir.exists():
        for agent_file in agents_dir.glob("*.md"):
            for adapter in ALL_ADAPTERS:
                _, msg = adapter.link_agent(agent_file.stem, agent_file, is_local=False)
                results.append(msg)

    return results

def find_skills_map(pkg_name, base_path):
    skills = find_sub_skills(base_path)
    if not skills:
        return {pkg_name: base_path}
    return skills
