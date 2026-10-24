# VAS Scanning Tutorial

**Preparing and comparing architectural images**  
Prepared by **Shuyuun Wang** · Supervisor **Bin Jiang**  
24 October 2026

## 1 What the scan tells you

3M VAS predicts initial, first-glance visual attention, described by 3M as approximately 3–5 seconds. Use it to examine likely focal regions and viewing order. It does not measure beauty, livingness, wholeness, preference, or actual participants’ eye movements. Interpret it alongside L-score, B-score and MOST, without assuming agreement. [1]

## 2 Prepare a fair input

- **Use a clear original.** VAS supports RGB JPG, PNG and PDF. 3M recommends at least **600 × 600 pixels**; smaller images may be automatically resized, affecting results. Check actual pixel dimensions, not only DPI. Upscaling cannot recover missing photographic detail. [1, 2]
- **Keep comparisons consistent.** Match canvas dimensions, resolution, framing and displayed subject scale where feasible; preserve aspect ratio. Prefer a realistic viewing context. 3M recommends landscape photographs with wider framing; this does not require rotating buildings or force a particular montage layout. Record unavoidable differences in viewpoint, light, season, people and occlusion. [2]
- **Keep the scanned visual clean.** Do not scan old heatmaps, numbered gaze paths, captions, browser controls or added comparison labels. Preserve original files and credits separately. Do not erase watermarks or use generative enhancement to invent details. If annotations cannot be excluded without damaging the scene, retain and report them as confounds.

Provenance, non-alteration and the comparison controls below are research safeguards, not additional 3M upload requirements.

## 3 Choose the comparison before scanning

**Combined scan:** place both images in one fixed montage to investigate their attention pattern in a shared visual field. Record panel bounds, gap and displayed scale. A position-swapped scan is a useful robustness check; swap whole panels without mirroring or stretching their contents. Report both results rather than selecting the preferred layout.

**Separate scans:** analyze each photograph in its own visual context. These characterize within-image patterns; their percentages do not directly measure competition between the two photographs. The website’s side-by-side results viewer does not turn separate scans into one joint analysis.

Choose the content category from the actual scene and research target. For architectural exteriors, **Outdoor Macro** is generally appropriate; ordinary non-retail interiors or line drawings may require **Other**. Confirm the current category description. Keep it fixed for matched conditions; 3M uses content-specific algorithms. Do not change categories after seeing results to obtain a preferred conclusion. [3]

## 4 Run and save

1. Open [VAS Portfolio](https://vas.3m.com/app/portfolio), upload the authorized input, select its card, and confirm filename, orientation and content category.
2. Decide whether AOIs are needed. For descriptive viewing, the three basic reports may suffice. To compare specified regions numerically, define corresponding **Areas of Interest before scanning**, using the same rule across conditions. Distinguish whole-photo panels from building-only regions; exclude montage gaps. A local post-processing ROI is not a native VAS AOI. [3]
3. Submit **Analyze once**. Save the input, category, AOI geometry or explicit “none,” scan date, result URL and native downloaded report. If interrupted, recover the existing result before resubmitting. In the previously observed interface, **Re-analyze clears prior results**; preserve them and use a new input version for a new condition.

## 5 Read the reports correctly

- **Heatmap:** shows the predicted spatial pattern of attention. Red does not mean “more beautiful”; absent heat does not establish that a region is never seen. [1]
- **Hotspots and AOIs:** each percentage estimates the likelihood of looking somewhere within that region during first-glance viewing. A viewer may see several regions, so percentages are **not attention shares**, need not total 100%, and must not be added or normalized into a beauty score. Hotspot probability is not an AOI result unless it actually describes that AOI. [1]
- **Gaze Sequence:** the numbered points indicate a predicted sequence of likely locations, not a recorded individual scanpath, fixation duration or complete account of viewing. [1]

A whole-image AOI in a separate scan may be near saturation and tell little about differences between buildings. Color-derived coverage, R or composite indices are optional **researcher-defined post-processing**, not native 3M beauty or coherence scores. State their formulas and thresholds separately.

## 6 Submit a reproducible record

Keep **original input + preprocessing record + scan settings + native reports + short interpretation**. Record source and credit, input dimensions and hash, comparison layout and panel identities, AOI rule, category, date and any missing conditions. Check every reported percentage and numbered point against native evidence. Label edited presentation figures as composites; retain the unchanged native reports.

A suitable conclusion is: “Under the recorded layout and category, VAS predicted attention around these features.” A claim that one image is more whole or beautiful requires separate argument and evidence. [1]

**Sources:** [1] [3M VAS FAQs](https://vas.3m.com/faqs); [2] [3M VAS Support](https://www.3m.com/3M/en_US/visual-attention-software-us/support/); [3] [How it Works](https://vas.3m.com/howitworks). Checked 24 October 2026. See [source notes](SOURCES.md) for handbook credits and the distinction between official guidance and local research safeguards.

**Teaching context:** *Living Structure + AI: Four Hands-On Exercises for Exploring and Assessing Wholeness*, Hongkai Zhang and Bin Jiang, VAS section p. 5 and examples p. 10. This supplementary tutorial does not reproduce its figures.
