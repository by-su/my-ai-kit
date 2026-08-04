import json
import tempfile
import unittest
from pathlib import Path

import src.permissions as permissions


class PatternConverterTests(unittest.TestCase):
    def test_to_claude_pattern_wraps_single_word_command(self):
        self.assertEqual(permissions.to_claude_pattern("git"), "Bash(git:*)")

    def test_to_claude_pattern_wraps_multi_word_command(self):
        self.assertEqual(permissions.to_claude_pattern("npm run build"), "Bash(npm run build:*)")

    def test_to_antigravity_pattern_wraps_single_word_command(self):
        self.assertEqual(permissions.to_antigravity_pattern("git"), "command(git)")

    def test_to_antigravity_pattern_wraps_multi_word_command(self):
        self.assertEqual(permissions.to_antigravity_pattern("npm run build"), "command(npm run build)")


class MergeAllowPatternsTests(unittest.TestCase):
    def test_preserves_unrelated_keys_and_deduplicates_allow(self):
        existing = {
            "permissions": {
                "allow": ["Bash(git:*)"],
                "deny": ["Bash(rm -rf:*)"],
                "ask": ["Bash(curl:*)"],
            },
            "otherSetting": True,
        }

        result = permissions.merge_allow_patterns(existing, ["Bash(git:*)", "Bash(ls:*)"])

        self.assertEqual(result["permissions"]["allow"], ["Bash(git:*)", "Bash(ls:*)"])
        self.assertEqual(result["permissions"]["deny"], ["Bash(rm -rf:*)"])
        self.assertEqual(result["permissions"]["ask"], ["Bash(curl:*)"])
        self.assertTrue(result["otherSetting"])

    def test_does_not_mutate_input_dict(self):
        existing = {"permissions": {"allow": ["Bash(git:*)"]}}

        permissions.merge_allow_patterns(existing, ["Bash(ls:*)"])

        self.assertEqual(existing["permissions"]["allow"], ["Bash(git:*)"])

    def test_creates_permissions_structure_when_missing(self):
        result = permissions.merge_allow_patterns({}, ["Bash(git:*)"])

        self.assertEqual(result["permissions"]["allow"], ["Bash(git:*)"])


