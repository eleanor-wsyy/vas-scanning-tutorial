"""Read-only raster checks; no image alteration, uploads or VAS calls."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, UnidentifiedImageError


def inspect_image(path):
    result = {"file": str(path), "warnings": [], "errors": []}
    try:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        result.update(sha256=digest.hexdigest(), bytes=path.stat().st_size)
        with Image.open(path) as check:
            check.verify()
        with Image.open(path) as image:
            w, h = image.size
            orientation = image.getexif().get(274, 1)
            result.update(format=image.format, color_mode=image.mode, width=w, height=h,
                          exif_orientation=orientation, meets_recommended_dimensions=w >= 600 and h >= 600)
            if not result["meets_recommended_dimensions"]:
                result["warnings"].append("Below 3M's recommended 600 x 600 pixels; upscaling cannot restore source detail.")
            if image.format not in {"JPEG", "PNG"}:
                result["warnings"].append("Not a documented raster upload format (JPG/PNG); export and inspect an authorized copy.")
            if image.mode != "RGB":
                result["warnings"].append("Not RGB; document conversion and the background used for any transparency.")
            if orientation != 1:
                result["warnings"].append("EXIF orientation differs from stored pixels; visually check displayed orientation.")
            if getattr(image, "n_frames", 1) > 1:
                result["warnings"].append("Multiple frames; explicitly select and inspect a static input.")
    except (OSError, ValueError, SyntaxError, UnidentifiedImageError, Image.DecompressionBombError) as error:
        result["errors"].append(f"Cannot verify raster: {type(error).__name__}: {error}")
    return result


def build_manifest(paths):
    images, seen = [inspect_image(p) for p in paths], {}
    for index, item in enumerate(images):
        digest = item.get("sha256")
        if digest:
            if digest in seen:
                item["duplicate_of_index"] = seen[digest]
                item["warnings"].append("Identical input bytes; confirm this duplicate is intentional.")
            else:
                seen[digest] = index
    return {"schema_version": 1, "source_checked": "2026-10-24",
            "recommendation_source": "https://www.3m.com/3M/en_US/visual-attention-software-us/support/",
            "scope": "Local raster metadata only; no sharpness judgment, modifications, uploads or scans.",
            "images": images, "visual_review_required": True,
            "notes": ["The size recommendation concerns the uploaded visual, not an official per-panel requirement.",
                      "Matching metadata does not establish valid experimental controls or clear source detail."]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, help="New JSON manifest; never overwrite existing files.")
    args = parser.parse_args(argv)
    manifest = build_manifest(args.images)
    text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        try:
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(text)
        except OSError as error:
            parser.error(f"Cannot create output: {error}")
        print(f"Manifest: {args.output}")
    else:
        print(text, end="")
    return 1 if any(i["errors"] for i in manifest["images"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
