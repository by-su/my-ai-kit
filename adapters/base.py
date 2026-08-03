import os
import shutil
from pathlib import Path

class BaseAdapter:
    def __init__(self, name, global_dir, local_rel_path, agent_global_dir=None, agent_local_rel_path=None):
        self.name = name
        self.global_dir = Path(global_dir).expanduser()
        self.local_rel_path = Path(local_rel_path)
        
        self.agent_global_dir = Path(agent_global_dir).expanduser() if agent_global_dir else self.global_dir.parent / "agents"
        self.agent_local_rel_path = Path(agent_local_rel_path) if agent_local_rel_path else self.local_rel_path.parent / "agents"

    def get_target_dir(self, is_local=False, cwd=None):
        if is_local and cwd:
            return Path(cwd) / self.local_rel_path
        return self.global_dir

    def get_agent_target_dir(self, is_local=False, cwd=None):
        if is_local and cwd:
            return Path(cwd) / self.agent_local_rel_path
        return self.agent_global_dir

    def ensure_target_dir(self, is_local=False, cwd=None):
        target_dir = self.get_target_dir(is_local, cwd)
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir

    def ensure_agent_target_dir(self, is_local=False, cwd=None):
        agent_dir = self.get_agent_target_dir(is_local, cwd)
        agent_dir.mkdir(parents=True, exist_ok=True)
        return agent_dir

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
            return True, f"Symlinked skill {skill_name} -> {self.name} [{scope_label}: {target_dir}]"
        except Exception as e:
            if source_path.is_dir():
                shutil.copytree(source_path, dest)
            else:
                shutil.copy2(source_path, dest)
            return True, f"Copied skill {skill_name} -> {self.name} [{scope_label}: {target_dir}] (Fallback)"

    def link_agent(self, agent_name, source_path, is_local=False, cwd=None):
        target_dir = self.ensure_agent_target_dir(is_local, cwd)
        dest = target_dir / source_path.name

        if dest.is_symlink() or dest.exists():
            dest.unlink()

        scope_label = "Local (pwd)" if is_local else "Global"
        try:
            os.symlink(source_path.resolve(), dest)
            return True, f"Symlinked agent {source_path.name} -> {self.name} [{scope_label}: {target_dir}]"
        except Exception as e:
            shutil.copy2(source_path, dest)
            return True, f"Copied agent {source_path.name} -> {self.name} [{scope_label}: {target_dir}] (Fallback)"

    def unlink_skill(self, skill_name, is_local=False, cwd=None):
        target_dir = self.get_target_dir(is_local, cwd)
        dest = target_dir / skill_name
        if dest.is_symlink() or dest.exists():
            if dest.is_dir() and not dest.is_symlink():
                shutil.rmtree(dest)
            else:
                dest.unlink()
            scope_label = "Local (pwd)" if is_local else "Global"
            return True, f"Unlinked skill {skill_name} from {self.name} [{scope_label}]"
        return False, f"{skill_name} was not present in {self.name}"
