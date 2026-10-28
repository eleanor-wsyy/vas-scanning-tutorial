# Local VAS tools

The default deliverable is a PNG composite. R/C are **opt-in**, not a hidden step during import or rendering. The tools consume real downloaded report ZIPs; they do not run scans or access accounts. Python 3.10+, Pillow, NumPy, OpenCV and PyMuPDF are required (repository `requirements.txt`).

## Commands

```sh
# 1. Import an existing native report. Existing case directories are never replaced.
python <skill>/scripts/vas.py prepare --report report.zip --case case-01

# 2. Agent inspects native images and completes case-01/review.json from actual evidence.
# 3. Default output: light heatmap, native percentage bitmaps, yellow contours, red gaze path.
python <skill>/scripts/vas.py render --case case-01

# Optional display adjustment, not a change to analytical inputs.
python <skill>/scripts/vas.py render --case case-01 --heatmap-weight 0.30 --output case-01/lighter.png

# 4. After viewing the final PNG against native evidence, record visual QA.
python <skill>/scripts/vas.py approve --case case-01 --composition case-01/figure.composition.json --evidence "Describe the actual native-versus-figure checks"

# ONLY on explicit user request:
python <skill>/scripts/vas.py metrics --case case-01 --calculate r
python <skill>/scripts/vas.py metrics --case case-01 --calculate c
python <skill>/scripts/vas.py metrics --case case-01 --calculate both
```

Use the real path in place of `<skill>`. For another reviewed record, pass `--review file.json`; approval binds the exact record and output hash. Identical renders/calculations are reusable. Different inputs/options never overwrite prior outputs: choose a new output/version. A failed export or local render is not permission to rescan.

## What is automatic and what needs review

`prepare` safely imports the four native images Original, Heatmap, Regions and VisualSequence, plus AOI/legend/PDF when present. It records hashes, coordinate dimensions and the category found in the PDF. A missing/unreadable category stays unverified; check it in the original result. No blanket Other category or 2.35× zoom is imposed.

The importer proposes gaze coordinates and probability-label boxes from existing pixels. These are **candidates**, not generated predictions. The agent must inspect the native images, correct any missing/false detections, identify actual photo-panel bounds and label-to-contour associations, and record `native_verified`, `evidence`, `layout`, and `hotspots_complete`. No extra confirmation from the user is needed merely to perform this visual QA. If detection is ambiguous, preserve the case and fix only the source-grounded annotation record, not the native images. Large images/many badges deliberately skip expensive automatic matching and require reviewed native coordinates/contours.

`render` refuses unreviewed data. It copies the actual percentage bitmap labels, traces/reuses native closed hotspot contours, and redraws only the verified gaze-order annotations. Default output width is 1200 portrait / 2048 landscape, marker diameter 32 / 44 pixels, no added title/footer. Label placement remains inside its actual panel and near its own hotspot. An impossible layout stops for review instead of placing labels over unrelated panels. The PNG starts as `needs_visual_review`; only after inspecting it should the agent call `approve`.

## Review record

All geometry is in **native Regions/Heatmap pixels**, using `manifest.json` dimensions. Original is aligned in memory only if its aspect ratio agrees; unchanged files and hashes are retained. Fill the generated `review.json`; do not substitute screenshot pixels or normalized coordinates without an explicit transform.

- `report_sha256`, `native_size`: must match the imported manifest.
- `native_verified: true`, `evidence`: actual observations supporting the native original/settings/annotations. Do not set this merely because a command ran.
- `layout`: `single` or `montage`. `panels`: records with `id` and `box: [left, top, right, bottom]`. A montage requires every actual photo panel; no blind midpoint split. A separator can be recorded as its own display panel when a real hotspot belongs there; omit it from photo metric ROIs.
- `hotspots_complete: true`: confirm every native percentage tag is accounted for. `hotspots`: one record per label with `source_box: [x,y,width,height]`, `panel_index`, and a corresponding `hotspot_anchor: [x,y]` on its actual boundary. `probability` may stay null for image-only rendering; for C it must be the visually read native number, 0–100. Optional `native_contour: [[x,y],...]` supplies an exact reviewed native boundary if automatic matching fails; never invent an ellipse or extrapolate a missing region.
- `gaze`: exactly four records `{order: 1..4, x, y}`, all copied/verified from the native sequence. Missing/ambiguous points stop the workflow.

The following fields are **unnecessary for default images**:

- `regions`: unique `id` and `roi: [[x,y],...]` for each explicitly requested metric region. R uses that ROI, with outside-image vertices naturally clipped by rasterization rather than changing their coordinates. C uses the same ROI for H/P/G. To investigate a different scope, use another named region/record, not a silent scope change.
- For C, each region also has `aoi: {box: [left,top,right,bottom], probability: 0..100, evidence: "..."}`. This must describe the actual native AOI, not an automatic hotspot or a post-hoc ROI. Rectangular AOI and local building-envelope ROI can differ; both are retained.
- For C, `legend: {box: [left,top,right,bottom], range: [first_probability,last_probability], evidence: "..."}` identifies the native colored probability bar. Verify its endpoints/direction; no source-specific legend box is hard-coded.

ROI/AOI boundaries should have been fixed before inspecting outcomes. If that cannot be established for a reused report, label the calculation exploratory; do not claim preregistered or controlled evidence.

## Requested metrics and limitations

**R** follows the structure of Lavdas and Salingaros (2022), DOI `10.3390/challe13020056`:

`R = ROI heatmap coverage percentage / (red spots + non-contiguous coverage regions)`

The bundled export-image estimate reuses the earlier local protocol: subtract `0.30 × Original`; coverage requires residual max RGB ≥30 and HSV saturation ≥70; red requires hue ≤12 or ≥170, saturation ≥160 and value ≥140 (OpenCV H 0–179). Use 8-connectivity and 25-pixel minimum components. Empty coverage produces null R. The output includes the 72-point sensitivity grid over coverage threshold, red saturation/value/hue and minimum component area. The paper’s full pixel thresholds were not specified; do not call these locally chosen thresholds its exact ImageJ reproduction or an official 3M score. Fixed native-pixel area thresholds are not scale invariant.

**C** adapts the four-report average of Ro and Huffman (2025), DOI `10.1080/02697459.2024.2342755`:

`C = (H_approx + P + G + A) / 4`

- H: color-derived ROI coverage at a legend-estimated ≥40% probability, residual/saturation checks and ≥25-pixel components. Color exports do not provide exact per-pixel probability values; retain the approximation label.
- P: highest verified native hotspot probability among hotspots with ≥50% of their true polygon area in the ROI. This overlap rule is a local choice. If none qualifies, P and C remain null, not zero.
- G: count of the four verified gaze centers in the ROI, divided by four and multiplied by 100.
- A: the separately verified native AOI probability. Do not add hotspot probabilities to manufacture A.

C is exploratory and depends on these component definitions. Full-frame single-image AOIs or saturated probabilities may be uninformative; do not interpret C as proof of superior beauty. The calculator reads **unchanged native images**, never the lightened display PNG, so changing display weight cannot change R/C. JSON outputs retain protocols, source/review hashes and warnings; no new predictions or missing data are fabricated.

## Rights and portability

The portable modules reuse the existing local annotation/contour/placement algorithms, not the hard-coded B-group scripts or their per-case repairs. Numeral-only recognition masks have their own provenance notice; no source photographs, account data or real report ZIPs ship with the skill. Report archives are bounded and screened for traversal, symlinks and duplicate basenames; native-file changes invalidate subsequent actions. Matplotlib, cloud OCR and third-party APIs are not needed.
