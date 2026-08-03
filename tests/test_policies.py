import unittest
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
            mykit.run_multiselect = lambda title, rows, default, single=False: None
            builtins.input = lambda prompt="": "2,1"

            with contextlib.redirect_stdout(io.StringIO()):
                selected, action = mykit.prompt_setup_selection("title", ["a", "b"], {"a"}, single=True)

            self.assertEqual(selected, {"a"})
            self.assertEqual(action, "next")
        finally:
            mykit.run_multiselect = old_run_multiselect
            builtins.input = old_input

    def test_setup_creates_custom_profile_from_profile_screen(self):
        mykit = load_mykit_bin()
        saved_state = {}
        seen_titles = []
        responses = iter([
            ({"custom"}, "next"),
            ({"python"}, "next"),
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

            def prompt_selection(title, items, default, single=False):
                seen_titles.append(title)
                self.assertEqual(single, title == "Profile")
                return next(responses)

            mykit.prompt_setup_selection = prompt_selection
            mykit.cmd_sync = lambda: None

            with contextlib.redirect_stdout(io.StringIO()):
                mykit.cmd_setup()

            self.assertEqual(seen_titles, [
                "Profile",
                "Languages and stacks for pruning",
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

    def test_setup_keeps_existing_preset_profile(self):
        mykit = load_mykit_bin()
        saved_state = {}
        seen_titles = []
        responses = iter([
            ({"personal"}, "next"),
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
            mykit.load_state = lambda: {
                "active_profile": "personal",
                "custom_profile_name": "old-custom",
                "profile_keywords": ["python"],
            }
            mykit.save_state = lambda state: saved_state.update(state)
            mykit.STATE_FILE = ExistingStateFile()
            mykit.prompt_custom_profile_name = lambda default: self.fail("preset setup should not prompt for custom profile name")

            def prompt_selection(title, items, default, single=False):
                seen_titles.append(title)
                self.assertEqual(single, title == "Profile")
                return next(responses)

            mykit.prompt_setup_selection = prompt_selection
            mykit.cmd_sync = lambda: None

            with contextlib.redirect_stdout(io.StringIO()):
                mykit.cmd_setup()

            self.assertEqual(seen_titles, [
                "Profile",
                "Global optional skills to enable",
                "MCP servers to enable",
            ])
            self.assertEqual(saved_state["active_profile"], "personal")
            self.assertNotIn("custom_profile_name", saved_state)
            self.assertNotIn("profile_keywords", saved_state)
        finally:
            mykit.load_manifest = old_load_manifest
            mykit.load_state = old_load_state
            mykit.save_state = old_save_state
            mykit.STATE_FILE = old_state_file
            mykit.prompt_custom_profile_name = old_prompt_name
            mykit.prompt_setup_selection = old_prompt_selection
            mykit.cmd_sync = old_cmd_sync

    def test_setup_treats_legacy_custom_profile_as_custom(self):
        mykit = load_mykit_bin()
        saved_state = {}
        seen_titles = []
        responses = iter([
            ({"custom"}, "next"),
            ({"python"}, "next"),
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

            def prompt_selection(title, items, default, single=False):
                seen_titles.append(title)
                self.assertEqual(single, title == "Profile")
                return next(responses)

            mykit.prompt_setup_selection = prompt_selection
            mykit.cmd_sync = lambda: None

            with contextlib.redirect_stdout(io.StringIO()):
                mykit.cmd_setup()

            self.assertEqual(seen_titles, [
                "Profile",
                "Languages and stacks for pruning",
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

    def test_profile_keywords_from_setup_state_override_named_profile(self):
        old_load_state = pruner.load_state
        try:
            pruner.load_state = lambda: {"profile_keywords": ["go"]}

            self.assertEqual(pruner.get_profile_keywords("personal"), ["go"])
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
