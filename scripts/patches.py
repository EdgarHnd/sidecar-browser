#!/usr/bin/env python3
"""Apply the reviewed UI patch only to the exact, clean Brave source pin.

With --export, regenerate the patch series and manifest from a patched checkout.
"""
import argparse
import copy
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"
DEFAULT_CHECKOUT = WORK / "brave-build/src/brave"


def patch_file(item):
    path = (ROOT / item["file"]).resolve()
    if not path.is_relative_to(ROOT / "patches"):
        raise ValueError("Patch must be inside the project patch directory")
    return path


def patch_bundle(lock):
    content = b""
    for item in lock["patches"]:
        data = patch_file(item).read_bytes()
        if hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise ValueError("Patch series checksum mismatch")
        content += data
    if hashlib.sha256(content).hexdigest() != lock["patch_sha256"]:
        raise ValueError("Combined patch checksum mismatch")
    return content


def git(checkout, *args):
    return subprocess.check_output(["git", "-C", str(checkout), *args], text=True).strip()


def patch_paths(checkout, patch):
    # Git's metadata parser includes binary patches, which have no +++ header.
    stats = git(checkout, "apply", "--numstat", "-z", str(patch))
    return [entry.split("\t", 2)[2] for entry in stats.split("\0") if entry]


def validate(checkout, lock, patch):
    if git(checkout, "rev-parse", "HEAD") != lock["brave_core_commit"]:
        raise ValueError("Source commit differs from the reviewed pin; rebase and review first")
    if git(checkout, "status", "--porcelain", "--untracked-files=no"):
        raise ValueError("Tracked source has changes; preserve/review them before applying")
    if hashlib.sha256(patch.read_bytes()).hexdigest() != lock["patch_sha256"]:
        raise ValueError("Patch checksum differs from the reviewed manifest")
    paths = patch_paths(checkout, patch)
    if sorted(paths) != sorted(lock["patch_files"]):
        raise ValueError("Patch file scope differs from the reviewed manifest")
    git(checkout, "apply", "--check", str(patch))


def verify_applied(checkout, lock, content=None):
    if content is None:
        content = patch_bundle(lock)
    if git(checkout, "rev-parse", "HEAD") != lock["brave_core_commit"]:
        raise ValueError("Wrong Brave source pin")
    if hashlib.sha256(content).hexdigest() != lock["patch_sha256"]:
        raise ValueError("Patch checksum changed")
    if git(checkout, "diff", "--cached", "--name-only"):
        raise ValueError("Unexpected staged source changes")
    changed = git(checkout, "diff", "--name-only", "HEAD").splitlines()
    if sorted(changed) != sorted(lock["patch_files"]):
        raise ValueError("Changed source file scope differs from the reviewed patch")
    # Compare file contents, not Git's choice of diff hunk boundaries.
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp).resolve()
        for name in lock["patch_files"]:
            file = (root / name).resolve()
            if not file.is_relative_to(root):
                raise ValueError("Invalid source path in manifest")
            original = subprocess.run(["git", "-C", str(checkout), "show", "HEAD:" + name],
                                      capture_output=True, check=False)
            if original.returncode == 0:
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(original.stdout)
        patch = root / "reviewed.patch"
        patch.write_bytes(content)
        git(root, "apply", str(patch))
        for name in lock["patch_files"]:
            if (root / name).read_bytes() != (checkout / name).read_bytes():
                raise ValueError("Source contents differ from the reviewed patch: " + name)


def export(checkout, lock, assign=()):
    """Return a manifest whose patch series reproduces the checkout's edits.

    Each changed file stays in the patch that already carries it; new files
    must be assigned explicitly. Nothing is written until the result verifies.
    """
    if git(checkout, "rev-parse", "HEAD") != lock["brave_core_commit"]:
        raise ValueError("Wrong Brave source pin")
    if git(checkout, "diff", "--cached", "--name-only"):
        raise ValueError("Unexpected staged source changes")
    owners = {}
    for item in lock["patches"]:
        for name in patch_paths(checkout, patch_file(item)):
            owners[name] = item["file"]
    series = [item["file"] for item in lock["patches"]]
    for name, patch in assign:
        if patch not in series:
            raise ValueError("Unknown patch: " + patch)
        owners[name] = patch
    changed = git(checkout, "diff", "--name-only", "HEAD").splitlines()
    unowned = sorted(set(changed) - owners.keys())
    if unowned:
        raise ValueError("Assign new source files to a patch: " + ", ".join(unowned))
    exported = copy.deepcopy(lock)
    patches = {}
    for item in exported["patches"]:
        files = [name for name in changed if owners[name] == item["file"]]
        if not files:
            raise ValueError("Patch would be empty: " + item["file"])
        data = subprocess.run(["git", "-C", str(checkout), "diff", "--binary", "HEAD", "--", *files],
                              capture_output=True, check=True).stdout
        item["sha256"] = hashlib.sha256(data).hexdigest()
        patches[item["file"]] = data
    content = b"".join(patches[name] for name in series)
    exported["patch_sha256"] = hashlib.sha256(content).hexdigest()
    exported["patch_files"] = sorted(changed)
    verify_applied(checkout, exported, content)
    return exported, patches


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, default=DEFAULT_CHECKOUT)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="Apply after checks; default checks only")
    mode.add_argument("--export", action="store_true",
                      help="Rewrite patches and manifest from the patched checkout")
    parser.add_argument("--assign", nargs=2, action="append", default=[], metavar=("FILE", "PATCH"),
                        help="With --export, put a new source FILE in PATCH (e.g. patches/0003-...)")
    args = parser.parse_args()
    lock = json.loads((ROOT / "upstream-lock.json").read_text())
    if args.export:
        exported, patches = export(args.checkout, lock, args.assign)
        for item in exported["patches"]:
            patch_file(item).write_bytes(patches[item["file"]])
        (ROOT / "upstream-lock.json").write_text(json.dumps(exported, indent=2) + "\n")
        print(f"Exported {len(patches)} patches covering {len(exported['patch_files'])} files")
        return
    with tempfile.TemporaryDirectory() as temp:
        patch = Path(temp) / "sidecar.patch"
        patch.write_bytes(patch_bundle(lock))
        validate(args.checkout, lock, patch)
        if args.apply:
            git(args.checkout, "apply", "--intent-to-add", str(patch))
    print("Patch applied" if args.apply else "Patch checks passed; source unchanged")


if __name__ == "__main__":
    main()
