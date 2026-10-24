# 3M VAS Scanning Tutorial

Prepared by **Shuyuun Wang**  
Supervisor **Bin Jiang**

## 1. Introduction

### 1.1 What is 3M VAS?

3M Visual Attention Software (VAS) predicts initial visual attention over approximately 3–5 seconds. It provides Heatmap, Hotspots and Gaze Sequence reports. Use it to examine likely focal regions and viewing order, alongside L-score, B-score and MOST. It does not directly measure beauty, livingness or wholeness, and its predictions are not actual participants’ eye movements (3M, FAQs).

### 1.2 Research background

The architectural VAS approach draws on **Lavdas, Salingaros and Sussman (2021)**. The earlier near/far and R-value exercise follows **Lavdas and Salingaros (2022)**, especially Sections 3.5 and 4.3; its R formula and 2.35× digital zoom are optional study-specific procedures, not 3M defaults. **Berto, Barbiero and Salingaros (2022)** provide related façade research comparing VAS with perceived restorativeness. **Alexander (2002–2005)** and **Jiang and de Rijke (2023)** provide the living-structure context, not validation that VAS measures wholeness.

## 2. Preparing Images

### 2.1 Image quality

Use a clear original in **RGB JPG, PNG or PDF**. 3M recommends at least **600 × 600 pixels**. Smaller images may be automatically resized, affecting results. Check actual pixel dimensions, not only DPI; upscaling cannot recover missing detail. For a montage, also check each source panel: a large canvas does not guarantee clear source content (3M, FAQs; Support).

Preserve aspect ratio and avoid generative enhancement. Do not scan old heatmaps, gaze numbers, browser controls or added comparison labels. Preserve untouched sources and credits. Do not erase watermarks; use an authorized unmarked source when available, or retain and report the mark as a confound.

### 2.2 Comparable conditions

Match image dimensions, resolution, framing and displayed subject scale where feasible. 3M recommends realistic sightlines and wider landscape photographs; do not rotate buildings to force a layout. Record differences in viewpoint, lighting, people and occlusion (3M, Support).

**Combined analysis:** place both images in one fixed montage to study attention in a shared visual field. Record panel boundaries, scale and gap. A position-swapped scan can test robustness; swap whole panels without mirroring or stretching their contents, and report both conditions.

**Separate analysis:** scan each photograph in its own context. Separate percentages do not directly measure competition between the two images. Viewing two reports side by side is not a joint scan. Freeze the design before seeing results. Figure 2 illustrates the two presentation formats.

## 3. Website User Guide

See Figure 1 for the handbook’s illustrated workflow; the steps below govern this tutorial.

### 3.1 Upload and select a category

