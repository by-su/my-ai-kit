import os
import shutil
from pathlib import Path

class BaseAdapter:
    def __init__(self, name, global_dir, local_rel_path):
        self.name = name
        self.global_dir = Path(global_dir).expanduser()
        self.local_rel_path = Path(local_rel_path)

    def get_target_dir(self, is_local=False, cwd=None):
        if is_local and cwd:
            return Path(cwd) / self.local_rel_path
        return self.global_dir

    def ensure_target_dir(self, is_local=False, cwd=None):
        target_dir = self.get_target_dir(is_local, cwd)
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir

    def link_skill(self, skill_name, source_path, is_local=False, cwd=None):
        target_dir = self.ensure_target_dir(is_local, cwd)
        dest = target_dir / skill_name

        if dest.is_symlink() or dest.exists():
            if dest.is_dir() and not dest.is_symlink():
                shutil.rmtree(dest)
            else:
                dest.unlink()

        scope_label = "Local (pwd)" if is_local else "Global"
        try:
            os.symlink(source_path.resolve(), dest)
            return True, f"Symlinked {skill_name} -> {self.name} [{scope_label}: {target_dir}]"
        except Exception as e:
            if source_path.is_dir():
                shutil.copytree(source_path, dest)
            else:
                shutil.copy2(source_path, dest)
            return True, f"Copied {skill_name} -> {self.name} [{scope_label}: {target_dir}] (Fallback)"

    def unlink_skill(self, skill_name, is_local=False, cwd=None):
        target_dir = self.get_target_dir(is_local, cwd)
        dest = target_dir / skill_name
        if dest.is_symlink() or dest.exists():
            if dest.is_dir() and not dest.is_symlink():
                shutil.rmtree(dest)
            else:
                dest.unlink()
            scope_label = "Local (pwd)" if is_local else "Global"
            return True, f"Unlinked {skill_name} from {self.name} [{scope_label}]"
        return False, f"{skill_name} was not present in {self.name}"
