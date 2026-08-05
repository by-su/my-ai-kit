import subprocess
from pathlib import Path


class WorktreeError(Exception):
    pass


def _run_git(args, cwd):
    return subprocess.run(["git", "-C", str(cwd)] + args, capture_output=True, text=True)


def find_repo_root(cwd):
    result = _run_git(["rev-parse", "--show-toplevel"], cwd)
    if result.returncode != 0:
        raise WorktreeError(f"'{cwd}' is not inside a git repository - --worktree requires git.")
    return Path(result.stdout.strip())


def default_worktree_path(repo_root, profile_display_name):
    return Path.home() / ".worktrees" / repo_root.name / profile_display_name


def _existing_worktree_paths(repo_root):
    result = _run_git(["worktree", "list", "--porcelain"], repo_root)
    paths = []
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            paths.append(Path(line[len("worktree "):]).resolve())
    return paths


def ensure_worktree(cwd, profile_display_name, explicit_path=None):
    """Create (or reuse) a git worktree for `profile_display_name`.

    Returns (resolved_path, created). Raises WorktreeError if `cwd` isn't inside a
    git repo or `git worktree add` fails (e.g. the branch it would auto-create
    already exists elsewhere).
    """
    repo_root = find_repo_root(cwd)
    target_path = (
        Path(explicit_path).expanduser().resolve()
        if explicit_path
        else default_worktree_path(repo_root, profile_display_name)
    )

    if target_path in _existing_worktree_paths(repo_root):
        return target_path, False

    target_path.parent.mkdir(parents=True, exist_ok=True)
    result = _run_git(["worktree", "add", str(target_path)], repo_root)
    if result.returncode != 0:
        raise WorktreeError(f"git worktree add failed: {result.stderr.strip()}")
    return target_path, True
