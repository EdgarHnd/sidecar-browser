#!/usr/bin/env python3
"""Local, isolated Sidecar component build. No production release/install path."""
import argparse
import datetime
import fcntl
import hashlib
import json
import os
import plistlib
import re
import subprocess
from pathlib import Path

from patches import DEFAULT_CHECKOUT, ROOT, git, validate
from upstream import check

WORK = ROOT.parents[1] / "work"
PATCH = ROOT / "patches/0001-sidecar-development-shell.patch"
STATE = ROOT / "build-state.json"


def update_state(**fields):
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    state.update(fields)
    state["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2) + "\n")
    tmp.replace(STATE)


def normalized_diff(value):
    chunks = value.strip().split("diff --git ")
    return sorted("\n".join(re.sub(r"^(@@ .*? @@).*$", r"\1", line)
                            for line in chunk.splitlines()
                            if not line.startswith("index ")).strip()
                  for chunk in chunks if chunk.strip())


def verify_applied(checkout, lock):
    if git(checkout, "rev-parse", "HEAD") != lock["brave_core_commit"]:
        raise ValueError("Wrong Brave source pin")
    if hashlib.sha256(PATCH.read_bytes()).hexdigest() != lock["patch_sha256"]:
        raise ValueError("Patch checksum changed")
    if git(checkout, "diff", "--cached", "--name-only"):
        raise ValueError("Unexpected staged source changes")
    actual = git(checkout, "diff", "--no-ext-diff", "--no-color", "--src-prefix=a/", "--dst-prefix=b/")
    if normalized_diff(actual) != normalized_diff(PATCH.read_text()):
        raise ValueError("Source changes differ from the reviewed patch")


def run(checkout, *args):
    env = os.environ.copy()
    tool_bin = WORK / "toolchain/node_modules/.bin"
    if not (tool_bin / "node").exists():
        raise ValueError("Local Node 24 toolchain is missing")
    env["PATH"] = str(tool_bin) + os.pathsep + env.get("PATH", "")
    print("Running:", " ".join(args), flush=True)
    subprocess.run(args, cwd=checkout, env=env, check=True)


def app_info(checkout):
    apps = list((checkout.parent / "out/Sidecar").glob("Sidecar Development.app"))
    if len(apps) != 1:
        raise ValueError("Expected Sidecar app was not built")
    app = apps[0]
    with (app / "Contents/Info.plist").open("rb") as file:
        info = plistlib.load(file)
    if info.get("CFBundleIdentifier") != "local.sidecar.browser.development":
        raise ValueError("Unexpected bundle identity; refusing to launch")
    executable = app / "Contents/MacOS" / info["CFBundleExecutable"]
    if not executable.is_file():
        raise ValueError("Built app executable missing")
    return executable


def execute(command, checkout, lock):
    if command in ("bootstrap", "init"):
        if git(checkout, "rev-parse", "HEAD") != lock["brave_core_commit"]:
            raise ValueError("Initialization requires the pinned source commit")
        if git(checkout, "status", "--porcelain", "--untracked-files=no"):
            raise ValueError("Initialization requires clean tracked source")
        update_state(stage="dependency-initialization", native_build="not-run",
                     native_tests="not-run", installed=False, automatic_binary_updates=False)
        run(checkout, "pnpm", "run", "init", "--target_arch=arm64", "--no-history")
        update_state(stage="dependencies-ready")
    if command in ("bootstrap", "apply"):
        validate(checkout, lock, PATCH)
        git(checkout, "apply", str(PATCH))
        update_state(stage="ui-patch-applied")
    if command in ("bootstrap", "build", "test", "launch"):
        verify_applied(checkout, lock)
    if command in ("bootstrap", "build"):
        update_state(stage="native-build", native_build="running", native_tests="not-run",
                     installed=False, automatic_binary_updates=False)
        run(checkout, "pnpm", "run", "build", "Component", "-C", "Sidecar",
            "--target_arch=arm64", "--gn", "symbol_level:1", "--ninja", "j:8")
        app_info(checkout)
        update_state(stage="native-build-complete", native_build="passed",
                     built_core_commit=lock["brave_core_commit"],
                     built_patch_sha256=lock["patch_sha256"])
    if command in ("bootstrap", "test"):
        update_state(stage="native-tests", native_tests="running")
        run(checkout, "pnpm", "run", "test", "brave_unit_tests", "-C", "Sidecar",
            "--filter=VerticalTabControllerUnitTest.*:BraveTabStripLayoutHelperUnitTest.*",
            "--ninja", "j:8")
        update_state(stage="development-build-ready", native_tests="passed")
    if command == "launch":
        state = json.loads(STATE.read_text())
        if (state.get("built_core_commit") != lock["brave_core_commit"]
                or state.get("built_patch_sha256") != lock["patch_sha256"]
                or state.get("native_build") != "passed"
                or state.get("native_tests") != "passed"):
            raise ValueError("Build/test receipt does not match this source")
        if check(lock)["source_status"] != "current":
            raise ValueError("Brave stable has changed; update the development build first")
        executable = app_info(checkout)
        subprocess.Popen([str(executable), "--user-data-dir=" + str(WORK / "sidecar-profile"),
                          "--no-first-run", "--no-default-browser-check", "about:blank"])
        print("Launched Sidecar with its isolated development profile.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["bootstrap", "init", "apply", "build", "test", "launch"])
    parser.add_argument("--checkout", type=Path, default=DEFAULT_CHECKOUT)
    args = parser.parse_args()
    lock = json.loads((ROOT / "upstream-lock.json").read_text())
    WORK.mkdir(exist_ok=True)
    with (WORK / "sidecar-operation.lock").open("w") as operation:
        try:
            fcntl.flock(operation, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit("A Sidecar operation is already running")
        try:
            current = json.loads(STATE.read_text()) if STATE.exists() else {}
            for field in ("error", "failed_during", "command"):
                current.pop(field, None)
            STATE.write_text(json.dumps(current, indent=2) + "\n")
            execute(args.command, args.checkout.resolve(), lock)
        except Exception as error:
            current = json.loads(STATE.read_text()) if STATE.exists() else {}
            fields = {"stage": "failed", "error": str(error),
                      "failed_during": current.get("stage"), "command": args.command}
            for field in ("native_build", "native_tests"):
                if current.get(field) == "running":
                    fields[field] = "failed"
            update_state(**fields)
            raise


if __name__ == "__main__":
    main()
