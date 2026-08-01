import os
import shutil
from pathlib import Path

class BaseAdapter:
    def __init__(self, name, target_dir):
        self.name = name
        self.target_dir = Path(target_dir).expanduser()

    def ensure_target_dir(self):
        self.target_dir.mkdir(parents=True, exist_ok=True)

    def link_skill(self, skill_name, source_path):
        self.ensure_target_dir()
        dest = self.target_dir / skill_name

        # If symlink or file/folder exists, clean it up first for clean sync
        if dest.is_symlink() or dest.exists():
            if dest.is_dir() and not dest.is_symlink():
                shutil.rmtree(dest)
            else:
                dest.unlink()

        try:
            os.symlink(source_path.resolve(), dest)
            return True, f"Symlinked {skill_name} -> {self.name}"
        except Exception as e:
            # Fallback to copy if symlink fails
            if source_path.is_dir():
                shutil.copytree(source_path, dest)
            else:
                shutil.copy2(source_path, dest)
            return True, f"Copied {skill_name} -> {self.name} (Fallback)"

    def unlink_skill(self, skill_name):
        dest = self.target_dir / skill_name
        if dest.is_symlink() or dest.exists():
            if dest.is_dir() and not dest.is_symlink():
                shutil.rmtree(dest)
            else:
                dest.unlink()
            return True, f"Unlinked {skill_name} from {self.name}"
        return False, f"{skill_name} was not present in {self.name}"
