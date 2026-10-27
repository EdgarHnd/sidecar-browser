#!/usr/bin/env python3
"""Track Brave stable source. This does not install or certify a browser."""
import argparse
import datetime
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = "https://api.github.com/repos/brave/"


def version(value):
    if not isinstance(value, str) or not re.fullmatch(r"v?\d+\.\d+\.\d+", value):
        raise ValueError("Invalid stable Brave version")
    return tuple(map(int, value.removeprefix("v").split(".")))


def fetch_json(url):
    request = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "Sidecar-local-upstream-tracker/0.1",
    })
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def resolve_commit(tag, fetch=fetch_json):
    version(tag)
    obj = fetch(API + "brave-core/git/ref/tags/" + tag)["object"]
    for _ in range(4):
        sha = obj.get("sha", "")
        if not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise ValueError("Invalid upstream object ID")
        if obj["type"] == "commit":
            return sha
        if obj["type"] != "tag":
            raise ValueError("Release tag does not point to a commit")
        obj = fetch(API + "brave-core/git/tags/" + sha)["object"]
    raise ValueError("Too many nested tags")


def check(lock, fetch=fetch_json):
    release = fetch(API + "brave-browser/releases/latest")
    if release.get("draft") is not False or release.get("prerelease") is not False:
        raise ValueError("Latest release is not a published stable release")
    tag = release["tag_name"]
    latest = version(tag)
    pinned = version(lock["brave_version"])
    if tag != "v" + ".".join(map(str, latest)):
        raise ValueError("Unexpected stable tag format")
    if latest < pinned:
        raise ValueError("Upstream reports an older release than the pin")
    commit = resolve_commit(tag, fetch)
    state = "update-available" if latest > pinned else "current"
    if latest == pinned and commit != lock["brave_core_commit"]:
        state = "pin-mismatch"
    return {
        "source_status": state,
        "pinned_brave": lock["brave_version"],
        "latest_brave": tag.removeprefix("v"),
        "latest_core_commit": commit,
        "release_url": "https://github.com/brave/brave-browser/releases/tag/" + tag,
        "published_at": release.get("published_at"),
        "automatic_binary_updates": False,
        "meaning": "Compares source pins only; does not establish installed browser security.",
    }


def artifact_status():
    # Local build receipts are optional; a fresh clone has none.
    try:
        return json.loads((ROOT / "build-state.json").read_text())
    except FileNotFoundError:
        return "not-built"
    except (OSError, ValueError):
        return "unreadable"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "upstream-status.json")
    args = parser.parse_args()
    try:
        status = check(json.loads((ROOT / "upstream-lock.json").read_text()))
        status["artifact_status"] = artifact_status()
        code = 0 if status["source_status"] == "current" else 1
    except Exception as error:
        status = {"source_status": "unknown", "error": str(error),
                  "automatic_binary_updates": False}
        code = 2
    status["checked_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    # Replace any previous green result even when the network check fails.
    temporary = args.output.with_suffix(".tmp")
    temporary.write_text(json.dumps(status, indent=2) + "\n")
    temporary.replace(args.output)
    print(json.dumps(status, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
