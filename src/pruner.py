import shutil
from pathlib import Path
from src.config import load_manifest, KIT_DIR

# Universal core developer utilities (always included across all profiles)
UNIVERSAL_UTILITIES = {
    'git', 'review', 'reviewer', 'testing', 'security',
    'refactor', 'cleaner', 'verification', 'performance',
    'architecture', 'architect', 'quality', 'debug', 'skill-create',
    'instinct', 'status', 'loop', 'tdd', 'mcp', 'prompt', 'clean', 'ui', 'design',
    'write', 'writing', 'article', 'copywriting', 'post', 'docs', 'doc', 'readme', 'x', 'codex'
}

def get_profile_keywords(profile_name):
    manifest = load_manifest()
    profiles = manifest.get("profiles", {})
    prof = profiles.get(profile_name, profiles.get("personal", {}))
    return prof.get("include", [])

def is_skill_relevant(skill_name, profile_keywords):
    if "*" in profile_keywords:
        return True

    lower_name = skill_name.lower()
    
    # 1. Exact or keyword match against active stack profile
    for kw in profile_keywords:
        kw_lower = kw.lower()
        if len(kw_lower) <= 3:
            parts = lower_name.replace('-', ' ').replace('_', ' ').split()
            if kw_lower in parts:
                return True
        elif kw_lower in lower_name:
            return True
            
    # 2. Match against universal developer utilities
    for util in UNIVERSAL_UTILITIES:
        if util in lower_name:
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
