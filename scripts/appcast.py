#!/usr/bin/env python3
"""Create a GitHub Releases appcast only after verifying its Ed25519 signature.

This is a release-builder tool, not an AI monitor or a browser runtime service.
It never reads private keys, signs an archive, uploads, or installs anything.
"""
import argparse
import base64
import datetime
import json
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote

SPARKLE = "http://www.andymatuschak.org/xml-namespaces/sparkle"
ET.register_namespace("sparkle", SPARKLE)


def checked_version(value):
    if not re.fullmatch(r"\d+(?:\.\d+){1,4}", value):
        raise ValueError("Version must contain two to five numeric components")
    parts = tuple(map(int, value.split(".")))
    return parts + (0,) * (5 - len(parts))


def decode(value, size):
    data = base64.b64decode(value, validate=True)
    if len(data) != size:
        raise ValueError("Invalid Ed25519 key/signature size")
    return data


def verify(archive, signature, public_key):
    key = decode(public_key, 32)
    sig = decode(signature, 64)
    # RFC 8410 SubjectPublicKeyInfo prefix for a raw Ed25519 public key.
    der = bytes.fromhex("302a300506032b6570032100") + key
    with tempfile.TemporaryDirectory() as temp:
        public = Path(temp) / "public.der"
        signature_file = Path(temp) / "signature.bin"
        public.write_bytes(der)
        signature_file.write_bytes(sig)
        result = subprocess.run([
            "openssl", "pkeyutl", "-verify", "-pubin", "-keyform", "DER",
            "-inkey", str(public), "-rawin", "-in", str(archive),
            "-sigfile", str(signature_file),
        ], capture_output=True, text=True)
        if result.returncode != 0:
            raise ValueError("Archive signature verification failed")


def make_feed(archive, repository, tag, version, previous, signature):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Expected a GitHub owner/repository")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", tag):
        raise ValueError("Invalid release tag")
    current = checked_version(version)
    if previous and current <= checked_version(previous):
        raise ValueError("Release version must increase")
    decode(signature, 64)
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "Sidecar updates"
    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = "Sidecar " + version
    ET.SubElement(item, "pubDate").text = datetime.datetime.now(
        datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    ET.SubElement(item, "enclosure", {
        "url": f"https://github.com/{repository}/releases/download/{tag}/{quote(archive.name)}",
        "length": str(archive.stat().st_size),
        "type": "application/octet-stream",
        f"{{{SPARKLE}}}version": version,
        f"{{{SPARKLE}}}shortVersionString": version,
        f"{{{SPARKLE}}}edSignature": signature,
        f"{{{SPARKLE}}}os": "macos",
    })
    ET.indent(rss)
    return ET.tostring(rss, encoding="utf-8", xml_declaration=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--version", required=True, help="Must match the packaged app's CFBundleVersion")
    parser.add_argument("--previous-version")
    parser.add_argument("--signature", required=True, help="Public base64 signature; never a private key")
    parser.add_argument("--public-key", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    verify(args.archive, args.signature, args.public_key)
    feed = make_feed(args.archive, args.repository, args.tag, args.version,
                     args.previous_version, args.signature)
    args.output.write_bytes(feed)
    print(json.dumps({"appcast": str(args.output), "signature_verified": True,
                      "published": False}))


if __name__ == "__main__":
    main()
