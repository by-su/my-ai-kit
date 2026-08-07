import contextlib
import io
import unittest

import src.completion as completion


MANIFEST = {
    "optional": [
        {"name": "zeta-pack"},
        {"name": "alpha-pack"},
        {"name": "no-name-entry"},
        {"name": ""},
    ]
}


class CompletionOptionalNamesTests(unittest.TestCase):
    def test_get_optional_skill_names_reads_from_manifest_and_sorts(self):
        names = completion.get_optional_skill_names(MANIFEST)
        self.assertEqual(names, ["alpha-pack", "no-name-entry", "zeta-pack"])

    def test_get_optional_skill_names_falls_back_to_load_manifest(self):
        old_load_manifest = completion.load_manifest
        try:
            completion.load_manifest = lambda: MANIFEST
            names = completion.get_optional_skill_names()
            self.assertEqual(names, ["alpha-pack", "no-name-entry", "zeta-pack"])
        finally:
            completion.load_manifest = old_load_manifest


class CompletionScriptGenerationTests(unittest.TestCase):
    def test_zsh_script_embeds_current_optional_skill_names(self):
        script = completion.build_zsh_completion_script(["alpha-pack", "zeta-pack"])
        self.assertIn('echo "alpha-pack zeta-pack"', script)
        self.assertNotIn("db-helper", script)

    def test_bash_script_embeds_current_optional_skill_names(self):
        script = completion.build_bash_completion_script(["alpha-pack", "zeta-pack"])
        self.assertIn('compgen -W "alpha-pack zeta-pack --all"', script)
        self.assertNotIn("db-helper", script)

    def test_generate_completion_zsh_uses_live_manifest(self):
        old_load_manifest = completion.load_manifest
        try:
            completion.load_manifest = lambda: MANIFEST
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                completion.generate_completion("zsh")
            text = output.getvalue()
            self.assertIn("alpha-pack", text)
            self.assertIn("zeta-pack", text)
        finally:
            completion.load_manifest = old_load_manifest


class InstalledCompletionFilesTests(unittest.TestCase):
    def test_repo_completion_files_match_current_manifest_optional_names(self):
        """Guards against the completion files silently drifting from manifest.yaml again."""
        from src.config import load_manifest, KIT_DIR

        names = completion.get_optional_skill_names(load_manifest())
        names_str = " ".join(names)

        zsh_text = (KIT_DIR / "completions" / "_mykit").read_text(encoding="utf-8")
        bash_text = (KIT_DIR / "completions" / "mykit.bash").read_text(encoding="utf-8")

        self.assertIn(f'echo "{names_str}"', zsh_text)
        self.assertIn(f'compgen -W "{names_str} --all"', bash_text)


if __name__ == "__main__":
    unittest.main()
