# Sidecar Tangerine icon

The selected Pod mark uses an ivory sidecar silhouette, a single solid wheel,
and a tangerine-to-coral rounded-square background with a soft enamel highlight.
Edgar selected Tangerine from the six color and finish options on October 27, 2026.
The current source, sidecar-tangerine-full-bleed.png, is opaque and fills the
square canvas; macOS supplies its corner mask. The earlier transparent,
pre-rounded source is retained only as a design reference. It was displayed
inside an extra system frame on the user's Mac and is not packaged anymore.

The icon was generated with OpenAI image generation, using the selected concept
as the reference. The latest edit removed the pre-rounded outer tile and transparent padding
while preserving the ivory pod and orange gradient.

Package the source on a Mac with Xcode installed:

```sh
python3 scripts/package_icon.py --output work/tangerine-icon
```

The script uses sips for the standard 16–1024 pixel Mac icon representations,
iconutil for app.icns, and actool for the named AppIcon in Assets.car. It only
writes into the requested output directory; it does not install or restart apps.

Both packaged assets are recorded in 0004-sidecar-tangerine-icon.patch under
Brave's development-channel branding directory. The existing Brave branding
step copies them into the application bundle. This covers both CFBundleIconFile
and CFBundleIconName and keeps the icon through subsequent local builds.
Other Brave channels and the installed original Brave app are unchanged.

For a future icon revision, review the packaged images, copy both files into
app/theme/brave/mac/development/ in the pinned core checkout, and regenerate
the binary patch and manifest hashes. Asset-catalog bytes may vary with Xcode;
the checked-in binary patch is the reviewed build input. The patch validator and
source guard validate binary paths and exact contents along with the UI patches.