class JsonFileHelperTests(unittest.TestCase):
    def test_read_json_file_returns_empty_dict_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing.json"

            self.assertEqual(permissions.read_json_file(path), {})

    def test_write_then_read_json_file_round_trips(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "settings.json"

            permissions.write_json_file(path, {"a": 1})

            self.assertEqual(permissions.read_json_file(path), {"a": 1})


class SyncTargetTests(unittest.TestCase):
    def test_sync_claude_permissions_writes_bash_patterns(self):
        old_path = permissions.CLAUDE_SETTINGS
        with tempfile.TemporaryDirectory() as tmp:
            permissions.CLAUDE_SETTINGS = Path(tmp) / "settings.json"
            try:
                permissions.sync_claude_permissions(["git", "ls"])

                data = json.loads(permissions.CLAUDE_SETTINGS.read_text(encoding="utf-8"))
                self.assertEqual(data["permissions"]["allow"], ["Bash(git:*)", "Bash(ls:*)"])
            finally:
                permissions.CLAUDE_SETTINGS = old_path

    def test_sync_antigravity_permissions_writes_command_patterns(self):
        old_path = permissions.ANTIGRAVITY_SETTINGS
        with tempfile.TemporaryDirectory() as tmp:
            permissions.ANTIGRAVITY_SETTINGS = Path(tmp) / "settings.json"
            try:
                permissions.sync_antigravity_permissions(["git", "ls"])

                data = json.loads(permissions.ANTIGRAVITY_SETTINGS.read_text(encoding="utf-8"))
                self.assertEqual(data["permissions"]["allow"], ["command(git)", "command(ls)"])
            finally:
                permissions.ANTIGRAVITY_SETTINGS = old_path


class NeutralizeConflictingKeysTests(unittest.TestCase):
    def test_comments_out_top_level_duplicate_outside_block(self):
        lines = ['sandbox_mode = "danger-full-access"', "model = \"gpt\""]

        result = permissions.neutralize_conflicting_keys(lines, ("sandbox_mode", "approval_policy"))

        self.assertTrue(result[0].startswith("#"))
        self.assertIn('sandbox_mode = "danger-full-access"', result[0])
        self.assertEqual(result[1], 'model = "gpt"')

    def test_ignores_lines_inside_existing_managed_block(self):
        lines = [
            permissions.CODEX_BEGIN_MARKER,
            'sandbox_mode = "workspace-write"',
            permissions.CODEX_END_MARKER,
        ]

        result = permissions.neutralize_conflicting_keys(lines, ("sandbox_mode", "approval_policy"))

        self.assertEqual(result, lines)


class UpsertManagedBlockTests(unittest.TestCase):
    def test_appends_block_to_fresh_content(self):
        block = f"{permissions.CODEX_BEGIN_MARKER}\nsandbox_mode = \"workspace-write\"\n{permissions.CODEX_END_MARKER}"

        result = permissions.upsert_managed_block("", block)

        self.assertEqual(result.count(permissions.CODEX_BEGIN_MARKER), 1)
        self.assertIn('sandbox_mode = "workspace-write"', result)

    def test_preserves_unrelated_existing_content(self):
        block = f"{permissions.CODEX_BEGIN_MARKER}\nsandbox_mode = \"workspace-write\"\n{permissions.CODEX_END_MARKER}"
        existing = '[other_table]\nfoo = "bar"\n'

        result = permissions.upsert_managed_block(existing, block)

        self.assertIn('[other_table]', result)
        self.assertIn('foo = "bar"', result)
        self.assertIn(permissions.CODEX_BEGIN_MARKER, result)

    def test_replacing_twice_is_idempotent(self):
        block = f"{permissions.CODEX_BEGIN_MARKER}\nsandbox_mode = \"workspace-write\"\n{permissions.CODEX_END_MARKER}"

        first = permissions.upsert_managed_block("", block)
        second = permissions.upsert_managed_block(first, block)

        self.assertEqual(first, second)
        self.assertEqual(second.count(permissions.CODEX_BEGIN_MARKER), 1)


class SyncCodexConfigTests(unittest.TestCase):
    def test_neutralizes_conflicting_key_and_writes_managed_block(self):
        old_path = permissions.CODEX_CONFIG
        with tempfile.TemporaryDirectory() as tmp:
            permissions.CODEX_CONFIG = Path(tmp) / "config.toml"
            permissions.CODEX_CONFIG.write_text(
                '[other_table]\nfoo = "bar"\nsandbox_mode = "danger-full-access"\n',
                encoding="utf-8",
            )
            try:
                permissions.sync_codex_config("workspace-write", "on-request")

                content = permissions.CODEX_CONFIG.read_text(encoding="utf-8")
                live_sandbox_lines = [
                    line for line in content.splitlines()
                    if line.strip().startswith("sandbox_mode =") and not line.strip().startswith("#")
                ]
                self.assertEqual(len(live_sandbox_lines), 1)
                self.assertIn('sandbox_mode = "workspace-write"', content)
                self.assertIn('[other_table]', content)
                self.assertIn('foo = "bar"', content)
            finally:
                permissions.CODEX_CONFIG = old_path


class SyncAutoApprovePermissionsTests(unittest.TestCase):
    def test_uses_manifest_commands_and_codex_policy(self):
        old_load_manifest = permissions.load_manifest
        old_claude = permissions.CLAUDE_SETTINGS
        old_antigravity = permissions.ANTIGRAVITY_SETTINGS
        old_codex = permissions.CODEX_CONFIG
        with tempfile.TemporaryDirectory() as tmp:
            permissions.load_manifest = lambda: {
                "auto_approve_commands": ["git"],
                "global": {"codex": {"sandbox_mode": "workspace-write", "approval_policy": "never"}},
            }
            permissions.CLAUDE_SETTINGS = Path(tmp) / "claude.json"
            permissions.ANTIGRAVITY_SETTINGS = Path(tmp) / "antigravity.json"
            permissions.CODEX_CONFIG = Path(tmp) / "config.toml"
            try:
                results = permissions.sync_auto_approve_permissions()

                self.assertTrue(len(results) >= 3)
                claude_data = json.loads(permissions.CLAUDE_SETTINGS.read_text(encoding="utf-8"))
                self.assertEqual(claude_data["permissions"]["allow"], ["Bash(git:*)"])
                self.assertIn('approval_policy = "never"', permissions.CODEX_CONFIG.read_text(encoding="utf-8"))
            finally:
                permissions.load_manifest = old_load_manifest
                permissions.CLAUDE_SETTINGS = old_claude
                permissions.ANTIGRAVITY_SETTINGS = old_antigravity
                permissions.CODEX_CONFIG = old_codex


class MergeHookEntriesTests(unittest.TestCase):
    def test_adds_hook_entry_to_empty_settings(self):
        result = permissions.merge_hook_entries({}, "SessionStart", "mykit session-hook start")

        self.assertEqual(
            result["hooks"]["SessionStart"][0]["hooks"][0]["command"],
            "mykit session-hook start",
        )

    def test_does_not_duplicate_existing_command(self):
        existing = {
            "hooks": {
                "SessionStart": [
                    {"matcher": "", "hooks": [{"type": "command", "command": "mykit session-hook start", "timeout": 5}]}
                ]
            }
        }

        result = permissions.merge_hook_entries(existing, "SessionStart", "mykit session-hook start")

        self.assertEqual(len(result["hooks"]["SessionStart"]), 1)

    def test_preserves_unrelated_hook_events_and_keys(self):
        existing = {
            "hooks": {"Stop": [{"matcher": "", "hooks": [{"type": "command", "command": "some-other-hook"}]}]},
            "otherSetting": True,
        }

        result = permissions.merge_hook_entries(existing, "SessionEnd", "mykit session-hook end")

        self.assertEqual(result["hooks"]["Stop"][0]["hooks"][0]["command"], "some-other-hook")
        self.assertTrue(result["otherSetting"])
        self.assertEqual(result["hooks"]["SessionEnd"][0]["hooks"][0]["command"], "mykit session-hook end")

    def test_does_not_mutate_input_dict(self):
        existing = {"hooks": {"SessionStart": []}}

        permissions.merge_hook_entries(existing, "SessionStart", "mykit session-hook start")

        self.assertEqual(existing["hooks"]["SessionStart"], [])


class SyncSessionHooksTests(unittest.TestCase):
    def test_writes_session_start_and_end_hooks_without_clobbering_permissions(self):
        old_path = permissions.CLAUDE_SETTINGS
        with tempfile.TemporaryDirectory() as tmp:
            permissions.CLAUDE_SETTINGS = Path(tmp) / "settings.json"
            permissions.write_json_file(permissions.CLAUDE_SETTINGS, {"permissions": {"allow": ["Bash(git:*)"]}})
            try:
                permissions.sync_session_hooks()

                data = json.loads(permissions.CLAUDE_SETTINGS.read_text(encoding="utf-8"))
                self.assertEqual(data["permissions"]["allow"], ["Bash(git:*)"])
                self.assertEqual(
                    data["hooks"]["SessionStart"][0]["hooks"][0]["command"],
                    permissions.SESSION_HOOK_START_CMD,
                )
                self.assertEqual(
                    data["hooks"]["SessionEnd"][0]["hooks"][0]["command"],
                    permissions.SESSION_HOOK_END_CMD,
                )
            finally:
                permissions.CLAUDE_SETTINGS = old_path

    def test_running_twice_does_not_duplicate_hooks(self):
        old_path = permissions.CLAUDE_SETTINGS
        with tempfile.TemporaryDirectory() as tmp:
            permissions.CLAUDE_SETTINGS = Path(tmp) / "settings.json"
            try:
                permissions.sync_session_hooks()
                permissions.sync_session_hooks()

                data = json.loads(permissions.CLAUDE_SETTINGS.read_text(encoding="utf-8"))
                self.assertEqual(len(data["hooks"]["SessionStart"]), 1)
                self.assertEqual(len(data["hooks"]["SessionEnd"]), 1)
            finally:
                permissions.CLAUDE_SETTINGS = old_path


if __name__ == "__main__":
    unittest.main()
