"""Bounded native-report import and explicit, source-bound review records."""
import hashlib
import io
import json
import math
import re
import shutil
import stat
import zipfile
from pathlib import Path, PurePosixPath

import cv2
import numpy as np
from PIL import Image

ASSETS = {"Original": "_VAS_Original", "Heatmap": "_VAS_Heatmap", "Regions": "_VAS_Regions",
          "Sequence": "_VAS_VisualSequence", "AOI": "_VAS_AreasOfInterest", "Legend": "_Results_Legend"}
CATEGORIES = ["Outdoor Macro", "In-Store Macro", "Signage", "Packaging", "Print", "Shelf Set", "Web Page", "Email", "Other"]


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_new(path, value):
    path = Path(path)
    data = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
    if path.exists():
        if path.read_bytes() == data:
            return
        raise FileExistsError(f"Preserve existing output; choose a new path: {path}")
    with path.open("xb") as stream:
        stream.write(data)


def safe_members(archive):
    infos = archive.infolist()
    if len(infos) > 100 or sum(i.file_size for i in infos) > 100_000_000:
        raise ValueError("Report ZIP exceeds 100 members / 100 MB expanded limit")
    seen, result = set(), []
    for info in infos:
        name = info.filename.replace("\\", "/")
        path = PurePosixPath(name)
        if name.startswith("/") or re.match(r"^[A-Za-z]:", name) or ".." in path.parts or stat.S_ISLNK(info.external_attr >> 16):
            raise ValueError("Unsafe ZIP member")
        if info.is_dir():
            continue
        basename = path.name.casefold()
        if basename in seen:
            raise ValueError("Duplicate ZIP basename")
        seen.add(basename)
        result.append((info, path.name))
    return result


def parse_report(path):
    with zipfile.ZipFile(path) as archive:
        members = safe_members(archive)
        assets = {}
        for key, suffix in ASSETS.items():
            matches = [(info, name) for info, name in members if Path(name).stem.casefold().endswith(suffix.casefold()) and Path(name).suffix.lower() in {".jpg", ".jpeg", ".png"}]
            if len(matches) > 1 or (key in {"Original", "Heatmap", "Regions", "Sequence"} and not matches):
                raise ValueError(f"Missing or ambiguous native {key} image")
            if matches:
                info, name = matches[0]
                data = archive.read(info)
                with Image.open(io.BytesIO(data)) as image:
                    if image.width * image.height > 25_000_000:
                        raise ValueError("Native image exceeds the 25 megapixel safety bound")
                    image.verify()
                assets[key] = {"data": data, "source_name": name, "extension": Path(name).suffix.lower()}
        pdfs = [info for info, name in members if name.lower().endswith(".pdf")]
        if len(pdfs) > 1:
            raise ValueError("Ambiguous native report PDF")
        category, pdf = None, None
        if pdfs:
            import pymupdf
            pdf = archive.read(pdfs[0])
            with pymupdf.open(stream=pdf, filetype="pdf") as doc:
                texts = [page.get_text() for page in doc]
            found = {cat for text in texts if "Image Category:" in text for cat in CATEGORIES if re.search(r"(?m)^" + re.escape(cat) + r"\s*$", text)}
            if len(found) == 1:
                category = found.pop()
        return assets, category, pdf


def prepare(report, case, result_url=None):
    report, case = Path(report), Path(case)
    if case.exists():
        raise FileExistsError("Case already exists; resume it instead of importing or scanning again")
    assets, category, pdf = parse_report(report)
    sizes = {}
    for key, item in assets.items():
        with Image.open(io.BytesIO(item["data"])) as image:
            sizes[key] = image.size
    size = sizes["Regions"]
    if any(sizes[k] != size for k in ["Heatmap", "Sequence"]):
        raise ValueError("Native Heatmap/Regions/Sequence dimensions differ; verify coordinate systems")
    if abs((sizes["Original"][0] / sizes["Original"][1]) / (size[0] / size[1]) - 1) > .005:
        raise ValueError("Original/native overlay aspect ratio mismatch")
    case.mkdir(parents=True)
    (case / "native").mkdir()
    shutil.copy2(report, case / "native_report.zip")
    records = {}
    for key, item in assets.items():
        dest = case / "native" / (key + item["extension"])
        dest.write_bytes(item["data"])
        records[key] = {"file": dest.relative_to(case).as_posix(), "sha256": sha(dest), "source_name": item["source_name"], "dimensions": list(sizes[key])}
    if pdf is not None:
        (case / "native/report.pdf").write_bytes(pdf)
        records["PDF"] = {"file": "native/report.pdf", "sha256": sha(case / "native/report.pdf")}
    manifest = {"schema_version": 1, "report_sha256": sha(case / "native_report.zip"), "native_size": list(size), "category": category, "result_url": result_url, "assets": records}
    write_new(case / "manifest.json", manifest)
    from native_annotations import label_boxes, points_from
    from outline_paths import associate_native_loops, box_distance
    images = load_case(case)[1]
    notes = []
    try:
        if size[0] * size[1] > 4_000_000:
            raise ValueError("Large native image: supply visually verified gaze coordinates instead of automatic detection")
        gaze = points_from(np.asarray(images["Sequence"]))
    except ValueError as error:
        gaze = []
        notes.append(str(error))
    boxes = label_boxes(images["Regions"])
    hotspots = [{"source_box": box, "panel_index": 0, "hotspot_anchor": None, "probability": None} for box in boxes]
    try:
        if len(boxes) > 12:
            raise ValueError("More than 12 candidate badges: review candidates and provide native contours instead of exponential matching")
        loops = associate_native_loops(images["Regions"], boxes) if boxes else []
        for hotspot, loop in zip(hotspots, loops):
            points = loop["points"]
            hotspot["hotspot_anchor"] = points[np.argmin(box_distance(points, hotspot["source_box"]))].tolist()
    except ValueError as error:
        notes.append(str(error))
    review = {"report_sha256": manifest["report_sha256"], "native_size": list(size), "native_verified": False, "evidence": "", "layout": "unreviewed", "panels": [{"id": "scene", "box": [0, 0, *size]}], "hotspots_complete": False, "hotspots": hotspots, "gaze": gaze, "regions": [], "legend": None, "candidate_notes": notes}
    write_new(case / "review.json", review)
    return manifest


