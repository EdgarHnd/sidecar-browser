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
- Sidebar navigation controls and an origin chip that opens Brave's native
  address bar, plus titled pinned-tab rows without a close button.
- A floating **Cmd+T** bar for switching to a matching open tab or opening a
  URL/search in a new tab. Arrow keys select, Return opens, Cmd+Return forces a
  new tab, and Escape or Cmd+W cancels without creating a tab.
- **Cmd+W on the active pinned tab preserves its pin**, selects another tab,
  and unloads the page when safe. Closing the last pin creates a landing tab.
  Ordinary tabs still close normally.
- The native development app compiled and launched; all 38 targeted native
  tests passed on October 26, 2026, along with 22 Python safeguard tests.
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
launches the actual browser.
Do not start a duplicate while it runs. To resume individual completed phases,
use `python3 scripts/develop.py apply`, `python3 scripts/develop.py build`, and
`python3 scripts/develop.py test`. The wrapper verifies
the source/patch before building. Compilation defaults to at most four local
jobs (`SISO_LIMITS=local=4`). Run the wrapper with `nice -n 15` to give other apps
priority. `python3 scripts/develop.py launch` uses a dedicated
development profile and an isolated app identity, and requires a current online source
check. It launches only the development app, never the regular Brave app.

## Arc-inspired direction

The sidebar now contains Back, Forward, Reload, the current origin and New Tab.
Brave's native focus mode hides the top toolbar when appropriate; the sidebar
address chip and Cmd+L reveal the real omnibox and its site-information controls.
The toolbar stays visible for external pages with security warnings.

The command bar currently searches tabs in the current window, then uses the
profile's default search engine or URL classifier. It does not yet show history,
bookmark suggestions, or general browser commands. Spaces and folders remain
future work.

Pin retention currently applies to the active tab's close command (including
Cmd+W). Pages with unload handlers remain loaded to protect unsaved work. Pin
reopening keeps its last URL; resetting to an original pinned URL and broader
bulk/context-menu close behavior remain to be implemented. Unpinning and then
closing still removes a tab normally.

See [the validation record](docs/validation.md) for tested interactions and
remaining compatibility work.

## Imported profile and streaming

At the user's request, the local Sidecar profile was populated from a copy of
their original Brave profile while both apps were closed. The original profile
was not modified. Password and cookie databases stayed encrypted; no secrets or
profile data are stored in this repository. The previous Sidecar profile was
retained as a local backup. Login and Keychain compatibility are not guaranteed.

Netflix playback is unresolved in this development build (reported E100/1044).
The running app registers Widevine 4.10.3112.0 as enabled, and a protected
Bitmovin DASH test stream plays. The same Netflix title works in original Brave.
The build includes Widevine and proprietary codecs, but CDM host verification
is disabled by the upstream development configuration. That is a compatibility
lead, not a confirmed explanation for this Netflix error. Use official Brave
for Netflix while the release/DRM path is investigated.

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
for normal browsing and keep Sidecar's development profile separate.

## Sources and licensing

- [Brave source and build instructions](https://github.com/brave/brave-core/tree/v1.98.60)
- [macOS prerequisites](https://github.com/brave/brave-browser/wiki/macOS-Development-Environment)
- [Build configuration](https://github.com/brave/brave-browser/wiki/Build-configuration)
- [Stable release](https://github.com/brave/brave-browser/releases/tag/v1.98.60)

Brave files and our modifications to them retain MPL-2.0 notices. Chromium and
third-party licenses still apply. This is a local prototype; a distributable
release also needs original branding/assets, license notices, and the required
source availability. Sidecar is not an official Brave or Arc product.
