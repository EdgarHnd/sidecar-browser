# Local development validation — October 26, 2026

Base: Brave 1.98.60, Chromium 156.0.8078.48, Apple Silicon component build.
The manifest binds all three patches to the pinned upstream source.

## Automated checks

- Native application compilation succeeded incrementally.
- 38 targeted native unit tests passed: 33 vertical-tab controller/layout tests
  and five pinned-tab close tests (empty window, ordinary tab, another tab,
  last pin, repeated closing).
- 22 Python safeguards passed, covering source tracking, patch verification,
  update metadata/signatures and rollback rejection.

These are targeted checks, not the complete Chromium test suite or release
certification. Component test binaries emit upstream duplicate Objective-C
class warnings; the selected tests completed successfully.

## Native UI checks

Using an isolated profile with public Example Domain and Wikipedia pages:

- Cmd+T opens the native floating bar without creating a tab.
- Entering a URL opens it in a new tab.
- A matching title switches to an existing tab, including a pin.
- Escape dismisses the bar without creating a tab.
- Cmd+W dismisses an open command bar without closing its underlying tab
  (verified tab and pin counts unchanged).
- A pinned tab displays its title with no close button.
- Cmd+W on a pin preserves it and selects another tab.
- Cmd+W on an ordinary tab closes it.
- Cmd+W on the only remaining pin creates a landing tab and keeps the window.
- The command bar sizes itself to its results instead of leaving a large blank
  panel below them.
- The sidebar origin chip focuses and selects the existing native omnibox.
- The launcher detaches the app process and its log from the invoking terminal.
  The imported session was restored with all ten pins after a launcher-session
  interruption; the corrected launcher remains running after the command ends.

## Remaining work

Spaces, folders, original pinned-URL reset, history/bookmark suggestions, and
broader bulk/context-menu pin retention are not implemented. A page with an
unload handler stays loaded when its pin is closed to avoid silent data loss.

Netflix E100/1044 was reported in the imported profile; the user confirmed the
same title works in original Brave. The running browser's media diagnostics
register Widevine 4.10.3112.0 as enabled with Software Secure robustness, and
codec/Widevine build flags are enabled. The public Bitmovin DRM demo detected
Widevine/EME support, and its protected DASH stream played with elapsed time
advancing to 17 seconds. Playback was muted, stopped, and the test tab closed.
This proves basic DRM playback, not Netflix's acceptance of the browser.
CDM host
verification is disabled in the upstream development configuration. Netflix
compatibility and the specific failure cause are unverified. No DRM or browser
security checks were bypassed.

References: [Brave's DRM documentation](https://support.brave.com/hc/en-us/articles/360023851591-How-do-I-view-DRM-protected-content),
[Bitmovin's DRM test](https://bitmovin.com/demos/drm), and
[Chromium Embedded Framework's host-verification requirements](https://github.com/chromiumembedded/cef/issues/3404).

Signed/notarized release packaging and a working end-to-end built-in updater
remain separate release gates. The public repository CI does not compile the
full browser.

## October 27 — shell polish

The native app rebuilt successfully after relocation into Dev. All 39 targeted
native tests passed: the previous 38 plus a check that the one-time quiet-shell
setup preserves later user customizations. All 22 Python safeguard tests passed.
The applied source was verified against the exact patch bundle.

The separate UI test profile confirmed:

- Quiet landing page, compact icon navigation, and a bottom New Tab action.
- Expanded sidebar occupies its own width; the page is no longer underneath it.
- Startup and blank tabs opened from Cmd+T do not focus the hidden omnibox.
- The sidebar address chip still focuses the native omnibox.
- Cmd+T rows show favicons, titles, domains, pin status, and distinct actions.
- Most recently used tabs appear first; title filtering switches to a pin.
- Cmd+W retains a pin and selects another tab; Cmd+W inside the palette cancels
  without changing the tab list.
- Settings and the version page load through the native navigation controls.

External-page verification in the fresh test profile was blocked waiting for
macOS Keychain access. A process sample showed cookie encryption initialization
waiting in SecItemCopyMatching; a separate HTTPS connectivity check succeeded.
The protected system prompt requires the user. Encryption and Keychain access
controls were not bypassed. Diagnostics remain local in the ignored work folder.

The final build was reopened with the existing Sidecar profile. The temporary
blank tab used for the final focus check was closed afterward.

Both the outer native build and nested Rust compilation default to four jobs.
