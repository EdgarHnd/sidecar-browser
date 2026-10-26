# Resume Sidecar

The first native build completed on October 26, 2026. All 33 targeted native
checks pass, and Sidecar launched with its isolated development profile. Three
layout fixtures were updated to account for the custom margins while preserving
their remainder-distribution and nesting-boundary assertions.

Source downloads, the installed Metal toolchain, and compilation outputs are
retained. Check `build-state.json` for live status.

If another interruption occurs, connect power and run from this directory:

```sh
python3 scripts/develop.py trial > ../../work/sidecar-trial.log 2>&1
```

This resumes compilation, runs the native tests, and launches the real custom
browser with its isolated profile if all checks pass. Do not rerun bootstrap
or init against the patched checkout.

Public repository: https://github.com/EdgarHnd/sidecar-browser

Updates are being implemented through the native updater and signed GitHub
Releases. The AI schedule was deleted. Production signing, publishing, and
end-to-end automatic-update validation are not yet configured.
