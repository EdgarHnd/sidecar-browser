# Resume Sidecar

The native browser and Arc-style controls built on October 26, 2026. All 38
targeted native checks pass. Three
layout fixtures were updated to account for the custom margins while preserving
their remainder-distribution and nesting-boundary assertions. Five additional
checks cover pinned-tab close behavior. The sidebar and Cmd+T bar also received
native UI smoke checks; see `docs/validation.md`.

The normal development profile is an authorized offline copy of the user's
Brave profile. A separate `work/sidecar-ui-smoke-profile` holds public
example pages used for UI testing. Never point either app at the other's live
profile directory.

Source downloads, the installed Metal toolchain, and compilation outputs are
retained under the project-local `work/` directory. After the local move into
`Dev/`, old paths remain as compatibility links for existing build artifacts.
Keep those links while reusing this build, which can contain absolute paths.
Check `build-state.json` for live status.

If another interruption occurs, connect power and run from this directory:

```sh
nice -n 15 python3 scripts/develop.py trial > work/sidecar-trial.log 2>&1
```

This resumes compilation, runs the native tests, and launches the real custom
browser with its isolated profile if all checks pass. The compiler defaults to
four local jobs so it is less disruptive to foreground apps. Do not rerun bootstrap
or init against the patched checkout.

Public repository: https://github.com/EdgarHnd/sidecar-browser

Updates are being implemented through the native updater and signed GitHub
Releases. The AI schedule was deleted. Production signing, publishing, and
end-to-end automatic-update validation are not yet configured.

Netflix E100/1044 is unresolved despite Widevine being enabled and present.
Do not promise DRM playback based on a successful compile or profile import.
