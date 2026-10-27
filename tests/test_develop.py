import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import develop


class DevelopmentLaunchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.lock = {"brave_core_commit": "tested-core", "patch_sha256": "tested-patch"}
        self.state = self.root / "build-state.json"
        self.state.write_text(json.dumps({
            "built_core_commit": "tested-core",
            "built_patch_sha256": "tested-patch",
            "native_build": "passed",
            "native_tests": "passed",
        }))
        for name, value in (("WORK", self.root), ("STATE", self.state)):
            context = patch.object(develop, name, value)
            context.start()
            self.addCleanup(context.stop)

    @patch.object(develop, "subprocess")
    @patch.object(develop, "app_info")
    @patch.object(develop, "check", return_value={"source_status": "current"})
    @patch.object(develop, "verify_applied")
    def test_launch_resumes_existing_profile_without_requesting_blank_page(
            self, verify, check, app_info, subprocess):
        app_info.return_value = self.root / "Sidecar.app/Contents/MacOS/Sidecar"
        develop.execute("launch", self.root / "checkout", self.lock)
        command = subprocess.run.call_args.args[0]
        self.assertEqual(command[:3], ["/usr/bin/open", "-n", "-a"])
        self.assertIn("--user-data-dir=" + str(self.root / "sidecar-profile"), command)
        self.assertIn("--restore-last-session", command)
        self.assertFalse(any(arg.startswith(("chrome://", "brave://", "http://", "https://"))
                             for arg in command))

    @patch.object(develop, "subprocess")
    @patch.object(develop, "check", return_value={"source_status": "changed"})
    @patch.object(develop, "verify_applied")
    def test_session_restore_keeps_upstream_version_guard(self, verify, check, subprocess):
        with self.assertRaisesRegex(ValueError, "Brave stable has changed"):
            develop.execute("launch", self.root / "checkout", self.lock)
        subprocess.run.assert_not_called()
