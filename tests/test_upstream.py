import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import upstream
from upstream import check, resolve_commit, version


class UpstreamTests(unittest.TestCase):
    def setUp(self):
        self.sha = "a" * 40
        self.lock = {"brave_version": "1.98.60", "brave_core_commit": self.sha}

    def api(self, tag="v1.98.60", sha=None, prerelease=False):
        def fetch(url):
            if url.endswith("releases/latest"):
                return {"tag_name": tag, "draft": False, "prerelease": prerelease}
            return {"object": {"type": "commit", "sha": sha or self.sha}}
        return fetch

    def test_current_source_is_not_an_installed_update(self):
        result = check(self.lock, self.api())
        self.assertEqual(result["source_status"], "current")
        self.assertFalse(result["automatic_binary_updates"])

    def test_numeric_version_order(self):
        self.assertEqual(check(self.lock, self.api("v1.100.1"))["source_status"], "update-available")

    def test_retagged_release_is_not_current(self):
        self.assertEqual(check(self.lock, self.api(sha="b" * 40))["source_status"], "pin-mismatch")

    def test_rejects_rollback(self):
        with self.assertRaises(ValueError):
            check(self.lock, self.api("v1.98.59"))

    def test_rejects_prerelease(self):
        with self.assertRaises(ValueError):
            check(self.lock, self.api(prerelease=True))

    def test_rejects_non_version_tags(self):
        for tag in ("nightly", "v1.98.60-beta", "../../other", None):
            with self.assertRaises(ValueError):
                version(tag)

    def test_resolves_annotated_tag(self):
        responses = iter([
            {"object": {"type": "tag", "sha": "b" * 40}},
            {"object": {"type": "commit", "sha": self.sha}},
        ])
        self.assertEqual(resolve_commit("v1.98.60", lambda _: next(responses)), self.sha)

    def test_network_error_cannot_return_current(self):
        def unavailable(_):
            raise OSError("offline")
        with self.assertRaises(OSError):
            check(self.lock, unavailable)

    def test_rejects_invalid_object_id(self):
        with self.assertRaises(ValueError):
            check(self.lock, self.api(sha="bad"))

    def test_fresh_clone_without_build_receipt_keeps_source_result(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "upstream-lock.json").write_text(json.dumps(self.lock))
            output = root / "status.json"
            with patch.object(upstream, "ROOT", root), \
                    patch.object(upstream, "check", return_value={"source_status": "current"}), \
                    patch.object(sys, "argv", ["upstream.py", "--output", str(output)]), \
                    redirect_stdout(io.StringIO()):
                self.assertEqual(upstream.main(), 0)
            status = json.loads(output.read_text())
        self.assertEqual(status["source_status"], "current")
        self.assertEqual(status["artifact_status"], "not-built")


if __name__ == "__main__":
    unittest.main()