Open [VAS Portfolio](https://vas.3m.com/app/portfolio), upload the authorized input and check its filename and orientation. Choose the category from the actual scene and research target. **Outdoor Macro** is generally suitable for architectural exteriors; **Other** may suit ordinary non-retail interiors or line drawings. Confirm current descriptions and keep the category fixed across matched conditions: 3M uses content-specific algorithms (3M, How it Works).

### 3.2 Define Areas of Interest

AOIs are optional for descriptive viewing. For native regional probabilities, define corresponding **Areas of Interest before scanning**, using the same rule across conditions. Distinguish whole-photo panels, building-only AOIs, automatic hotspots and local post-processing ROIs. Exclude montage gaps. Do not change AOIs after inspecting results to favor an interpretation.

### 3.3 Analyze and preserve results

Submit **Analyze once**. Save the input, settings, AOI geometry or “none,” date, result URL and native report. After interruption, recover existing uploads/results before resubmitting. Previously observed **Re-analyze** behavior clears old results; preserve them and use a new input version for a changed condition.

## 4. Interpreting and Reporting Results

- **Heatmap:** shows predicted attention, not beauty. Red does not mean “more whole”; absent heat does not prove a region is never seen.
- **Hotspots and AOIs:** percentages estimate the likelihood of seeing somewhere within each stated region. Several regions can be seen by the same viewer. These are **not additive attention shares**: do not sum or normalize them into a beauty score. A hotspot value is not the probability of a different AOI.
- **Gaze Sequence:** numbered points indicate predicted order, not a recorded individual scanpath or fixation duration (3M, FAQs).

An entire-image AOI in a separate scan may be near saturation and poorly distinguish buildings. R, color-derived coverage and composite indices require their own cited formulas, thresholds and limitations; they are not native 3M beauty scores. Our implementation choices are not automatically exact replications of the papers.

Submit **original input, preprocessing record, scan settings, native reports and a short interpretation**. Record sources, credits, dimensions, hashes, layout, category, AOIs, date and missing conditions. Verify all numbers and gaze points against native evidence. Label edited presentation figures as composites and retain unchanged reports. Claims about beauty or wholeness require separate evidence.

## 5. Illustrated Examples

### 5.1 Website workflow

![Historical VAS website workflow](assets/handbook-vas-workflow.jpg)

*Figure 1. Historical website workflow from Hongkai Zhang and Bin Jiang’s handbook, p. 5. Interface details and trial allowance are historical, not current service specifications. The example screen shows Packaging; it is not a category recommendation for architectural exteriors. Follow Section 3.1 when selecting your content type.*

### 5.2 Combined and separate analyses

**(a) Combined analysis**

![Combined-analysis teaching example](assets/handbook-combined-scan.jpg)

**(b) Separate analyses**

![Separate-analysis teaching examples](assets/handbook-separate-scans.jpg)

*Figure 2. Combined and separate VAS presentation examples from the same handbook, p. 5. The original photographs and framing are not fully matched, so these figures illustrate analysis formats rather than isolate a scanning-design effect. Percentages and numbered points are retained unchanged; they are not beauty scores or new results from this tutorial.*

## Resources

### Websites

3M VAS Portfolio: https://vas.3m.com/app/portfolio

3M VAS FAQs: https://vas.3m.com/faqs

3M VAS Support: https://www.3m.com/3M/en_US/visual-attention-software-us/support/

3M VAS How it Works: https://vas.3m.com/howitworks

Tutorial and Codex skill repository: [https://github.com/eleanor-wsyy/vas-scanning-tutorial](https://github.com/eleanor-wsyy/vas-scanning-tutorial)

Repository access: private; readers must be signed in with an authorized GitHub account.

Official pages checked 24 October 2026. Image-format and size recommendations come from 3M; comparison controls, non-alteration and evidence archiving are research safeguards.

### References

Alexander C. (2002–2005), *The Nature of Order: An Essay on the Art of Building and the Nature of the Universe*, Center for Environmental Structure: Berkeley, CA.

Berto R., Barbiero G. and Salingaros N. A. (2022), Biophilic design of building façades from an evolutionary psychology framework: Visual Attention Software compared to Perceived Restorativeness, *Visions for Sustainability*, 19, 91–124. https://doi.org/10.13135/2384-8677/7054

Jiang B. and de Rijke C. (2023), Living images: A recursive approach to computing the structural beauty of images or the livingness of space, *Annals of the American Association of Geographers*, 113(6), 1329–1347. https://doi.org/10.1080/24694452.2023.2178376

Lavdas A. A., Salingaros N. A. and Sussman A. (2021), Visual Attention Software: A new tool for understanding the “subliminal” experience of the built environment, *Applied Sciences*, 11(13), 6197. https://doi.org/10.3390/app11136197

Lavdas A. A. and Salingaros N. A. (2022), Architectural beauty: Developing a measurable and objective scale, *Challenges*, 13(2), 56. https://doi.org/10.3390/challe13020056

**Teaching source:** Hongkai Zhang and Bin Jiang, *Living Structure + AI: Four Hands-On Exercises for Exploring and Assessing Wholeness*, especially p. 5 and p. 10. This tutorial supplements that handbook; its authorship is preserved. Figures 1–2 reproduce attributed, unchanged image excerpts from p. 5; original image and interface rights remain with their respective holders.
