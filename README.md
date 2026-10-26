# Sidecar — custom Brave development project

Sidecar is a temporary working name for an Arc-inspired personal browser built
from Brave. This is the first development milestone, not a finished browser.

Public source: [EdgarHnd/sidecar-browser](https://github.com/EdgarHnd/sidecar-browser).
GitHub Actions verifies the update/build safeguards and native feed validator.
Those checks do not compile the full browser or certify a distributable release.

## What exists

- Brave stable **1.98.60**, Chromium **156.0.8078.48**, pinned to the exact
  brave-core commit in `upstream-lock.json`.
- A native source patch with a separate macOS development identity, vertical
  tabs on by default, a 260-point sidebar, 36-point tab rows and 6-point gaps.
- Updated existing controller tests for the new default and explicit opt-out.
- A source-release tracker that detects newer releases and retagged commits,
  rejects prereleases/rollback, and reports unknown when the network fails.
- A patch guard that refuses the wrong base, modified source, altered patches
  and unexpected file scope. It never resets a checkout or silently drops edits.
- An integrated native updater feed route targeting signed GitHub Releases.
  The AI schedule was deleted; updates will not depend on Codex.

The source checkout and large build dependencies live in
`../../work/brave-build/src/brave`. Node 24 and pnpm are local to
`../../work/toolchain`; your global toolchain is unchanged. The initialization
log from the initial attempt is `../../work/brave-init.log`. The active
initialization/build runner writes `../../work/sidecar-build.log`; the resumed
build/test/launch runner writes `../../work/sidecar-trial.log`, and
`build-state.json` records its current phase.
The existing Brave application and its profile have not been modified.

## Development commands

Run from this project directory:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/upstream.py
python3 scripts/patches.py
```

`upstream.py` exits 0 for matching source, 1 for an update or changed tag, and 2
for an unknown result. A matching source pin is **not** evidence that an
installed browser is updated, tested, or safe.

`python3 scripts/develop.py bootstrap` performs initialization,
patch application, build and tests in order, stopping on the first failure.
After initialization, `python3 scripts/develop.py trial` builds, tests and
launches the actual browser; this is the currently running operation.
Do not start a duplicate while it runs. To resume individual completed phases,
use `python3 scripts/develop.py apply`, `python3 scripts/develop.py build`, and
`python3 scripts/develop.py test`. The wrapper verifies
the source/patch before building. `python3 scripts/develop.py launch` uses a dedicated
test profile and an isolated app identity, and requires a current online source
check. It launches only the development app, never the regular Brave app.

## Arc-inspired direction

The first patch establishes the native sidebar baseline. It does not yet move
the omnibox, implement Spaces, or provide Arc's command palette.

Next: move navigation and the omnibox into the sidebar, simplify the top
toolbar, refine pinned tabs, then introduce persistent Spaces and a keyboard
command palette. Keep the existing omnibox's origin display, permission
indicators and security interstitials. Reuse Brave's tab model and native Views
components. Do not embed arbitrary sites in an iframe or substitute a WebKit
wrapper for Brave.

## Security update contract

"Always instantly current" is not a guarantee a fork can honestly make.
Each upstream release must be fetched, integrated, built, tested, signed and
installed. Sidecar will use a **built-in native updater** with signed GitHub Releases;
see [native updater notes](native/README.md). The standalone source tracker is
a maintainer/build tool, not a runtime updater. No AI schedule remains.

Before this can replace your daily browser, implement and prove:

1. Automated stable-release detection and immutable source provenance.
2. A candidate build for every stable update; UI conflicts stop promotion.
3. Browser regression tests and manual smoke tests for navigation, profiles,
   permissions, downloads, extensions, tab restoration and renderer isolation.
4. An independently signed/notarized macOS app and signed update feed, using
   our own identity and keys. Never ship updates signed with a key in the repo.
5. Update verification, atomic installation, relaunch and an end-to-end upgrade
   test. Reject wrong identity, altered payloads and unapproved downgrades.
6. A visible stale/unknown state and alerts if a security release cannot ship.

Brave's development configuration already disables its app updater. We have
not disabled sandboxing, TLS verification, or security checks. Official Brave
updates cannot preserve our custom UI; a custom distribution needs its own
update channel. Browser services such as Safe Browsing require independent
configuration and verification before daily use. Do not assume official Brave
service credentials or signing identities are available to this fork.

Read [the implementation notes](docs/architecture.md) for build and update
boundaries. Until the release/update path is operational, use official Brave
for normal browsing and Sidecar only with its separate test profile.

## Sources and licensing

- [Brave source and build instructions](https://github.com/brave/brave-core/tree/v1.98.60)
- [macOS prerequisites](https://github.com/brave/brave-browser/wiki/macOS-Development-Environment)
- [Build configuration](https://github.com/brave/brave-browser/wiki/Build-configuration)
- [Stable release](https://github.com/brave/brave-browser/releases/tag/v1.98.60)

Brave files and our modifications to them retain MPL-2.0 notices. Chromium and
third-party licenses still apply. This is a local prototype; a distributable
release also needs original branding/assets, license notices, and the required
source availability. Sidecar is not an official Brave or Arc product.
