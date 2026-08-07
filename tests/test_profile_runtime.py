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

    def test_activate_profile_runtime_locks_down_runtime_dir_permissions(self):
        runtime.activate_profile_runtime("pm", migrate_legacy=False)

        for tool in runtime.RUNTIME_ROOTS:
            target = runtime.profile_runtime_dir("pm", tool)
            self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(target.parent.stat().st_mode), 0o700)

    def test_parked_owner_data_is_permission_locked_down(self):
        for tool, root in runtime.RUNTIME_ROOTS.items():
            root.mkdir(parents=True)
            (root / "owner.txt").write_text(tool, encoding="utf-8")

        runtime.activate_profile_runtime("custom:work", migrate_legacy=True, owner_profile="personal")

        for tool in runtime.RUNTIME_ROOTS:
            parked = runtime.profile_runtime_dir("personal", tool)
            self.assertEqual(stat.S_IMODE(parked.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(parked.parent.stat().st_mode), 0o700)

    def test_owner_profile_first_activation_leaves_real_directory_untouched(self):
        for tool, root in runtime.RUNTIME_ROOTS.items():
            root.mkdir(parents=True)
            (root / "owner.txt").write_text(tool, encoding="utf-8")

        backup, changes = runtime.activate_profile_runtime("personal", migrate_legacy=False, owner_profile="personal")

        self.assertIsNone(backup)
        self.assertEqual(changes, [])
        for tool, root in runtime.RUNTIME_ROOTS.items():
            self.assertFalse(root.is_symlink())
            self.assertEqual((root / "owner.txt").read_text(encoding="utf-8"), tool)

    def test_activating_non_owner_parks_owner_data_instead_of_archiving_it(self):
        for tool, root in runtime.RUNTIME_ROOTS.items():
            root.mkdir(parents=True)
            (root / "owner.txt").write_text(tool, encoding="utf-8")

        backup, changes = runtime.activate_profile_runtime("custom:work", migrate_legacy=True, owner_profile="personal")

        # migrate_legacy=True always creates a backup dir + manifest (pre-existing
        # behavior), but since owner data is parked rather than archived, nothing
        # is actually recorded as backed up.
        self.assertIsNotNone(backup)
        manifest = json.loads((backup / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["entries"], [])
        self.assertEqual(len(changes), len(runtime.RUNTIME_ROOTS))
        for tool, root in runtime.RUNTIME_ROOTS.items():
            target = runtime.profile_runtime_dir("custom:work", tool)
            self.assertTrue(root.is_symlink())
            self.assertEqual(root.resolve(), target.resolve())
            parked = runtime.profile_runtime_dir("personal", tool)
            self.assertEqual((parked / "owner.txt").read_text(encoding="utf-8"), tool)

    def test_switching_back_to_owner_restores_parked_data_as_real_directory(self):
        for tool, root in runtime.RUNTIME_ROOTS.items():
            root.mkdir(parents=True)
            (root / "owner.txt").write_text(tool, encoding="utf-8")

        runtime.activate_profile_runtime("custom:work", migrate_legacy=True, owner_profile="personal")
        backup, changes = runtime.activate_profile_runtime("personal", migrate_legacy=False, owner_profile="personal")

        self.assertIsNone(backup)
        self.assertEqual(len(changes), len(runtime.RUNTIME_ROOTS))
        for tool, root in runtime.RUNTIME_ROOTS.items():
            self.assertFalse(root.is_symlink())
            self.assertEqual((root / "owner.txt").read_text(encoding="utf-8"), tool)
            self.assertFalse(runtime.profile_runtime_dir("personal", tool).exists())

    def test_switching_between_two_non_owner_profiles_leaves_owner_data_parked(self):
        for tool, root in runtime.RUNTIME_ROOTS.items():
            root.mkdir(parents=True)
            (root / "owner.txt").write_text(tool, encoding="utf-8")

        runtime.activate_profile_runtime("custom:work", migrate_legacy=True, owner_profile="personal")
        backup, changes = runtime.activate_profile_runtime("custom:other", migrate_legacy=False, owner_profile="personal")

        self.assertIsNone(backup)
        self.assertEqual(len(changes), len(runtime.RUNTIME_ROOTS))
        for tool, root in runtime.RUNTIME_ROOTS.items():
            target = runtime.profile_runtime_dir("custom:other", tool)
            self.assertTrue(root.is_symlink())
            self.assertEqual(root.resolve(), target.resolve())
            parked = runtime.profile_runtime_dir("personal", tool)
            self.assertEqual((parked / "owner.txt").read_text(encoding="utf-8"), tool)

    def test_remove_profile_runtime_removes_only_requested_profile(self):
        runtime.profile_runtime_dir("custom:pm", "claude").mkdir(parents=True)
        runtime.profile_runtime_dir("custom:other", "claude").mkdir(parents=True)

        self.assertTrue(runtime.remove_profile_runtime("custom:pm"))
        self.assertFalse(runtime.profile_runtime_dir("custom:pm", "claude").parent.exists())
        self.assertTrue(runtime.profile_runtime_dir("custom:other", "claude").parent.exists())


if __name__ == "__main__":
    unittest.main()
