import base64
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from appcast import make_feed, verify, SPARKLE


class AppcastTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.archive = root / "Sidecar test.zip"
        self.archive.write_bytes(b"Test update payload, not an application")
        private, public, sig = (root / name for name in ("key.pem", "public.der", "sig.bin"))
        for args in (["genpkey", "-algorithm", "ED25519", "-out", str(private)],
                     ["pkey", "-in", str(private), "-pubout", "-outform", "DER", "-out", str(public)],
                     ["pkeyutl", "-sign", "-inkey", str(private), "-rawin", "-in", str(self.archive), "-out", str(sig)]):
            subprocess.run(["openssl", *args], check=True, capture_output=True)
        self.key = base64.b64encode(public.read_bytes()[-32:]).decode()
        self.sig = base64.b64encode(sig.read_bytes()).decode()

    def test_verifies_real_signature_and_rejects_tampering(self):
        verify(self.archive, self.sig, self.key)
        self.archive.write_bytes(b"tampered")
        with self.assertRaises(ValueError):
            verify(self.archive, self.sig, self.key)

    def test_wrong_key_is_rejected(self):
        with self.assertRaises(ValueError):
            verify(self.archive, self.sig, base64.b64encode(bytes(32)).decode())

    def test_feed_metadata_matches_payload(self):
        result = make_feed(self.archive, "example/sidecar", "v1", "156.1.98.61", "156.1.98.60", self.sig)
        enclosure = ET.fromstring(result).find("./channel/item/enclosure")
        self.assertEqual(enclosure.attrib["length"], str(self.archive.stat().st_size))
        self.assertTrue(enclosure.attrib["url"].endswith("Sidecar%20test.zip"))
        self.assertEqual(enclosure.attrib[f"{{{SPARKLE}}}edSignature"], self.sig)

    def test_rollback_and_same_version_are_rejected(self):
        for version in ("156.1.98.59", "156.1.98.60"):
            with self.assertRaises(ValueError):
                make_feed(self.archive, "example/sidecar", "v1", version, "156.1.98.60", self.sig)

    def test_invalid_repository_is_rejected(self):
        with self.assertRaises(ValueError):
            make_feed(self.archive, "https://elsewhere", "v1", "1.2.3", None, self.sig)
