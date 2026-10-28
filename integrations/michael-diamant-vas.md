# Existing Michael Diamant workflow

The installed source-specific `michael-diamant-vas` skill was updated locally with the official-guidance and comparison-protocol references from this repository. Its original scripts, assets, provenance matching, native-value preservation and requested figure style were retained.

The update clarifies the official 600 × 600 recommendation; distinguishes AOIs, hotspots and local ROI metrics; keeps old near/far settings experiment-specific; and requires compact resumable checkpoints.

For another installation, add the two references to the existing skill and link them from its entrypoint, or install the self-contained `vas-scanning` skill instead. Do not replace a working source-discovery implementation with this note. The legacy renderer, digit templates, account state and private research artifacts are not distributed here.

## Integrated default rendering

For new scans, use the installed `vas-scanning` native-report tools for the shared default: 0.45 exported-heatmap blend, native percentage bitmaps, yellow contours and small verified gaze points. Do not compute R/C unless the user requests them. Preserve and resume existing batches with their recorded protocol; this update does not silently re-render archives or apply their case-specific repairs to new inputs. The standalone generic skill contains the portable code and references needed for this path.
