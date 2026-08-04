import unittest
from unittest.mock import patch
import builtins
import contextlib
import importlib.machinery
import importlib.util
import io

import src.dedupe as dedupe
import src.pruner as pruner
import src.setup as setup
import src.skills as skills
import src.symlink as symlink


MANIFEST = {
    "core": [{"name": "core-local"}],
    "optional": [
        {"name": "default-on", "default_enabled": True},
        {"name": "default-off", "default_enabled": False},
        {"name": "global-on", "default_enabled": False},
        {"name": "local-on", "default_enabled": False},
    ],
}


def load_mykit_bin():
    loader = importlib.machinery.SourceFileLoader("mykit_bin_test", "bin/mykit")
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class SkillPolicyTests(unittest.TestCase):
    def test_active_skill_items_include_defaults_and_enabled_scopes(self):
        old_load_state = skills.load_state
        old_load_local_state = skills.load_local_state
        try:
            skills.load_state = lambda: {
                "enabled_optionals": ["global-on"],
                "disabled_optionals": [],
            }
            skills.load_local_state = lambda cwd=None: {
                "enabled_optionals": ["local-on"],
            }

            names = [item["name"] for item in skills.get_active_skill_items(MANIFEST)]

            self.assertEqual(names, ["core-local", "default-on", "global-on", "local-on"])
        finally:
            skills.load_state = old_load_state
            skills.load_local_state = old_load_local_state

    def test_active_skill_items_respect_disabled_defaults(self):
        old_load_state = skills.load_state
        old_load_local_state = skills.load_local_state
        try:
            skills.load_state = lambda: {
                "enabled_optionals": [],
                "disabled_optionals": ["default-on"],
            }
            skills.load_local_state = lambda cwd=None: {"enabled_optionals": []}

            names = [item["name"] for item in skills.get_active_skill_items(MANIFEST)]

            self.assertEqual(names, ["core-local"])
        finally:
            skills.load_state = old_load_state
            skills.load_local_state = old_load_local_state

    def test_active_skill_items_include_all(self):
        names = [item["name"] for item in skills.get_active_skill_items(MANIFEST, include_all=True)]

        self.assertEqual(names, ["core-local", "default-on", "default-off", "global-on", "local-on"])


