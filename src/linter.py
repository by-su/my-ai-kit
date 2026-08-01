import os
import re
from pathlib import Path
from src.config import load_manifest, KIT_DIR
from src.symlink import resolve_skill_path
from adapters import ALL_ADAPTERS

def parse_frontmatter(file_path):
    """Extracts and validates YAML frontmatter from a SKILL.md file."""
    if not file_path.exists():
        return None, "File does not exist"

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return None, f"Failed to read file: {e}"

    if not content.startswith("---"):
        return None, "Missing opening '---' YAML frontmatter header"

    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, "Missing closing '---' YAML frontmatter delimiter"

    yaml_block = parts[1].strip()
    data = {}
    
    for line in yaml_block.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if ':' in line:
            k, v = line.split(':', 1)
            data[k.strip()] = v.strip()

    if "name" not in data:
        return None, "Frontmatter missing required 'name' field"

    return data, None

def run_linter(fix=False):
    manifest = load_manifest()
    all_skills = manifest.get("core", []) + manifest.get("optional", [])
    
    print("\033[1;36m🔍 Running mykit lint checks...\033[0m\n")
    
    seen_names = {}
    errors_found = 0
    warnings_found = 0

    # 1. Check SKILL.md validity & Name collisions
    print("\033[1;34m[1/3] Validating SKILL.md Frontmatter & Names...\033[0m")
    for item in all_skills:
        skill_name = item.get("name")
        skill_path = resolve_skill_path(item)

        if not skill_path or not skill_path.exists():
            print(f"  \033[1;31m✗ {skill_name}\033[0m: Skill directory not found ({skill_path})")
            errors_found += 1
            continue

        skill_md = skill_path / "SKILL.md"
        if not skill_md.exists():
            print(f"  \033[1;33m⚠️ {skill_name}\033[0m: SKILL.md not found in {skill_path} (Directory only)")
            warnings_found += 1
            continue

        data, err = parse_frontmatter(skill_md)
        if err:
            print(f"  \033[1;31m✗ {skill_name}\033[0m: {err} ({skill_md})")
            errors_found += 1
        else:
            declared_name = data.get("name")
            if declared_name in seen_names:
                print(f"  \033[1;31m✗ Collision!\033[0m '{declared_name}' declared in multiple skills: {seen_names[declared_name]} & {skill_md}")
                errors_found += 1
            else:
                seen_names[declared_name] = str(skill_md)
                print(f"  \033[1;32m✓ {skill_name}\033[0m (name: '{declared_name}')")

    # 2. Check Adapter Symlinks
    print("\n\033[1;34m[2/3] Checking Adapter Symlink Integrity...\033[0m")
    for adapter in ALL_ADAPTERS:
        adapter.ensure_target_dir()
        broken = []
        for item in adapter.target_dir.glob("*"):
            if item.is_symlink() and not item.exists():
                broken.append(item)

        if broken:
            if fix:
                for b in broken:
                    b.unlink()
                print(f"  \033[1;32m✓ {adapter.name}\033[0m: Cleaned up {len(broken)} broken symlinks!")
            else:
                names = [b.name for b in broken]
                print(f"  \033[1;33m⚠️ {adapter.name}\033[0m: {len(broken)} broken symlink(s) found (run 'mykit lint --fix' to clean)")
                warnings_found += len(broken)
        else:
            print(f"  \033[1;32m✓ {adapter.name}\033[0m: All symlinks healthy")

    # 3. Check Manifest targets
    print("\n\033[1;34m[3/3] Validating Manifest Structure...\033[0m")
    targets = manifest.get("targets", {})
    active_targets = [k for k, v in targets.items() if v]
    print(f"  \033[1;32m✓ Target 에이전트\033[0m: {', '.join(active_targets)}")

    # Summary
    print("\n" + "─" * 50)
    if errors_found == 0 and warnings_found == 0:
        print("\033[1;32m🎉 Lint Passed cleanly! No errors or warnings found.\033[0m")
    else:
        print(f"\033[1;33mFinished with {errors_found} error(s) and {warnings_found} warning(s).\033[0m")

    return errors_found == 0
