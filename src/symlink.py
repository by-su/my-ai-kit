from pathlib import Path
from adapters import ALL_ADAPTERS
from src.config import KIT_DIR, CACHE_DIR, load_manifest, load_state, load_local_state

def resolve_skill_path(skill_item):
    source_type = skill_item.get("source", "local")
    name = skill_item.get("name")
    
    path_str = skill_item.get("path")
    if path_str:
        path_obj = Path(path_str).expanduser()
        if path_obj.is_absolute() or str(path_str).startswith("~"):
            return path_obj
        return KIT_DIR / path_str

    if source_type == "github":
        return CACHE_DIR / "fetched" / name
    return None

def find_sub_skills(base_path):
    """
    Finds complete skill root directories.
    When a skill directory is symlinked, its internal assets/, references/, scripts/, etc.
    remain completely intact inside the skill folder.
    """
    if not base_path or not base_path.exists():
        return {}

    skills = {}

    # Case 1: Root itself is a complete skill with SKILL.md
    if (base_path / "SKILL.md").exists():
        skills[base_path.name] = base_path
        return skills

    # Case 2: ecc-pruned-skills (each subfolder is a complete skill folder)
    if base_path.name == "ecc-pruned-skills":
        for item in base_path.iterdir():
            if item.is_dir():
                skills[item.name] = item
        return skills

    # Case 3: Structure like prompt-architect (skills/<skill-name>)
    if (base_path / "skills").exists():
        skills_dir = base_path / "skills"
        for item in skills_dir.iterdir():
            if item.is_dir():
                skills[item.name] = item
        if skills:
            return skills

    # Case 4: Structure like mengto-skills (agent-skills/<category>/<skill-name>)
    if (base_path / "agent-skills").exists():
        ag_dir = base_path / "agent-skills"
        for category in ag_dir.iterdir():
            if category.is_dir():
                for skill_folder in category.iterdir():
                    if skill_folder.is_dir():
                        skills[skill_folder.name] = skill_folder
        if skills:
            return skills

    # Case 5: Direct skill root folders in base_path
    for item in base_path.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            if (item / "SKILL.md").exists() or any(f.suffix == ".md" for f in item.glob("*.md")):
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
