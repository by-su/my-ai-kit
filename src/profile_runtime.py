"""Profile-scoped roots for globally configured agent tools."""

from datetime import datetime
from pathlib import Path
import json
import os
import re
import shutil


PROFILE_RUNTIME_BASE = Path.home() / ".agent-skills" / "runtime"
PROFILE_BACKUP_BASE = Path.home() / ".agent-skills" / "legacy"
SKILL_STORE = Path.home() / ".agent-skills" / "store"

RUNTIME_ROOTS = {
    "claude": Path.home() / ".claude",
    "codex": Path.home() / ".codex",
    "antigravity-cli": Path.home() / ".gemini" / "antigravity-cli",
    "antigravity-config": Path.home() / ".gemini" / "config",
    "antigravity-skills": Path.home() / ".gemini" / "skills",
    "antigravity-agents": Path.home() / ".gemini" / "agents",
}


def profile_slug(profile_name):
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", str(profile_name))
    return slug.strip(".-") or "personal"


def profile_runtime_dir(profile_name, tool_name):
    return PROFILE_RUNTIME_BASE / profile_slug(profile_name) / tool_name


def _new_backup_dir():
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = PROFILE_BACKUP_BASE / timestamp
    suffix = 1
    while target.exists():
        target = PROFILE_BACKUP_BASE / f"{timestamp}-{suffix}"
        suffix += 1
    target.mkdir(parents=True, exist_ok=False)
    os.chmod(target, 0o700)
    return target


def _write_backup_manifest(backup_root, profile_name, entries):
    manifest = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "profile": str(profile_name),
        "entries": entries,
    }
    manifest_path = backup_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.chmod(manifest_path, 0o600)


def remove_profile_runtime(profile_name):
    target = PROFILE_RUNTIME_BASE / profile_slug(profile_name)
    if not target.exists():
        return False
    if target.is_symlink():
        target.unlink()
    else:
        shutil.rmtree(target)
    return True


def activate_profile_runtime(profile_name, migrate_legacy=False):
    """Activate one profile's global roots, backing up legacy roots once."""
    backup_root = _new_backup_dir() if migrate_legacy else None
    changes = []
    backup_entries = []

    for tool_name, global_root in RUNTIME_ROOTS.items():
        target = profile_runtime_dir(profile_name, tool_name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.mkdir(parents=True, exist_ok=True)

        if global_root.is_symlink():
            if global_root.resolve() == target.resolve():
                continue
            global_root.unlink()
        elif global_root.exists():
            if not migrate_legacy:
                raise FileExistsError(f"Existing global runtime root: {global_root}")
            shutil.move(str(global_root), str(backup_root / tool_name))
            backup_entries.append({"source": str(global_root), "backup": str(backup_root / tool_name)})

        global_root.parent.mkdir(parents=True, exist_ok=True)
        global_root.symlink_to(target, target_is_directory=True)
        changes.append((tool_name, global_root, target))

    if migrate_legacy and SKILL_STORE.exists():
        shutil.move(str(SKILL_STORE), str(backup_root / "store"))
        SKILL_STORE.mkdir(parents=True, exist_ok=True)
        backup_entries.append({"source": str(SKILL_STORE), "backup": str(backup_root / "store")})

    if backup_root:
        _write_backup_manifest(backup_root, profile_name, backup_entries)

    if backup_root and not any(backup_root.iterdir()):
        backup_root.rmdir()
        backup_root = None

    return backup_root, changes
