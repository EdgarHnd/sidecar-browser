# Built-in updates

The AI heartbeat was removed at the user's request. Sidecar will use Brave's
native Sparkle updater on macOS, with signed releases hosted on GitHub Releases.
No Codex session or AI scheduler is part of the runtime update path.

`patches/0002-native-update-feed.patch` adds an independent feed route for the
Sidecar bundle identity. It reads `SidecarUpdateFeedURL` and `SUPublicEDKey`
from the app's signed Info.plist, refuses non-HTTPS/credential-bearing URLs and
invalid public-key encodings, and prevents falling through to Brave's feed or
command-line feed override for Sidecar. Sparkle remains responsible for verifying
download signatures and installing the update. URL validation alone is not
signature verification.

The patch is prepared separately from the running development build so changing
its input manifest cannot race the initial source synchronization. It has not
yet been compiled into a browser or exercised in an end-to-end upgrade.

Compile the Foundation-only native validator test on macOS:

```sh
xcrun clang++ -std=c++20 -fobjc-arc -framework Foundation \
  tests/update_feed_test.mm -o ../../work/update-feed-test
../../work/update-feed-test
```

Release configuration must supply:

- A GitHub repository and HTTPS release asset URL ending in
  `/releases/latest/download/appcast.xml`.
- A persistent Ed25519 public key embedded in the app, with its private key
  held securely by the release builder.
- Sidecar's own release bundle identity and separate profile directory.
- A non-component Release build with Sparkle enabled and Omaha 4 disabled.
  This avoids Brave's independent Omaha rollout selecting the wrong updater.
- Signed packages, update signatures and a monotonically increasing build
  version; a verified upgrade from an older Sidecar installation.

Brave's native updater checks every three hours while running and downloads
updates in the background. Relaunch completes installation. A conventional
release build workflow must independently track Brave stable, build and test
Sidecar, then publish a signed artifact and appcast. The app updater cannot
compile a new Brave release by itself.

Release hosting/signing and the full release workflow are not operational yet.
The first component build is for local testing and does not enable Sparkle.

## Release-feed generator

`scripts/appcast.py` takes an already-signed archive and its public Ed25519
signature. It verifies that signature over the actual file with OpenSSL before
writing the GitHub Releases appcast. It rejects non-increasing versions when
given the previous version. Its tests use temporary generated keys and confirm
that a modified payload and a different public key are rejected.

Use the same public key embedded in Sidecar and the exact packaged app's
`CFBundleVersion`. Validate the archive's application identity, code signatures
and version before this step. The feed generator verifies the archive signature;
it does not certify the app's contents, publish releases or install updates.

The signing operation should use Sparkle's signing tool with a dedicated release
keychain. No private signing key belongs in a repository, workflow log, or
command-line argument. Upload the verified archive and `appcast.xml` to the
same published GitHub release, then test an upgrade from the previous build.
