#!/usr/bin/env python3
"""Apply the reviewed UI patch only to the exact, clean Brave source pin."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CHECKOUT = ROOT.parents[1] / "work/brave-build/src/brave"


def git(checkout, *args):
    return subprocess.check_output(["git", "-C", str(checkout), *args], text=True).strip()


def validate(checkout, lock, patch):
    if git(checkout, "rev-parse", "HEAD") != lock["brave_core_commit"]:
        raise ValueError("Source commit differs from the reviewed pin; rebase and review first")
    if git(checkout, "status", "--porcelain", "--untracked-files=no"):
        raise ValueError("Tracked source has changes; preserve/review them before applying")
    if hashlib.sha256(patch.read_bytes()).hexdigest() != lock["patch_sha256"]:
        raise ValueError("Patch checksum differs from the reviewed manifest")
    paths = []
    for line in patch.read_text().splitlines():
        if line.startswith("+++ b/"):
            paths.append(line[6:])
    if sorted(paths) != sorted(lock["patch_files"]):
        raise ValueError("Patch file scope differs from the reviewed manifest")
    git(checkout, "apply", "--check", str(patch))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, default=DEFAULT_CHECKOUT)
    parser.add_argument("--apply", action="store_true", help="Apply after checks; default checks only")
    args = parser.parse_args()
    lock = json.loads((ROOT / "upstream-lock.json").read_text())
    patch = ROOT / "patches/0001-sidecar-development-shell.patch"
    validate(args.checkout, lock, patch)
    if args.apply:
        git(args.checkout, "apply", str(patch))
    print("Patch applied" if args.apply else "Patch checks passed; source unchanged")


if __name__ == "__main__":
    main()
