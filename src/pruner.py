import shutil
from pathlib import Path
from src.config import load_manifest, load_state, KIT_DIR

# Universal core developer utilities (keyword-based, used for SKILL pruning)
UNIVERSAL_UTILITIES = {
    'git', 'testing', 'security',
    'refactor', 'cleaner', 'verification', 'performance',
    'architecture', 'architect', 'quality', 'debug', 'skill-create',
    'instinct', 'status', 'loop', 'tdd', 'mcp', 'prompt', 'clean', 'ui', 'design',
    'write', 'writing', 'article', 'copywriting', 'post', 'docs', 'doc', 'readme', 'fix', 'x', 'codex',
}


# Universal agents: always deployed regardless of active tech-stack profile.
# These provide value across ANY project (architecture, review, security, etc.)
UNIVERSAL_AGENTS = {
    # Orchestration & planning
    'architect', 'code-architect', 'chief-of-staff', 'planner',
    # Code quality & review
    'code-reviewer', 'code-explorer', 'code-simplifier', 'refactor-cleaner',
    'comment-analyzer', 'silent-failure-hunter',
    # Testing & reliability
    'e2e-runner', 'tdd-guide', 'pr-test-analyzer', 'build-error-resolver',
    # Security & performance
    'security-reviewer', 'performance-optimizer',
    # Docs & specs
    'doc-updater', 'docs-lookup', 'spec-miner',
    # AI agents
    'agent-evaluator', 'loop-operator',
    # Infrastructure & DB
    'database-reviewer', 'network-architect', 'network-config-reviewer', 'homelab-architect',
    # Accessibility & design
    'a11y-architect', 'type-design-analyzer', 'seo-specialist',
    # Conversation & analysis
    'conversation-analyzer',
}


def get_profile_keywords(profile_name):
    state = load_state()
    if profile_name.startswith("custom:"):
        custom_name = profile_name.split(":", 1)[1]
        custom_profiles = state.get("custom_profiles", {})
        if custom_name in custom_profiles:
            return custom_profiles[custom_name].get("include", [])
    if profile_name.startswith("custom:") and "profile_keywords" in state:
        return state.get("profile_keywords", [])

    manifest = load_manifest()
    profiles = manifest.get("profiles", {})
    prof = profiles.get(profile_name, profiles.get("personal", {}))
    return prof.get("include", [])

def is_skill_relevant(skill_name, profile_keywords):
    if "*" in profile_keywords:
        return True

    lower_name = skill_name.lower()
    parts = lower_name.replace('-', ' ').replace('_', ' ').split()
    
    # 1. Exact or keyword match against active stack profile
    for kw in profile_keywords:
        kw_lower = kw.lower()
        if len(kw_lower) <= 3:
            if kw_lower in parts:
                return True
        elif kw_lower in lower_name:
            return True
            
    # 2. Match against universal developer utilities
    for util in UNIVERSAL_UTILITIES:
        if len(util) <= 3:
            if util in parts:
                return True
        elif util in lower_name:
            return True
            
    return False

def is_agent_profile_relevant(agent_name, profile_keywords):
    """
    Strict profile match for agents — does NOT use UNIVERSAL_UTILITIES
    to avoid false positives (e.g. 'ui' matching 'build', 'java' matching 'javascript').
    Only matches if the profile keyword is a standalone word segment in the agent name.
    """
    if "*" in profile_keywords:
        return True

    parts = set(agent_name.lower().replace('-', ' ').replace('_', ' ').split())
    for kw in profile_keywords:
        if kw.lower() in parts:
            return True
    return False

def prune_skills_for_profile(ecc_base_dir, target_dir, profile_name="personal"):
    ecc_base = Path(ecc_base_dir).expanduser()
    target_dir = Path(target_dir).expanduser()
    
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    
    keywords = get_profile_keywords(profile_name)
    included = []
    excluded = []
    
    # 1. Prune skills directory
    skills_dir = ecc_base / "skills"
    if skills_dir.exists():
        for item in skills_dir.iterdir():
            if item.is_dir():
                if is_skill_relevant(item.name, keywords):
                    dest = target_dir / item.name
                    shutil.copytree(item, dest)
                    included.append(item.name)
                else:
                    excluded.append(item.name)
                    
    # 2. Filter ECC Custom Commands by profile relevance
    commands_dir = ecc_base / "commands"
    if commands_dir.exists():
        for cmd_file in commands_dir.glob("*.md"):
            cmd_name = cmd_file.stem
            if is_skill_relevant(cmd_name, keywords):
                cmd_dest_dir = target_dir / cmd_name
                cmd_dest_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(cmd_file, cmd_dest_dir / "SKILL.md")
                included.append(f"command:{cmd_name}")
            else:
                excluded.append(f"command:{cmd_name}")

    return included, excluded

def prune_mengto_skills_for_profile(mengto_base_dir, target_dir, profile_name="personal"):
    mengto_base = Path(mengto_base_dir).expanduser()
    target_dir = Path(target_dir).expanduser()
    
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    keywords = get_profile_keywords(profile_name)
    included = []
    excluded = []

    ag_dir = mengto_base / "agent-skills"
    if ag_dir.exists():
        for category in ag_dir.iterdir():
            if category.is_dir():
                for skill_folder in category.iterdir():
                    if skill_folder.is_dir():
                        # Include UI, Web Design, and Writing/Codex categories always
                        if is_skill_relevant(skill_folder.name, keywords) or category.name in ("ui", "web-design", "codex", "media"):
                            dest = target_dir / skill_folder.name
                            shutil.copytree(skill_folder, dest)
                            included.append(skill_folder.name)
                        else:
                            excluded.append(skill_folder.name)

    return included, excluded

def prune_pack_agents_for_profile(agents_src_dir, target_dir, profile_name="personal"):
    """
    Filters agent .md files from a skill pack's agents/ directory.
    Inclusion logic (OR):
      1. Agent stem is in UNIVERSAL_AGENTS -> always included regardless of profile
      2. Agent name matches active profile keywords via is_skill_relevant()
    """
    src = Path(agents_src_dir).expanduser()
    target = Path(target_dir).expanduser()

    if not src.exists():
        return [], []

    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)

    keywords = get_profile_keywords(profile_name)
    included = []
    excluded = []

    for agent_file in sorted(src.glob("*.md")):
        stem = agent_file.stem
        if stem in UNIVERSAL_AGENTS or is_agent_profile_relevant(stem, keywords):
            shutil.copy2(agent_file, target / agent_file.name)
            included.append(stem)
        else:
            excluded.append(stem)

    return included, excluded
