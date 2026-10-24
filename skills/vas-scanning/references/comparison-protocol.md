# Comparison protocol

## Choose a question

| Design | Supports | Does not establish |
|---|---|---|
| Joint montage | Predicted attention within one shared layout | Which building is more beautiful; a layout-independent ranking |
| Position-swapped montage | Sensitivity to display position while retaining panel content | A pure rotation effect if scale, framing or composition also changed |
| Separate images | Predicted attention within each image | Direct competition between images; joint probability from the separate percentages |
| Category contrast | Sensitivity to selected content type with the same input | A general best category selected after inspecting outcomes |

Fix the input, category, layout, AOI scope and planned interpretation before scanning. A full factorial design is useful only when the actual question concerns multiple factors; do not impose it on a short classroom exercise.

## AOI and metric boundaries

- Native AOI probability: the service result for the marked region.
- Hotspot probability: the service result for its automatically identified hotspot, not for a different AOI.
- Local ROI: geometry used by a later calculation, not evidence an AOI was sent to VAS.
- Heatmap coverage: an estimate derived from exported pixels and explicit thresholds; not a direct readout of native probability.
- R or a composite: externally defined calculation requiring a cited formula, parameter record and limitations; never silently treat it as 3M’s official score.

Several regions can be seen by the same viewer. Their probabilities cannot be added or normalized into attention shares. Full-frame AOIs in separate scans may be near saturation; retain native values but avoid ranking beauty with them. Missing results remain null/pending, not zero. For numeric comparisons, retain native probabilities and explain scope and position sensitivity; avoid claiming statistical significance without an appropriate study.

## Preparation controls

Preserve the original scene and source identity. Match dimensions, resolution, framing and subject scale where feasible. Document differences that cannot be matched; do not claim causal isolation when viewpoint, weather, clutter or source quality differ. Keep watermarks when removing them would alter source content; choose an unmarked authorized source when available rather than painting over it. Exclude added labels from the visual stimulus and keep credits outside it.

Choose bounds from the actual divider, not the midpoint. Swapping panels must preserve their internal pixels, relative scale and source IDs. Record coordinate systems, panel extents, any transformations, and the AOI rule. A single large canvas does not establish good source resolution.

## Resume and verification

Hash the original and input; keep condition IDs distinct from filenames and physical position. Save unchanged native evidence. Check settings and the native original against the intended input, then visually verify every reported label and gaze point. A composite can be useful but must not replace native evidence.

If Analyze was submitted but completion is uncertain, find the unique existing card/result before any retry. A failed download is not a failed analysis: retry only the export when appropriate. Do not overwrite archived results. Read one compact handoff and the next small batch on resume; avoid repeated scans, giant chat histories or re-rendering already verified outputs.
