#!/usr/bin/env python3
"""Package Sidecar's selected PNG as macOS ICNS and AppIcon assets."""
import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def package(source, output):
    output.mkdir(parents=True, exist_ok=True)
    iconset = output / "Sidecar.iconset"
    catalog = output / "Sidecar.xcassets"
    app_icons = catalog / "AppIcon.appiconset"
    iconset.mkdir(exist_ok=True)
    app_icons.mkdir(parents=True, exist_ok=True)
    images = []
    for size in (16, 32, 128, 256, 512):
        for scale in (1, 2):
            suffix = "@2x" if scale == 2 else ""
            name = f"icon_{size}x{size}{suffix}.png"
            pixels = str(size * scale)
            subprocess.run(["sips", "-z", pixels, pixels, str(source),
                            "--out", str(iconset / name)], check=True,
                           stdout=subprocess.DEVNULL)
            (app_icons / name).write_bytes((iconset / name).read_bytes())
            images.append({"idiom": "mac", "size": f"{size}x{size}",
                           "scale": f"{scale}x", "filename": name})
    info = {"version": 1, "author": "Sidecar"}
    (catalog / "Contents.json").write_text(json.dumps({"info": info}, indent=2) + "\n")
    (app_icons / "Contents.json").write_text(
        json.dumps({"images": images, "info": info}, indent=2) + "\n")
    subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o",
                    str(output / "app.icns")], check=True)
    subprocess.run(["xcrun", "actool", "--compile", str(output),
                    "--platform", "macosx", "--minimum-deployment-target", "11.0",
                    "--app-icon", "AppIcon", "--output-partial-info-plist",
                    str(output / "AppIcon-info.plist"),
                    "--output-format", "human-readable-text", str(catalog)], check=True)
    for name in ("app.icns", "Assets.car"):
        if not (output / name).is_file():
            raise RuntimeError(f"Icon packaging did not produce {name}")
    print(f"Packaged Sidecar icon in {output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path,
                        default=ROOT / "assets/branding/sidecar-tangerine.png")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    package(args.source.resolve(strict=True), args.output.resolve())


if __name__ == "__main__":
    main()