class SetupSelectionTests(unittest.TestCase):
    def test_empty_selection_keeps_defaults(self):
        selected, action, warnings = setup.parse_setup_selection("", ["a", "b"], {"b"})

        self.assertEqual(selected, {"b"})
        self.assertEqual(action, "next")
        self.assertEqual(warnings, [])

    def test_selection_accepts_numbers_names_all_and_none(self):
        names = ["context7", "github", "memory"]

        self.assertEqual(setup.parse_setup_selection("1,memory", names, set())[0], {"context7", "memory"})
        self.assertEqual(setup.parse_setup_selection("all", names, set())[0], set(names))
        self.assertEqual(setup.parse_setup_selection("none", names, {"github"})[0], set())

    def test_selection_accepts_navigation_actions(self):
        self.assertEqual(setup.parse_setup_selection("b", ["a"], {"a"})[1], "back")
        self.assertEqual(setup.parse_setup_selection("q", ["a"], {"a"})[1], "cancel")

    def test_selection_reports_unknown_tokens(self):
        selected, action, warnings = setup.parse_setup_selection("9,missing", ["a"], set())

        self.assertEqual(selected, set())
        self.assertEqual(action, "next")
        self.assertEqual(warnings, [
            "Ignoring out-of-range selection: 9",
            "Ignoring unknown selection: missing",
        ])

    def test_multiselect_skips_non_tty(self):
        old_stdin = setup.sys.stdin
        old_stdout = setup.sys.stdout

        class NotTty:
            def isatty(self):
                return False

        try:
            setup.sys.stdin = NotTty()
            setup.sys.stdout = NotTty()

            self.assertIsNone(setup.run_multiselect("title", [("a", "")], {"a"}))
        finally:
            setup.sys.stdin = old_stdin
            setup.sys.stdout = old_stdout

    def test_wrap_text_uses_display_width_for_wide_characters(self):
        lines = setup._wrap_text("개인 개발 스택 python react", 12)

        self.assertGreater(len(lines), 1)
        for line in lines:
            self.assertLessEqual(setup._display_width(line), 12)

    def test_setup_profile_keywords_include_common_open_source_stacks(self):
        mykit = load_mykit_bin()
        keywords = mykit.get_setup_profile_keywords({"profiles": {}})

        for keyword in ["go", "rust", "php", "ruby", "csharp", "cpp", "swift", "terraform"]:
            self.assertIn(keyword, keywords)

    def test_custom_profile_name_is_normalized(self):
        mykit = load_mykit_bin()

        self.assertEqual(mykit.normalize_custom_profile_name("Backend API"), "backend-api")
        self.assertEqual(mykit.normalize_custom_profile_name(""), "custom")

    def test_single_selection_keeps_first_matching_item(self):
        mykit = load_mykit_bin()
        old_run_multiselect = mykit.run_multiselect
        old_input = builtins.input
        try:
            mykit.run_multiselect = lambda title, rows, default, single=False, **kwargs: None
            builtins.input = lambda prompt="": "2,1"

            with contextlib.redirect_stdout(io.StringIO()):
                selected, action = mykit.prompt_setup_selection("title", ["a", "b"], {"a"}, single=True)

            self.assertEqual(selected, {"a"})
            self.assertEqual(action, "next")
        finally:
            mykit.run_multiselect = old_run_multiselect
            builtins.input = old_input

    def test_setup_creates_profile_when_none_exists(self):
        mykit = load_mykit_bin()
        saved_state = {}
        seen_titles = []
        responses = iter([
            ({"python"}, "next"),
            (set(), "next"),
            (set(), "next"),
            (set(), "next"),
            (set(), "next"),
            (set(), "next"),
            (set(), "next"),
            (set(), "next"),
            (set(), "next"),
        ])

        class MissingStateFile:
            def exists(self):
                return False

        old_load_manifest = mykit.load_manifest
        old_load_state = mykit.load_state
        old_save_state = mykit.save_state
        old_state_file = mykit.STATE_FILE
        old_prompt_name = mykit.prompt_custom_profile_name
        old_prompt_selection = mykit.prompt_setup_selection
        old_cmd_sync = mykit.cmd_sync
        try:
            mykit.load_manifest = lambda: {
                "optional": [
                    {"name": "ecc-suite", "description": "ECC skills"},
                    {"name": "promptfoo", "description": "Prompt evals"},
                ],
                "global": {"mcp_servers": {"context7": {"enabled": False}}},
            }
            mykit.load_state = lambda: {}
            mykit.save_state = lambda state: saved_state.update(state)
            mykit.STATE_FILE = MissingStateFile()
            mykit.prompt_custom_profile_name = lambda default: "backend-api"

            def prompt_selection(title, items, default, single=False, **kwargs):
                seen_titles.append(title)
                self.assertEqual(single, title == "Profile")
                return next(responses)

            mykit.prompt_setup_selection = prompt_selection
            mykit.cmd_sync = lambda: None

            with contextlib.redirect_stdout(io.StringIO()):
                mykit.cmd_setup()

            self.assertEqual(seen_titles, [
                "Languages and stacks (Languages)",
                "Languages and stacks (Frontend & Web)",
                "Languages and stacks (Backend & Server)",
                "Languages and stacks (Mobile)",
                "Languages and stacks (Databases & ORMs)",
                "Languages and stacks (DevOps & Cloud)",
                "Languages and stacks (AI & Data)",
                "Global optional skills to enable",
                "MCP servers to enable",
            ])
            self.assertEqual(saved_state["active_profile"], "custom:backend-api")
            self.assertEqual(saved_state["custom_profile_name"], "backend-api")
            self.assertEqual(saved_state["profile_keywords"], ["python"])
            self.assertEqual(saved_state["enabled_pruning_packs"], [])
        finally:
            mykit.load_manifest = old_load_manifest
            mykit.load_state = old_load_state
            mykit.save_state = old_save_state
            mykit.STATE_FILE = old_state_file
            mykit.prompt_custom_profile_name = old_prompt_name
            mykit.prompt_setup_selection = old_prompt_selection
            mykit.cmd_sync = old_cmd_sync

    def test_setup_migrates_existing_template_profile_to_user_profile(self):
        mykit = load_mykit_bin()
        saved_state = {}
        seen_titles = []
        responses = iter([
            (set(), "next"),
            (set(), "next"),
            ({"python"}, "next"),
            (set(), "next"),
            (set(), "next"),
            (set(), "next"),
            (set(), "next"),
            (set(), "next"),
            (set(), "next"),
        ])

        class ExistingStateFile:
            def exists(self):
                return True

        old_load_manifest = mykit.load_manifest
        old_load_state = mykit.load_state
        old_save_state = mykit.save_state
        old_state_file = mykit.STATE_FILE
        old_prompt_name = mykit.prompt_custom_profile_name
        old_prompt_selection = mykit.prompt_setup_selection
        old_cmd_sync = mykit.cmd_sync
        try:
            mykit.load_manifest = lambda: {
                "profiles": {"personal": {"description": "Personal", "include": ["python"]}},
                "optional": [{"name": "promptfoo", "description": "Prompt evals"}],
                "global": {"mcp_servers": {"context7": {"enabled": False}}},
            }
            mykit.load_state = lambda: {
                "active_profile": "personal",
                "custom_profile_name": "old-custom",
                "profile_keywords": ["python"],
            }
            mykit.save_state = lambda state: saved_state.update(state)
            mykit.STATE_FILE = ExistingStateFile()
            mykit.prompt_custom_profile_name = lambda default: "personal"

            def prompt_selection(title, items, default, single=False, **kwargs):
                seen_titles.append(title)
                self.assertFalse(single)
                return next(responses)

            mykit.prompt_setup_selection = prompt_selection
            mykit.cmd_sync = lambda: None

            with contextlib.redirect_stdout(io.StringIO()):
                mykit.cmd_setup()

            self.assertEqual(seen_titles, [
                "Languages and stacks (Languages)",
                "Languages and stacks (Frontend & Web)",
                "Languages and stacks (Backend & Server)",
                "Languages and stacks (Mobile)",
                "Languages and stacks (Databases & ORMs)",
                "Languages and stacks (DevOps & Cloud)",
                "Languages and stacks (AI & Data)",
                "Global optional skills to enable",
                "MCP servers to enable",
            ])
            self.assertEqual(saved_state["active_profile"], "custom:personal")
            self.assertEqual(saved_state["custom_profiles"]["personal"]["include"], ["python"])
        finally:
            mykit.load_manifest = old_load_manifest
            mykit.load_state = old_load_state
            mykit.save_state = old_save_state
            mykit.STATE_FILE = old_state_file
            mykit.prompt_custom_profile_name = old_prompt_name
            mykit.prompt_setup_selection = old_prompt_selection
            mykit.cmd_sync = old_cmd_sync

    def test_setup_treats_legacy_custom_profile_as_new_profile(self):
        mykit = load_mykit_bin()
        saved_state = {}
        seen_titles = []
        responses = iter([
            (set(), "next"),
            (set(), "next"),
            ({"python"}, "next"),
            (set(), "next"),
            (set(), "next"),
            (set(), "next"),
            (set(), "next"),
            (set(), "next"),
            (set(), "next"),
        ])

        class ExistingStateFile:
            def exists(self):
                return True

        old_load_manifest = mykit.load_manifest
        old_load_state = mykit.load_state
        old_save_state = mykit.save_state
        old_state_file = mykit.STATE_FILE
        old_prompt_name = mykit.prompt_custom_profile_name
        old_prompt_selection = mykit.prompt_setup_selection
        old_cmd_sync = mykit.cmd_sync
        try:
            mykit.load_manifest = lambda: {
                "optional": [{"name": "promptfoo", "description": "Prompt evals"}],
                "global": {"mcp_servers": {"context7": {"enabled": False}}},
            }
            mykit.load_state = lambda: {"active_profile": "custom"}
            mykit.save_state = lambda state: saved_state.update(state)
            mykit.STATE_FILE = ExistingStateFile()
            mykit.prompt_custom_profile_name = lambda default: "custom"

            def prompt_selection(title, items, default, single=False, **kwargs):
                seen_titles.append(title)
                self.assertEqual(single, title == "Profile")
                return next(responses)

            mykit.prompt_setup_selection = prompt_selection
            mykit.cmd_sync = lambda: None

            with contextlib.redirect_stdout(io.StringIO()):
                mykit.cmd_setup()

            self.assertEqual(seen_titles, [
                "Languages and stacks (Languages)",
                "Languages and stacks (Frontend & Web)",
                "Languages and stacks (Backend & Server)",
                "Languages and stacks (Mobile)",
                "Languages and stacks (Databases & ORMs)",
                "Languages and stacks (DevOps & Cloud)",
                "Languages and stacks (AI & Data)",
                "Global optional skills to enable",
                "MCP servers to enable",
            ])
            self.assertEqual(saved_state["active_profile"], "custom:custom")
            self.assertEqual(saved_state["profile_keywords"], ["python"])
        finally:
            mykit.load_manifest = old_load_manifest
            mykit.load_state = old_load_state
            mykit.save_state = old_save_state
            mykit.STATE_FILE = old_state_file
            mykit.prompt_custom_profile_name = old_prompt_name
            mykit.prompt_setup_selection = old_prompt_selection
            mykit.cmd_sync = old_cmd_sync

    def test_stack_edit_updates_existing_profile(self):
        mykit = load_mykit_bin()
        saved_state = {}

        old_load_manifest = mykit.load_manifest
        old_load_state = mykit.load_state
        old_save_state = mykit.save_state
        old_get_active_profile = mykit.get_active_profile
        old_prompt_name = mykit.prompt_custom_profile_name
        old_prompt_selection = mykit.prompt_setup_selection
        old_cmd_sync = mykit.cmd_sync
        try:
            mykit.load_manifest = lambda: {
                "profiles": {"personal": {"include": ["python", "react"]}},
            }
            mykit.load_state = lambda: {
                "active_profile": "custom:web-server",
                "custom_profiles": {
                    "web-server": {
                        "description": "custom profile 'web-server'",
                        "include": ["python", "react"],
                    }
                },
            }
            mykit.save_state = lambda state: saved_state.update(state)
            mykit.get_active_profile = lambda: "custom:web-server"
            mykit.prompt_custom_profile_name = lambda default: "web-server"
            responses = iter([
                ({"web-server"}, "next"),
                ({"python"}, "next"),
                (set(), "next"),
                ({"fastapi"}, "next"),
                (set(), "next"),
                (set(), "next"),
                (set(), "next"),
                (set(), "next"),
                (set(), "next"),
                (set(), "next"),
            ])

            def prompt_selection(title, items, default, single=False, **kwargs):
                if title == "Profile":
                    self.assertEqual(default, {"web-server"})
                    self.assertIn("add", items)
                    self.assertIn("web-server", items)
                    self.assertTrue(single)
                elif title == "Languages and stacks (Backend & Server)":
                    self.assertFalse(single)
                return next(responses)

            mykit.prompt_setup_selection = prompt_selection
            mykit.cmd_sync = lambda: None

            with contextlib.redirect_stdout(io.StringIO()):
                mykit.cmd_profile(["edit"])

            self.assertEqual(saved_state["custom_profiles"]["web-server"]["include"], ["fastapi", "python"])
        finally:
            mykit.load_manifest = old_load_manifest
            mykit.load_state = old_load_state
            mykit.save_state = old_save_state
            mykit.get_active_profile = old_get_active_profile
            mykit.prompt_custom_profile_name = old_prompt_name
            mykit.prompt_setup_selection = old_prompt_selection
            mykit.cmd_sync = old_cmd_sync

    def test_stack_edit_prints_current_profile_keywords(self):
        mykit = load_mykit_bin()

        old_load_manifest = mykit.load_manifest
        old_load_state = mykit.load_state
        old_save_state = mykit.save_state
        old_get_active_profile = mykit.get_active_profile
        old_prompt_name = mykit.prompt_custom_profile_name
        old_prompt_selection = mykit.prompt_setup_selection
        old_cmd_sync = mykit.cmd_sync
        try:
            mykit.load_manifest = lambda: {
                "profiles": {"personal": {"include": ["python", "react"]}},
            }
            mykit.load_state = lambda: {
                "active_profile": "custom:web-server",
                "custom_profiles": {
                    "web-server": {
                        "description": "custom profile 'web-server'",
                        "include": ["python", "react"],
                    }
                },
            }
            mykit.save_state = lambda state: None
            mykit.get_active_profile = lambda: "custom:web-server"
            mykit.prompt_custom_profile_name = lambda default: "web-server"
            responses = iter([
                ({"web-server"}, "next"),
                ({"python"}, "next"),
                ({"react"}, "next"),
                (set(), "next"),
                (set(), "next"),
                (set(), "next"),
                (set(), "next"),
                (set(), "next"),
                (set(), "next"),
                (set(), "next"),
            ])
            mykit.prompt_setup_selection = lambda title, items, default, single=False, **kwargs: next(responses)
            mykit.cmd_sync = lambda: None

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                mykit.cmd_profile(["edit"])

            text = output.getvalue()
            self.assertIn("mykit initial setup", text)
        finally:
            mykit.load_manifest = old_load_manifest
            mykit.load_state = old_load_state
            mykit.save_state = old_save_state
            mykit.get_active_profile = old_get_active_profile
            mykit.prompt_custom_profile_name = old_prompt_name
            mykit.prompt_setup_selection = old_prompt_selection
            mykit.cmd_sync = old_cmd_sync

    def test_stack_list_shows_custom_profiles(self):
        mykit = load_mykit_bin()

        old_load_manifest = mykit.load_manifest
        old_load_state = mykit.load_state
        old_get_active_profile = mykit.get_active_profile
        try:
            mykit.load_manifest = lambda: {"profiles": {"personal": {"description": "Personal", "include": ["python"]}}}
            mykit.load_state = lambda: {
                "active_profile": "custom:web-server",
                "custom_profiles": {
                    "web-server": {
                        "description": "custom profile 'web-server'",
                        "include": ["react", "typescript"],
                    }
                },
            }
            mykit.get_active_profile = lambda: "custom:web-server"

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                mykit.cmd_profile(["list"])

            text = output.getvalue()
            self.assertIn("Profiles:", text)
            self.assertIn("web-server", text)
            self.assertIn("react, typescript", text)
            self.assertIn("mykit profile use <profile-name>", text)
        finally:
            mykit.load_manifest = old_load_manifest
            mykit.load_state = old_load_state
            mykit.get_active_profile = old_get_active_profile

    def test_profile_remove_deletes_profile(self):
        mykit = load_mykit_bin()
        saved_state = {}

        old_load_manifest = mykit.load_manifest
        old_load_state = mykit.load_state
        old_save_state = mykit.save_state
        old_get_active_profile = mykit.get_active_profile
        old_cmd_sync = mykit.cmd_sync
        try:
            mykit.load_manifest = lambda: {"profiles": {"personal": {"description": "Personal", "include": ["python"]}}}
            mykit.load_state = lambda: {
                "active_profile": "custom:dev",
                "custom_profiles": {
                    "dev": {"description": "dev profile", "include": ["python"]},
                    "prod": {"description": "prod profile", "include": ["java"]},
                },
            }
            mykit.save_state = lambda state: saved_state.update(state)
            mykit.get_active_profile = lambda: "custom:dev"
            mykit.cmd_sync = lambda: None

            with contextlib.redirect_stdout(io.StringIO()):
                mykit.cmd_profile(["remove", "dev", "-y"])

            self.assertNotIn("dev", saved_state["custom_profiles"])
            self.assertIn("prod", saved_state["custom_profiles"])
            self.assertEqual(saved_state["active_profile"], "custom:prod")
        finally:
            mykit.load_manifest = old_load_manifest
            mykit.load_state = old_load_state
            mykit.save_state = old_save_state
            mykit.get_active_profile = old_get_active_profile
            mykit.cmd_sync = old_cmd_sync

    def test_profile_edit_delete_option(self):
        mykit = load_mykit_bin()
        saved_state = {}

        old_load_manifest = mykit.load_manifest
        old_load_state = mykit.load_state
        old_save_state = mykit.save_state
        old_get_active_profile = mykit.get_active_profile
        old_prompt_name = mykit.prompt_custom_profile_name
        old_prompt_selection = mykit.prompt_setup_selection
        old_cmd_sync = mykit.cmd_sync
        try:
            mykit.load_manifest = lambda: {"profiles": {"personal": {"include": ["python"]}}}
            mykit.load_state = lambda: {
                "active_profile": "custom:old_profile",
                "custom_profiles": {
                    "old_profile": {"description": "old", "include": ["python"]},
                    "new_profile": {"description": "new", "include": ["java"]},
                },
            }
            mykit.save_state = lambda state: saved_state.update(state)
            mykit.get_active_profile = lambda: "custom:old_profile"
            mykit.prompt_custom_profile_name = lambda default: "new_profile"

            responses = iter([
                ({"old_profile"}, "delete"),
                ({"new_profile"}, "next"),
                ({"java"}, "next"),
                (set(), "next"),
                (set(), "next"),
                (set(), "next"),
                (set(), "next"),
                (set(), "next"),
                (set(), "next"),
                (set(), "next"),
                (set(), "next"),
            ])
            mykit.prompt_setup_selection = lambda title, items, default, single=False, **kwargs: next(responses)
            mykit.cmd_sync = lambda: None

            with patch("builtins.input", return_value="y"):
                with contextlib.redirect_stdout(io.StringIO()):
                    mykit.cmd_profile(["edit"])

            self.assertNotIn("old_profile", saved_state["custom_profiles"])
            self.assertIn("new_profile", saved_state["custom_profiles"])
        finally:
            mykit.load_manifest = old_load_manifest
            mykit.load_state = old_load_state
            mykit.save_state = old_save_state
            mykit.get_active_profile = old_get_active_profile
            mykit.prompt_custom_profile_name = old_prompt_name
            mykit.prompt_setup_selection = old_prompt_selection
            mykit.cmd_sync = old_cmd_sync


