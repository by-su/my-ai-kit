from pathlib import Path
from adapters import ALL_ADAPTERS
from src.config import (
    KIT_DIR, CACHE_DIR, load_manifest, load_state, load_local_state, save_local_state,
    get_active_profile, resolve_profile_binding,
)
from src.pruner import profile_pack_dir, get_profile_enable_optionals

PRUNABLE_PACKS = {"ecc-suite", "mengto-skills"}


def get_enabled_pruning_packs(state=None):
    if state is None:
        state = load_state()
    return set(state.get("enabled_pruning_packs", list(PRUNABLE_PACKS)))

def resolve_skill_path(skill_item, active_profile=None):
    source_type = skill_item.get("source", "local")
    name = skill_item.get("name")

    if source_type == "github" and name in PRUNABLE_PACKS:
        enabled_pruning = get_enabled_pruning_packs()
        if name not in enabled_pruning:
            return CACHE_DIR / "fetched" / name

        if active_profile:
            return profile_pack_dir(active_profile, name)

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

def find_pack_agents(base_path, fetched_name=None, active_profile=None):
    """
    Returns list of agent .md files for a skill pack.
    Priority: 1) pruned-agents dir, 2) base_path/agents/, 3) fetched/name/agents/
    """
    # 1. Pruned agents dir (created by prune_pack_agents_for_profile during sync)
    if fetched_name and active_profile and fetched_name in get_enabled_pruning_packs():
        pruned_dir = profile_pack_dir(active_profile, f"{fetched_name}-agents")
        if pruned_dir.exists():
            found = list(pruned_dir.glob("*.md"))
            if found:
                return found

    # 2. base_path/agents/ and fetched fallback
    search_paths = [base_path]
    if fetched_name:
        fetched_path = CACHE_DIR / "fetched" / fetched_name
        if fetched_path.exists() and fetched_path != base_path:
            search_paths.append(fetched_path)

    for path in search_paths:
        agents_dir = path / "agents"
        if agents_dir.exists() and agents_dir.is_dir():
            found = list(agents_dir.glob("*.md"))
            if found:
                return found
    return []


def sync_active_skills(cwd=None):
    if cwd is None:
        cwd = Path.cwd()

    manifest = load_manifest()
    state = load_state()
    local_state = load_local_state(cwd)
    active_profile = get_active_profile(cwd)
    is_bound = resolve_profile_binding(cwd) is not None

    global_enabled_optionals = state.get("enabled_optionals", [])
    local_enabled_optionals = local_state.get("enabled_optionals", [])
    # Only auto-activate a profile's declared optionals as *local* when cwd is explicitly
    # bound to that profile. For the plain global case, enable_optionals_for_profile()
    # (called from `mykit profile use --global`) already persisted them into
    # state["enabled_optionals"], so they flow through global_enabled_optionals below.
    profile_optionals = set(get_profile_enable_optionals(active_profile)) if is_bound else set()

    # Track which local skill/agent names exist *because* the active profile put them
    # there (as opposed to an explicit `mykit enable <skill>`), so switching this folder's
    # profile can cleanly unlink whatever the *previous* profile added instead of
    # accumulating skills across every profile ever used here.
    previously_profile_linked_skills = set(local_state.get("profile_linked_skills", []))
    previously_profile_linked_agents = set(local_state.get("profile_linked_agents", []))
    newly_profile_linked_skills = set()
    newly_profile_linked_agents = set()

    results = []

    # 0. Clean up stale agent symlinks from all global adapter agent dirs
    for adapter in ALL_ADAPTERS:
        ag_dir = adapter.ensure_agent_target_dir(is_local=False)
        for item in list(ag_dir.glob("*.md")):
            if item.is_symlink():
                item.unlink()

    # 1. Core skills -> Always Global
    for item in manifest.get("core", []):
        name = item.get("name")
        path = resolve_skill_path(item, active_profile=active_profile)
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
        path = resolve_skill_path(item, active_profile=active_profile)

        if not path or not path.exists():
            continue

        is_prunable_bound = is_bound and name in PRUNABLE_PACKS
        is_profile_driven = (name in profile_optionals) or is_prunable_bound
        is_local_active = (name in local_enabled_optionals) or is_profile_driven
        is_global_active = (not is_prunable_bound) and (
            (name in global_enabled_optionals) or (is_default and name not in state.get("disabled_optionals", []))
        )

        sub_map = find_skills_map(name, path)
        pack_agents = find_pack_agents(path, fetched_name=name, active_profile=active_profile)
        # Only track as "profile-driven" if it's not *also* explicitly enabled via
        # `mykit enable <skill>` locally - that's user-managed and must survive profile switches.
        track_as_profile_driven = is_profile_driven and name not in local_enabled_optionals

        if is_local_active:
            for s_name, s_path in sub_map.items():
                if track_as_profile_driven:
                    newly_profile_linked_skills.add(s_name)
                for adapter in ALL_ADAPTERS:
                    _, msg = adapter.link_skill(s_name, s_path, is_local=True, cwd=cwd)
                    results.append(msg)
            for agent_file in pack_agents:
                if track_as_profile_driven:
                    newly_profile_linked_agents.add(agent_file.stem)
                for adapter in ALL_ADAPTERS:
                    _, msg = adapter.link_agent(agent_file.stem, agent_file, is_local=True, cwd=cwd)
                    results.append(msg)
        elif is_global_active:
            for s_name, s_path in sub_map.items():
                for adapter in ALL_ADAPTERS:
                    _, msg = adapter.link_skill(s_name, s_path, is_local=False)
                    results.append(msg)
            for agent_file in pack_agents:
                for adapter in ALL_ADAPTERS:
                    _, msg = adapter.link_agent(agent_file.stem, agent_file, is_local=False)
                    results.append(msg)

    # 2.5 Unlink local skills/agents the *previous* profile added that the current
    # profile no longer wants, so switching a bound folder's profile is a clean swap.
    stale_skills = previously_profile_linked_skills - newly_profile_linked_skills
    stale_agents = previously_profile_linked_agents - newly_profile_linked_agents
    for adapter in ALL_ADAPTERS:
        for s_name in stale_skills:
            adapter.unlink_skill(s_name, is_local=True, cwd=cwd)
        agent_dir = adapter.get_agent_target_dir(is_local=True, cwd=cwd)
        for a_name in stale_agents:
            dest = agent_dir / f"{a_name}.md"
            if dest.is_symlink() or dest.exists():
                dest.unlink()

    local_state["profile_linked_skills"] = sorted(newly_profile_linked_skills)
    local_state["profile_linked_agents"] = sorted(newly_profile_linked_agents)
    save_local_state(local_state, cwd)

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
