import json
import os
import tempfile
import unittest
from pathlib import Path

import src.sessions as sessions


class IsPidAliveTests(unittest.TestCase):
    def test_current_process_is_alive(self):
        self.assertTrue(sessions.is_pid_alive(os.getpid()))

    def test_nonexistent_pid_is_not_alive(self):
        self.assertFalse(sessions.is_pid_alive(999999))

    def test_non_int_pid_is_not_alive(self):
        self.assertFalse(sessions.is_pid_alive(None))


class RecordSessionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_sessions_file = sessions.SESSIONS_FILE
        self.old_get_active_profile = sessions.get_active_profile
        sessions.SESSIONS_FILE = Path(self.tmp.name) / "sessions.json"
        sessions.get_active_profile = lambda cwd=None: "custom:typescript"

    def tearDown(self):
        sessions.SESSIONS_FILE = self.old_sessions_file
        sessions.get_active_profile = self.old_get_active_profile
        self.tmp.cleanup()

    def test_record_session_start_writes_profile_pid_and_cwd(self):
        sessions.record_session_start("session-a", 12345, self.tmp.name)

        data = json.loads(sessions.SESSIONS_FILE.read_text(encoding="utf-8"))
        self.assertEqual(data["session-a"]["pid"], 12345)
        self.assertEqual(data["session-a"]["profile"], "custom:typescript")
        self.assertEqual(data["session-a"]["cwd"], str(Path(self.tmp.name).resolve()))
        self.assertIn("started_at", data["session-a"])

    def test_record_session_end_removes_only_target_session(self):
        sessions.record_session_start("session-a", 111, self.tmp.name)
        sessions.record_session_start("session-b", 222, self.tmp.name)

        sessions.record_session_end("session-a")

        data = json.loads(sessions.SESSIONS_FILE.read_text(encoding="utf-8"))
        self.assertNotIn("session-a", data)
        self.assertIn("session-b", data)

    def test_record_session_end_on_missing_session_is_noop(self):
        sessions.record_session_start("session-a", 111, self.tmp.name)

        sessions.record_session_end("does-not-exist")

        data = json.loads(sessions.SESSIONS_FILE.read_text(encoding="utf-8"))
        self.assertIn("session-a", data)


class ListActiveSessionsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_sessions_file = sessions.SESSIONS_FILE
        sessions.SESSIONS_FILE = Path(self.tmp.name) / "sessions.json"

    def tearDown(self):
        sessions.SESSIONS_FILE = self.old_sessions_file
        self.tmp.cleanup()

    def test_prunes_dead_pids_and_keeps_alive_ones(self):
        sessions.save_sessions({
            "alive-session": {"pid": os.getpid(), "profile": "personal", "started_at": "2026-01-01T00:00:00"},
            "dead-session": {"pid": 999999, "profile": "personal", "started_at": "2026-01-01T00:00:00"},
        })

        result = sessions.list_active_sessions()

        self.assertIn("alive-session", result)
        self.assertNotIn("dead-session", result)

    def test_persists_pruned_result_to_disk(self):
        sessions.save_sessions({
            "dead-session": {"pid": 999999, "profile": "personal", "started_at": "2026-01-01T00:00:00"},
        })

        sessions.list_active_sessions()

        data = json.loads(sessions.SESSIONS_FILE.read_text(encoding="utf-8"))
        self.assertEqual(data, {})

    def test_returns_empty_dict_when_no_sessions_file(self):
        self.assertEqual(sessions.list_active_sessions(), {})


class GetSessionsForPathTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_sessions_file = sessions.SESSIONS_FILE
        sessions.SESSIONS_FILE = Path(self.tmp.name) / "sessions.json"
        self.folder_a = str(Path(self.tmp.name) / "a")
        self.folder_a_sub = str(Path(self.tmp.name) / "a" / "sub")
        self.folder_b = str(Path(self.tmp.name) / "b")

    def tearDown(self):
        sessions.SESSIONS_FILE = self.old_sessions_file
        self.tmp.cleanup()

    def test_matches_session_with_identical_cwd(self):
        sessions.save_sessions({
            "s1": {"pid": os.getpid(), "cwd": self.folder_a, "profile": "general", "started_at": "t"},
        })

        matches = sessions.get_sessions_for_path(self.folder_a)

        self.assertIn("s1", matches)

    def test_matches_ancestor_and_descendant_cwd(self):
        sessions.save_sessions({
            "parent": {"pid": os.getpid(), "cwd": self.folder_a, "profile": "general", "started_at": "t"},
            "child": {"pid": os.getpid(), "cwd": self.folder_a_sub, "profile": "pm", "started_at": "t"},
        })

        matches_from_child = sessions.get_sessions_for_path(self.folder_a_sub)
        matches_from_parent = sessions.get_sessions_for_path(self.folder_a)

        self.assertIn("parent", matches_from_child)
        self.assertIn("child", matches_from_parent)

    def test_ignores_unrelated_cwd(self):
        sessions.save_sessions({
            "s1": {"pid": os.getpid(), "cwd": self.folder_a, "profile": "general", "started_at": "t"},
        })

        matches = sessions.get_sessions_for_path(self.folder_b)

        self.assertEqual(matches, {})

    def test_ignores_sessions_missing_cwd(self):
        sessions.save_sessions({
            "legacy": {"pid": os.getpid(), "profile": "general", "started_at": "t"},
        })

        matches = sessions.get_sessions_for_path(self.folder_a)

        self.assertEqual(matches, {})


if __name__ == "__main__":
    unittest.main()