class DedupeScopeTests(unittest.TestCase):
    def test_dedupe_scope_defaults_to_active_skills(self):
        old_load_state = dedupe.load_state
        old_load_local_state = dedupe.load_local_state
        try:
            dedupe.load_state = lambda: {
                "enabled_optionals": ["global-on"],
                "disabled_optionals": ["default-on"],
            }
            dedupe.load_local_state = lambda cwd=None: {
                "enabled_optionals": ["local-on"],
            }

            names = [item["name"] for item in dedupe.get_dedupe_skill_items(MANIFEST)]

            self.assertEqual(names, ["core-local", "global-on", "local-on"])
        finally:
            dedupe.load_state = old_load_state
            dedupe.load_local_state = old_load_local_state


class PrunerTests(unittest.TestCase):
    def test_short_keywords_match_whole_parts_only(self):
        self.assertTrue(pruner.is_skill_relevant("fix-ci", []))
        self.assertFalse(pruner.is_skill_relevant("prefix-helper", []))

    def test_profile_keywords_from_custom_profile_override_named_profile(self):
        old_load_state = pruner.load_state
        try:
            pruner.load_state = lambda: {
                "custom_profiles": {"backend": {"include": ["go"]}},
            }

            self.assertEqual(pruner.get_profile_keywords("custom:backend"), ["go"])
        finally:
            pruner.load_state = old_load_state


class PruningPackPolicyTests(unittest.TestCase):
    def test_prunable_pack_uses_fetched_repo_when_pruning_is_disabled(self):
        old_load_state = symlink.load_state
        try:
            symlink.load_state = lambda: {"enabled_pruning_packs": []}

            path = symlink.resolve_skill_path({
                "name": "ecc-suite",
                "source": "github",
                "path": "~/.agent-skills/store/ecc-pruned-skills",
            })

            self.assertEqual(path, symlink.CACHE_DIR / "fetched" / "ecc-suite")
        finally:
            symlink.load_state = old_load_state

    def test_enabled_pruning_packs_default_to_prunable_packs(self):
        self.assertEqual(symlink.get_enabled_pruning_packs({}), symlink.PRUNABLE_PACKS)


if __name__ == "__main__":
    unittest.main()
