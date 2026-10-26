# Implementation boundaries

## Keep the divergence small

The project owns a reviewed patch series against a stable brave-core commit.
Brave's own package manifest selects Chromium and dependencies. Do not
independently advance Chromium while claiming the result matches Brave stable.
Never resolve an update conflict by quietly deleting a custom patch.

Version pins live outside the large source checkout. Source changes are not
applied until initialization finishes, since upstream synchronization can
replace/stash local changes. The patches cover development branding, UI defaults,
sidebar layout, command handling, native update-feed integration and tests.
No renderer, networking, certificate, sandbox or permission implementation is
patched. This reduces review surface; it does not prove absence of security
bugs.

## Separate identities and data

The development bundle is `local.sidecar.browser.development`, named
`Sidecar Development`. The upstream company's signing team is cleared in this
development branding. Build as Component, with Brave's development channel.
Do not use `--channel release` with this patch: release branding is deliberately
untouched and is not a shippable Sidecar product.

The launcher uses `../../work/sidecar-profile`. At the user's explicit request,
a one-time offline copy of their Brave profile populated that directory,
including encrypted credential databases. The source was never modified;
cache/lock files were excluded and the previous Sidecar profile was backed up.
Profile contents, database files, and credentials must never enter this public
repository. Do not point the app at Brave's live Application Support directory
or register as the default browser during development.
Do not use `--no-sandbox`, ignore TLS
errors, or disable security services to make development navigation work.

## Sidebar and keyboard controls

The native Views sidebar observes the existing tab model. Navigation delegates
to Brave's browser commands, and its origin chip focuses the existing omnibox.
Focus mode retains the full toolbar for external security-warning states.

The command bar owns weak references to its browser and matching tabs, and uses
Chromium's autocomplete classifier for new navigations. It does not render web
content or read browsing databases. Opening/dismissing it alone creates no tab.

The close-command hook checks the active tab's pinned state. A pinned page is
deactivated and, when no unload handler is present, offered to Chromium's tab
lifecycle manager for discarding. The same model entry and pin survive. A last
pin gets a new landing tab, preserving the window. Ordinary close commands
continue through Brave. This does not yet redefine bulk or context-menu closing
or store a separate original URL for a pin.

Widevine and proprietary codecs are compiled in. Host verification is disabled
in the development build. A protected test stream plays, but Netflix E100/1044
remains unresolved; copying a profile does not establish compatibility with
every DRM service or certify a custom browser.

## Release promotion (not implemented yet)

Separate source detection, candidate build, verification and installed status.
Keep a signed release manifest containing upstream Brave/Chromium versions,
commit IDs, custom patch hash, architecture, monotonically increasing build
number, app hash and test attestations. A signed artifact must not be promoted
just because compilation succeeds.

The updater should validate artifact signatures and bundle identity, reject
rollback/replay, stage replacement atomically and record successful relaunch.
The user sees pending/stale/failed rather than a misleading green status when
a candidate exists but has not been installed. A failed UI rebase must trigger
attention rather than silently retaining an old engine indefinitely.

Developer ID signing, notarization, update hosting, signing-key management,
Safe Browsing configuration, crash reporting/privacy choices and release smoke
tests remain open work. No production updater is configured by this milestone.
