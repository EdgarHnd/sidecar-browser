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

## October 27 — Keychain recovery

After the earlier stalled request, the application log recorded macOS Keychain
error -60008 and a subsequent development-build assertion in BookmarkCounter.
Neither Sidecar nor SecurityAgent was running when the user reported no prompt.
Launching the same build through macOS LaunchServices restored public-page
navigation without needing a visible approval prompt. Example Domain loaded
successfully; Wikipedia also loaded through the updated guarded launcher. Test
tabs/windows were closed afterward. This identifies a working recovery, not a proven root cause of
the original Keychain authorization failure or the later counter assertion.

The development launcher now uses LaunchServices with the existing profile,
source-version guard, and build/test receipt checks intact. Per-launch logs
remain local and ignored. No Keychain permissions or encryption settings changed.


## October 27 — Favorites

The native application compiled with the Favorites model and icon grid. All
49 targeted native tests passed (the previous 39 plus ten Favorites tests),
and all 22 Python safeguards passed. GN header dependency checks passed for
the Favorites model, grid, and unit-test target. The source/build/test receipts
match the final patch bundle.

The separate UI profile confirmed:

- Add a website using the Favorites **+** or the Cmd+T **favorite** action.
- Render its favicon in the grid without a duplicate row among ordinary pins.
- Cmd+W keeps the Favorite and selects another tab; clicking it returns to it.
- Reset a navigated Favorite to its originally saved URL from the context menu.
- Move a Favorite back to ordinary pinned tabs while keeping its page open.
- Move earlier/later from the context menu; saved order survives app restart.
- Restore both Favorite entries and cached icons after restarting the app.
- Keep an accessible Expand sidebar button in collapsed mode, above the grid.
- Show saved Favorites in a new window before loading their pages, then open
  one through Cmd+T without creating a duplicate visible tab row.

Native drop handling has a regression test that moves a saved entry and rejects
unknown or renderer-tainted payloads. The user confirmed that physically dragging
the Wikipedia Favorite onto Example Domain reorders the two tiles. Context-menu
ordering is also verified. The macOS automation delivered press/release to the
tile without drag movement reaching its Views handler; that automation limitation
did not reproduce with the user's mouse. Temporary pointer diagnostics were
removed from the final patch.

Favorites are limited to 12 HTTP(S) pages per profile. Ordinary pins are not
automatically converted. Favorites are shared between windows of the same
profile; each window opens its own live tab when needed. Spaces and folders
remain future work. This is a development build, not release certification.


## October 27 — profile and session recovery

The existing Sidecar profile remained on disk and was the profile used by the
launcher. Its previous 12-tab window was available in Recently Closed. Restoring
that window exposed a development assertion: BrowserView reported the outer
contents container size, including Brave's one-pixel outline, while WebContents
reported the inner viewport (a two-pixel difference in both dimensions).
BraveBrowserView now reports the container's content bounds. The assertion and
other browser checks remain enabled.

The launcher now requests the previous session with `--restore-last-session`
instead of an explicit new-tab URL. A launcher regression test verifies that it
uses the existing Sidecar profile without requesting a blank page; another
checks that session restoration still respects the upstream-version guard.

Validation: native compilation succeeded, all 49 targeted native tests and all
24 Python safeguards passed. The previously closed window restored successfully
with 12 tabs and ten pins. A subsequent clean quit and guarded relaunch preserved
all 12 tabs and ten pins. An ignored local recovery copy of session files was
saved before the repair. Original Brave was not modified.

Profile presence and tab recovery do not prove login continuity. Sidecar's cookie
store contained fewer records than original Brave; the cause and continued
availability of individual site sessions remain unverified. No cookies or
credentials were decrypted or replaced during this recovery.


## October 27 — Tangerine application icon

The selected Tangerine Pod image is saved under assets/branding. The macOS
packaging script produced 16–1024 pixel representations, app.icns, and a named
AppIcon asset catalog with Xcode actool. Both development-channel resources
are preserved in a fourth, checksum-verified binary patch. The patch scope
validator now reads Git's numstat metadata so binary changes receive the same
scope checks as text changes. A regression test covers a mixed text/binary
patch, an omitted binary path, exact application, and subsequent tampering.

