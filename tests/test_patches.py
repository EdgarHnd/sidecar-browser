import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))
import patches
from patches import git, validate
from develop import verify_applied


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
        verify_applied(self.root, self.lock, self.patch.read_bytes())

    def test_build_guard_rejects_extra_edit_after_application(self):
        git(self.root, "apply", str(self.patch))
        (self.root / "shell.txt").write_text("new\nunreviewed edit\n")
        with self.assertRaises(ValueError):
            verify_applied(self.root, self.lock, self.patch.read_bytes())

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

    def test_binary_patch_scope_and_applied_content_are_verified(self):
        icon = self.root / "app icon.bin"
        original = bytes(range(256))
        replacement = b"new-icon\0" + original[::-1]
        icon.write_bytes(original)
        git(self.root, "add", icon.name)
        git(self.root, "-c", "user.name=Test", "-c", "user.email=test@localhost",
            "-c", "commit.gpgsign=false", "commit", "-qm", "binary fixture")
        self.lock["brave_core_commit"] = git(self.root, "rev-parse", "HEAD")
        icon.write_bytes(replacement)
        binary_patch = subprocess.check_output(
            ["git", "-C", str(self.root), "diff", "--binary", "HEAD", "--", icon.name])
        self.patch.write_bytes(self.patch.read_bytes() + binary_patch)
        icon.write_bytes(original)
        self.lock["patch_sha256"] = hashlib.sha256(self.patch.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError, "file scope"):
            validate(self.root, self.lock, self.patch)
        self.lock["patch_files"].append(icon.name)
        validate(self.root, self.lock, self.patch)
        self.assertEqual(icon.read_bytes(), original)
        git(self.root, "apply", str(self.patch))
        self.assertEqual(icon.read_bytes(), replacement)
        verify_applied(self.root, self.lock, self.patch.read_bytes())
        icon.write_bytes(replacement + b"tampered")
        with self.assertRaisesRegex(ValueError, "Source contents"):
            verify_applied(self.root, self.lock, self.patch.read_bytes())

    def test_export_rewrites_series_and_requires_new_files_to_be_assigned(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp).resolve()
            (project / "patches").mkdir()
            name = "patches/0001-shell.patch"
            (project / name).write_bytes(self.patch.read_bytes())
            lock = dict(self.lock, patches=[{"file": name, "sha256": self.lock["patch_sha256"]}])
            git(self.root, "apply", str(self.patch))
            (self.root / "shell.txt").write_text("newer\n")
            (self.root / "added.txt").write_text("added\n")
            git(self.root, "add", "--intent-to-add", "added.txt")
            with mock.patch.object(patches, "ROOT", project):
                with self.assertRaisesRegex(ValueError, "added.txt"):
                    patches.export(self.root, lock)
                exported, data = patches.export(self.root, lock, [("added.txt", name)])
                self.assertEqual(lock["patch_files"], ["shell.txt"])
                self.assertEqual(exported["patch_files"], ["added.txt", "shell.txt"])
                (project / name).write_bytes(data[name])
                verify_applied(self.root, exported)

    def test_native_feed_header_matches_shipped_patch(self):
        # CI compiles native/; the browser builds the copy inside patch 0002.
        name = "browser/mac/sidecar_update_feed.h"
        git(self.root, "apply", "--include=" + name,
            str(PROJECT / "patches/0002-native-update-feed.patch"))
        self.assertEqual((self.root / name).read_bytes(),
                         (PROJECT / "native/sidecar_update_feed.h").read_bytes())
