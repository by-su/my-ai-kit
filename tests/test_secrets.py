import re
import os
import subprocess
import unittest
from pathlib import Path


SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b"),
)


class RepositorySecretScanTests(unittest.TestCase):
    def test_tracked_files_do_not_contain_high_confidence_secrets(self):
        repo_root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=repo_root,
            check=True,
            capture_output=True,
        )

        findings = []
        for raw_path in result.stdout.split(b"\0"):
            if not raw_path:
                continue
            path = repo_root / os.fsdecode(raw_path)
            try:
                content = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for pattern in SECRET_PATTERNS:
                if pattern.search(content):
                    findings.append(f"{path.relative_to(repo_root)} matches {pattern.pattern}")

        self.assertEqual([], findings, "Potential secret(s) found in tracked files:\n" + "\n".join(findings))


if __name__ == "__main__":
    unittest.main()