Validation: incremental native build succeeded in 13 steps; all 49 targeted
native tests and all 25 Python safeguards passed. Both app.icns and Assets.car
in the rebuilt application match the packaged assets byte for byte. The
64-pixel representation was visually inspected. The guarded launcher reopened
Sidecar using the existing profile, showing its seven saved Favorites and
remaining ordinary pinned tab. The app was already closed before this update;
no profile import, replacement, or tab cleanup was performed.

Direct Dock inspection through macOS automation timed out, so a live Dock
pixel check is not recorded. The app bundle resources and icon identifiers
(CFBundleIconFile and CFBundleIconName) were verified. In-browser Brave brand
marks are outside this app-icon change.


## October 27 — normal-launch profile and icon corrections

A normal Dock/Finder launch passed no --user-data-dir argument and opened
BraveSoftware/Brave-Browser-Development, an empty profile, while the development
launcher used work/sidecar-profile. The Sidecar bundle now declares
Sidecar/Development as CrProductDirName and the launcher uses that same path
under Application Support. On this Mac it is a symlink to the existing data
under Dev; no existing profile was moved or replaced. A local safety copy of
session files, preferences, and encrypted databases was saved first. The
existing profile is configured to restore its previous session on startup.
A regression test rejects a bundle whose default directory differs from the
launcher's expected directory.

The earlier icon's pre-rounded transparent border was framed again by macOS.
The current source is opaque, full-bleed square artwork, leaving masking to
the system. Both icon resources were rebuilt, and macOS's resolved 128-pixel
application icon was inspected: it shows a single orange rounded tile without
the extra gray backing. No Dock cache or system preferences were changed.

The user explicitly authorized restoring their encrypted Google cookies from
original Brave. After a SQLite backup, only Google-domain cookie rows were
merged into Sidecar; the original database was opened read-only, values stayed
encrypted, and other Sidecar rows were preserved. Google Play Console showed an
authenticated account. After a clean quit and a normal macOS app launch without
profile arguments, all seven Favorites and the ordinary pinned tab reappeared,
and the authenticated Google account view was verified again after refresh.
This verifies Google session recovery, not every website login or future
server-side session validity.

The native build and all 49 targeted native tests passed; all 26 Python
safeguards passed. No credential values or private profile files are committed.


The user subsequently authorized the remaining website sessions. With Sidecar
closed and another SQLite backup saved, non-Google cookie rows from original
Brave were merged without decrypting their values. The already recovered Google
session and Sidecar-only rows were retained. GitHub and Mixpanel cookie records
are present after relaunch. A user-operated Google passkey dialog briefly
interrupted live checks; no interaction with that dialog was automated. After
the user finished it, Mixpanel opened its authenticated project dashboard and
GitHub displayed its authenticated user menu and the repository in the original
Favorite. GitHub initially displayed a blank loading view, then rendered after
the regular-tab check and switching back. The temporary test tab was closed;
all seven Favorites and the existing ordinary pinned tab remained. Google,
GitHub, and Mixpanel authentication are verified; other services were not
individually checked and can require fresh authentication. The code repair's
GitHub verification run passed both jobs.


## October 27 — Favorites motion and Cmd+T sizing

Favorites now reorder by dragging inside the sidebar instead of through a macOS
drag session: the tile lifts and follows the pointer, its neighbours slide
aside, and release snaps it into place. Escape or lost mouse capture returns it,
and a drag never counts as a click. Tiles fade their hover state, shrink
slightly while pressed, and slide when reordered, added, or removed from the
menu. With no pasteboard data involved, the earlier renderer-taint check on
drops no longer applies. The Cmd+T bar fades in, and its height now comes from
its rows; previously the last row was clipped.

`scripts/patches.py --export` now regenerates the patch series and manifest
from the checkout. Patch 0002 was regenerated once with standard index lines;
its content is unchanged.

Validation: the browser built; all 49 targeted native tests passed. The old
drop test was replaced by one that sends real press, drag, Escape, and release
events to tiles hosted in a widget. All 29 Python safeguard tests passed. In the
relaunched app the Cmd+T bar measured 640×510 with all seven rows at full
height, and Favorites tiles rendered normally. Animation timing and how dragging
feels were not checked by automation and need a hands-on check.

Known issues found during this pass, not fixed: the collapsed sidebar's toggle
sits under the window's close button (macOS reports the close button at that
point); the app menu still reads "About Brave", "Hide Brave", and "Quit Brave";
and `gn check` fails for `//brave/browser/ui:ui` on the
`chrome_web_contents_view_focus_helper.h` include in `brave_browser_view.cc`.
