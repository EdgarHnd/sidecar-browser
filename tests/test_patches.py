import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from patches import git, validate
from develop import verify_applied, normalized_diff


class PatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        git(self.root, "init", "-q")
        (self.root / "shell.txt").write_text("old\n")
        git(self.root, "add", "shell.txt")
        git(self.root, "-c", "user.name=Test", "-c", "user.email=test@localhost",
            "-c", "commit.gpgsign=false", "commit", "-qm", "fixture")
        self.patch = self.root / "change.patch"
        self.patch.write_text("diff --git a/shell.txt b/shell.txt\n"
                              "--- a/shell.txt\n+++ b/shell.txt\n"
                              "@@ -1 +1 @@\n-old\n+new\n")
        self.lock = {"brave_core_commit": git(self.root, "rev-parse", "HEAD"),
                     "patch_sha256": hashlib.sha256(self.patch.read_bytes()).hexdigest(),
                     "patch_files": ["shell.txt"]}

    def test_validates_without_modifying_source(self):
        validate(self.root, self.lock, self.patch)
        self.assertEqual((self.root / "shell.txt").read_text(), "old\n")

    def test_build_guard_accepts_exact_patch(self):
        git(self.root, "apply", str(self.patch))
        with patch("develop.PATCH", self.patch):
            verify_applied(self.root, self.lock)

    def test_build_guard_ignores_only_git_function_labels(self):
        raw = self.patch.read_text()
        with_label = raw.replace("@@ -1 +1 @@", "@@ -1 +1 @@ void Function() {")
        self.assertEqual(normalized_diff(raw), normalized_diff(with_label))
        self.assertNotEqual(normalized_diff(raw), normalized_diff(raw.replace("+new", "+other")))

    def test_build_guard_rejects_extra_edit_after_application(self):
        git(self.root, "apply", str(self.patch))
        (self.root / "shell.txt").write_text("new\nunreviewed edit\n")
        with patch("develop.PATCH", self.patch), self.assertRaises(ValueError):
            verify_applied(self.root, self.lock)

    def test_rejects_different_base(self):
        self.lock["brave_core_commit"] = "0" * 40
        with self.assertRaises(ValueError):
            validate(self.root, self.lock, self.patch)

    def test_preserves_local_changes(self):
        (self.root / "shell.txt").write_text("user edit\n")
        with self.assertRaises(ValueError):
            validate(self.root, self.lock, self.patch)
        self.assertEqual((self.root / "shell.txt").read_text(), "user edit\n")

    def test_rejects_tampered_patch(self):
        self.patch.write_text(self.patch.read_text().replace("+new", "+other"))
        with self.assertRaises(ValueError):
            validate(self.root, self.lock, self.patch)

    def test_rejects_unreviewed_file_scope(self):
        self.lock["patch_files"] = ["other.txt"]
        with self.assertRaises(ValueError):
            validate(self.root, self.lock, self.patch)

    def test_conflict_cannot_partially_apply(self):
        self.patch.write_text(self.patch.read_text().replace("-old", "-missing"))
        self.lock["patch_sha256"] = hashlib.sha256(self.patch.read_bytes()).hexdigest()
        with self.assertRaises(subprocess.CalledProcessError):
            validate(self.root, self.lock, self.patch)
        self.assertEqual((self.root / "shell.txt").read_text(), "old\n")
