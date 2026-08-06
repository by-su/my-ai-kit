import tempfile
import unittest
import json
import stat
from pathlib import Path

import src.profile_runtime as runtime


class ProfileRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.old_base = runtime.PROFILE_RUNTIME_BASE
        self.old_backup = runtime.PROFILE_BACKUP_BASE
        self.old_store = runtime.SKILL_STORE
        self.old_roots = runtime.RUNTIME_ROOTS
        runtime.PROFILE_RUNTIME_BASE = root / "runtime"
        runtime.PROFILE_BACKUP_BASE = root / "legacy"
        runtime.SKILL_STORE = root / "store"
        runtime.RUNTIME_ROOTS = {
            "claude": root / "home" / ".claude",
            "codex": root / "home" / ".codex",
            "antigravity-cli": root / "home" / ".gemini" / "antigravity-cli",
            "antigravity-config": root / "home" / ".gemini" / "config",
            "antigravity-skills": root / "home" / ".gemini" / "skills",
            "antigravity-agents": root / "home" / ".gemini" / "agents",
        }

    def tearDown(self):
        runtime.PROFILE_RUNTIME_BASE = self.old_base
        runtime.PROFILE_BACKUP_BASE = self.old_backup
        runtime.SKILL_STORE = self.old_store
        runtime.RUNTIME_ROOTS = self.old_roots
        self.tmp.cleanup()

    def test_initialization_backs_up_legacy_roots_and_store(self):
        for tool, root in runtime.RUNTIME_ROOTS.items():
            root.mkdir(parents=True)
            (root / "legacy.txt").write_text(tool, encoding="utf-8")
        runtime.SKILL_STORE.mkdir(parents=True)
        (runtime.SKILL_STORE / "old-skill").write_text("old", encoding="utf-8")

        backup, changes = runtime.activate_profile_runtime("custom:pm", migrate_legacy=True)

        self.assertIsNotNone(backup)
        self.assertEqual(len(changes), len(runtime.RUNTIME_ROOTS))
        manifest = json.loads((backup / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["profile"], "custom:pm")
        self.assertEqual(stat.S_IMODE((backup / "manifest.json").stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(backup.stat().st_mode), 0o700)
        self.assertEqual((backup / "store" / "old-skill").read_text(encoding="utf-8"), "old")
        for tool, root in runtime.RUNTIME_ROOTS.items():
            target = runtime.profile_runtime_dir("custom:pm", tool)
            self.assertTrue(root.is_symlink())
            self.assertEqual(root.resolve(), target.resolve())
            self.assertEqual((backup / tool / "legacy.txt").read_text(encoding="utf-8"), tool)

    def test_switching_profile_keeps_existing_profile_roots(self):
        runtime.activate_profile_runtime("personal", migrate_legacy=False)

        backup, changes = runtime.activate_profile_runtime("pm", migrate_legacy=False)

        self.assertIsNone(backup)
        self.assertEqual(len(changes), len(runtime.RUNTIME_ROOTS))
        for tool, root in runtime.RUNTIME_ROOTS.items():
            self.assertEqual(root.resolve(), runtime.profile_runtime_dir("pm", tool).resolve())

    def test_remove_profile_runtime_removes_only_requested_profile(self):
        runtime.profile_runtime_dir("custom:pm", "claude").mkdir(parents=True)
        runtime.profile_runtime_dir("custom:other", "claude").mkdir(parents=True)

        self.assertTrue(runtime.remove_profile_runtime("custom:pm"))
        self.assertFalse(runtime.profile_runtime_dir("custom:pm", "claude").parent.exists())
        self.assertTrue(runtime.profile_runtime_dir("custom:other", "claude").parent.exists())


if __name__ == "__main__":
    unittest.main()
