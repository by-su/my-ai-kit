import subprocess
import tempfile
import unittest
from pathlib import Path

import src.worktree as worktree


def _init_repo(path):
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "Test"], check=True)
    (path / "README.md").write_text("hello\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(path), "add", "README.md"], check=True)
    subprocess.run(["git", "-C", str(path), "commit", "-q", "-m", "init"], check=True)


class FindRepoRootTests(unittest.TestCase):
    def test_raises_for_non_git_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(worktree.WorktreeError):
                worktree.find_repo_root(tmp)

    def test_returns_repo_root_for_git_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            _init_repo(repo)

            root = worktree.find_repo_root(repo)

            self.assertEqual(root, repo.resolve())


class DefaultWorktreePathTests(unittest.TestCase):
    def test_builds_repo_then_profile_path_under_home(self):
        self.old_home = worktree.Path.home
        worktree.Path.home = staticmethod(lambda: Path("/fake/home"))
        try:
            result = worktree.default_worktree_path(Path("/some/path/my-repo"), "pm")
            self.assertEqual(result, Path("/fake/home/.worktrees/my-repo/pm"))
        finally:
            worktree.Path.home = self.old_home


class EnsureWorktreeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        _init_repo(self.repo)

    def tearDown(self):
        self.tmp.cleanup()

    def test_raises_for_non_git_cwd(self):
        with tempfile.TemporaryDirectory() as other:
            with self.assertRaises(worktree.WorktreeError):
                worktree.ensure_worktree(other, "pm")

    def test_creates_worktree_at_explicit_path(self):
        target = Path(self.tmp.name) / "explicit-wt"

        path, created = worktree.ensure_worktree(self.repo, "pm", explicit_path=str(target))

        self.assertTrue(created)
        self.assertEqual(path, target.resolve())
        self.assertTrue((target / "README.md").exists())

    def test_reuses_existing_worktree_without_recreating(self):
        target = Path(self.tmp.name) / "explicit-wt"
        worktree.ensure_worktree(self.repo, "pm", explicit_path=str(target))

        path, created = worktree.ensure_worktree(self.repo, "pm", explicit_path=str(target))

        self.assertFalse(created)
        self.assertEqual(path, target.resolve())

    def test_raises_when_git_worktree_add_fails(self):
        target = Path(self.tmp.name) / "explicit-wt"
        target.mkdir()
        (target / "not-empty.txt").write_text("blocking file\n", encoding="utf-8")

        with self.assertRaises(worktree.WorktreeError):
            worktree.ensure_worktree(self.repo, "pm", explicit_path=str(target))


if __name__ == "__main__":
    unittest.main()
