# Implementation boundaries

## Keep the divergence small

The project owns a reviewed patch series against a stable brave-core commit.
Brave's own package manifest selects Chromium and dependencies. Do not
independently advance Chromium while claiming the result matches Brave stable.
Never resolve an update conflict by quietly deleting a custom patch.

Version pins live outside the large source checkout. Source changes are not
applied until initialization finishes, since upstream synchronization can
replace/stash local changes. The current patch only touches development
branding, UI defaults, tab layout constants and corresponding controller tests.
No renderer, networking, certificate, sandbox or permission implementation is
patched. This reduces review surface; it does not prove absence of security
bugs.

## Separate identities and data

The development bundle is `local.sidecar.browser.development`, named
`Sidecar Development`. The upstream company's signing team is cleared in this
development branding. Build as Component, with Brave's development channel.
Do not use `--channel release` with this patch: release branding is deliberately
untouched and is not a shippable Sidecar product.

The launcher uses `../../work/sidecar-profile`. Do not point it at Brave's
Application Support directory, copy passwords/cookies, or register as the
default browser during development. Do not use `--no-sandbox`, ignore TLS
errors, or disable security services to make development navigation work.

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
