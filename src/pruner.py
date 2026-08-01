import shutil
from pathlib import Path
from src.config import load_manifest, KIT_DIR

UNIVERSAL_UTILITIES = {
    'git', 'review', 'reviewer', 'tdd', 'testing', 'security',
    'mcp', 'prompt', 'refactor', 'cleaner', 'verification',
    'performance', 'db', 'database', 'api', 'architecture', 'architect',
    'memory', 'distill', 'persona', 'comply', 'audit', 'quality',
    'debug', 'silent-failure', 'logistics', 'search', 'flow', 'pattern',
    'skill-create', 'instinct', 'status', 'command', 'homunculus', 'loop'
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
    
    # 1. Check if it matches any keyword in the active stack profile
    for kw in profile_keywords:
        if kw.lower() in lower_name:
            return True
            
    # 2. Check if it matches universal developer utilities
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
                    
    # 2. Include all ECC Custom Commands
    commands_dir = ecc_base / "commands"
    if commands_dir.exists():
        for cmd_file in commands_dir.glob("*.md"):
            cmd_name = cmd_file.stem
            cmd_dest_dir = target_dir / cmd_name
            cmd_dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(cmd_file, cmd_dest_dir / "SKILL.md")
            included.append(f"command:{cmd_name}")

    return included, excluded
