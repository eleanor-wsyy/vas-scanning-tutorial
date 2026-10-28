# Architectural Image Analysis with 3M VAS

A concise classroom guide and reusable Codex skill for responsible **3M Visual Attention Software (VAS)** analysis of architectural images.

Shuyun Wang and Bin Jiang  
LivableCityLAB, Thrust of Urban Governance and Design  
The Hong Kong University of Science and Technology (Guangzhou), China  
Email: [swang585@connect.hkust-gz.edu.cn](mailto:swang585@connect.hkust-gz.edu.cn) [binjiang@hkustgz.edu.cn](mailto:binjiang@hkustgz.edu.cn)  
Updated 24 October 2026. Independent teaching material; not a 3M product or endorsement.

## Read the tutorial

- [English tutorial](docs/VAS-Scanning-Tutorial.md) · [PDF handout](docs/VAS-Scanning-Tutorial.pdf)
- [中文速查版](docs/VAS-Scanning-Tutorial-zh.md)
- [Official sources and evidence boundaries](docs/SOURCES.md)
- [Scholarly references and experiment-method mapping](docs/REFERENCES.md)

The guide covers input quality, content categories, combined versus separate scans, AOIs, interpretation, and reproducible reporting. **VAS predicts initial visual attention; it does not measure beauty or wholeness.**

## Install the skill

Copy `skills/vas-scanning/` into your Codex skills directory (`~/.codex/skills/` by default). Restart or refresh skill discovery as required by your installation. This repository does not bundle a VAS account or subscription.

Example request:

> Use $vas-scanning to prepare a comparison of these architectural photographs. Check image quality, specify the comparison and AOI protocol, and preserve native evidence. Do not upload or scan until the images and destination are authorized.

**Default: images only.** The skill now bundles a portable native-report renderer. It produces a light heatmap (exported-heatmap blend weight 0.45), original percentage labels, yellow hotspot outlines and verified 1–4 gaze points with red paths. It does not compute R or C unless requested.

The skill is independent of the earlier Michael Diamant source-discovery workflow. It generalizes the scanning safeguards without assuming every image comes from X or requiring a particular montage orientation.

## Local image preflight

Python 3.10+ is needed. The full toolkit requires Pillow, NumPy, OpenCV and PyMuPDF; the preflight-only helper still uses just Pillow. In a fresh environment:

```sh
python -m pip install -r requirements.txt
python skills/vas-scanning/scripts/preflight.py photo-A.jpg photo-B.png --output preflight.json
python -m unittest discover -s tests -v
```

The helper **only reads local raster images** and writes a manifest. It reports dimensions, color mode, EXIF orientation, SHA256, duplicate inputs, and official-size warnings. It does not measure sharpness, alter files, upload images, call VAS, or certify experimental validity. PDF is supported by VAS but must be exported and checked visually before this raster-only helper can inspect it.

## Native report rendering and opt-in metrics

```sh
python skills/vas-scanning/scripts/vas.py prepare --report report.zip --case case-01
# The agent inspects unchanged native evidence and completes case-01/review.json.
python skills/vas-scanning/scripts/vas.py render --case case-01

# Only when requested by the user:
python skills/vas-scanning/scripts/vas.py metrics --case case-01 --calculate r
python skills/vas-scanning/scripts/vas.py metrics --case case-01 --calculate c
python skills/vas-scanning/scripts/vas.py metrics --case case-01 --calculate both
```

See [tool commands, review fields and formulas](skills/vas-scanning/references/local-tools.md). R needs a source-bound ROI. C additionally needs the native legend, complete hotspots/gaze and native AOI probabilities. These are researcher-defined estimates, not official 3M beauty scores. Detection suggests existing annotations; native and final visual QA remain necessary. No new scans, uploads or external API calls are performed by these local tools.

User-facing default delivery is the figure; hashes/review records are kept internally. Metrics write separate JSON only on explicit calculation commands, using original native exports rather than the display image. Existing outputs are never silently overwritten.

To rebuild the PDF, install `requirements-build.txt` and run `python scripts/build_tutorial_pdf.py`.

## Data and rights

The illustrated edition includes three unchanged image excerpts from page 5 of Hongkai Zhang and Bin Jiang’s handbook, with attribution and historical-example captions. Their original rights are retained; see [image notice](docs/assets/NOTICE.md). No complete source PDF, private chats, account data or native VAS report archive is distributed. Input photos and VAS outputs remain subject to their respective rights and service terms. Uploading to VAS and republishing to GitHub are separate permissions.

## Credits

The teaching context is *Living Structure + AI: Four Hands-On Exercises for Exploring and Assessing Wholeness*, by **Hongkai Zhang and Bin Jiang**, especially its VAS section on p. 5 and examples on p. 10. This tutorial is newly written supplementary guidance, not a revision attributed to the handbook authors. The tutorial author line is Shuyun Wang and Bin Jiang, as requested by the user; original handbook and image-source credits remain unchanged.

Original text and code in this repository are covered by the [MIT license](LICENSE); third-party images, materials and trademarks are excluded.