def load_case(case):
    case = Path(case).resolve()
    manifest = read(case / "manifest.json")
    if sha(case / "native_report.zip") != manifest["report_sha256"]:
        raise ValueError("Native report ZIP changed after import")
    images = {}
    for key, asset in manifest["assets"].items():
        path = (case / asset["file"]).resolve()
        path.relative_to(case)
        if sha(path) != asset["sha256"]:
            raise ValueError(f"Native asset changed: {key}")
        if key != "PDF":
            with Image.open(path) as image:
                images[key] = image.convert("RGB")
    size = tuple(manifest["native_size"])
    if any(images[key].size != size for key in ["Regions", "Heatmap", "Sequence"]):
        raise ValueError("Native dimensions changed")
    original = images["Original"]
    if abs((original.width/original.height)/(size[0]/size[1])-1) > .005:
        raise ValueError("Original aspect ratio changed")
    images["Original"] = original.resize(size, Image.Resampling.LANCZOS)
    return manifest, images


def finite_number(value):
    return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value)


def polygon_mask(points, size):
    array = np.asarray(points, dtype=float)
    if array.ndim != 2 or array.shape[1] != 2 or len(array) < 3 or not np.isfinite(array).all():
        raise ValueError("ROI requires at least three finite [x,y] vertices")
    if np.max(np.abs(array)) > 100_000_000:
        raise ValueError("ROI coordinates exceed safe rasterization bounds")
    mask = np.zeros((size[1], size[0]), np.uint8)
    cv2.fillPoly(mask, [np.rint(array).astype(np.int32)], 1)
    if not mask.any():
        raise ValueError("ROI has no pixels inside the native image")
    return mask.astype(bool)


def load_review(case, review_path=None, annotations=False):
    manifest, images = load_case(case)
    review_path = Path(review_path) if review_path else Path(case) / "review.json"
    review = read(review_path)
    if review.get("report_sha256") != manifest["report_sha256"] or review.get("native_size") != manifest["native_size"]:
        raise ValueError("Review does not match this native report/coordinate system")
    if review.get("native_verified") is not True or not str(review.get("evidence", "")).strip():
        raise ValueError("Visually review native evidence and record native_verified/evidence first")
    width, height = manifest["native_size"]
    if annotations:
        if review.get("layout") not in {"single", "montage"} or review.get("hotspots_complete") is not True:
            raise ValueError("Verify layout and completeness of native hotspot labels")
        panels = review.get("panels", [])
        if not panels or (review["layout"] == "montage" and len(panels) < 2):
            raise ValueError("Record actual photo-panel bounds; do not split a montage at 50% blindly")
        for panel in panels:
            box = panel["box"]
            if len(box) != 4 or not all(finite_number(v) for v in box) or not (0 <= box[0] < box[2] <= width and 0 <= box[1] < box[3] <= height):
                raise ValueError("Invalid native panel bounds")
        gaze = review.get("gaze", [])
        if len(gaze) != 4 or any(not isinstance(p.get('order'), int) or isinstance(p.get('order'), bool) for p in gaze) or sorted(p.get('order', 0) for p in gaze) != [1, 2, 3, 4]:
            raise ValueError("Verify all four unique native gaze points; never fill missing ones")
        for point in gaze:
            if not all(finite_number(point.get(k)) for k in ["x", "y"]) or not (0 <= point["x"] < width and 0 <= point["y"] < height):
                raise ValueError("Gaze point outside native image")
        boxes = []
        for spot in review.get("hotspots", []):
            box = spot["source_box"]
            if len(box) != 4 or not all(isinstance(v, int) and not isinstance(v, bool) for v in box) or not (0 <= box[0] < box[0]+box[2] <= width and 0 <= box[1] < box[1]+box[3] <= height):
                raise ValueError("Invalid native probability bitmap box")
            if box in boxes:
                raise ValueError("Duplicate native probability box")
            boxes.append(box)
            index, anchor = spot.get("panel_index"), spot.get("hotspot_anchor")
            if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < len(panels):
                raise ValueError("Invalid probability-label panel mapping")
            panel = panels[index]["box"]
            if not anchor or len(anchor) != 2 or not all(finite_number(v) for v in anchor) or not (panel[0] <= anchor[0] <= panel[2] and panel[1] <= anchor[1] <= panel[3]):
                raise ValueError("Native hotspot anchor must belong to its mapped panel")
    return manifest, images, review, sha(review_path)
