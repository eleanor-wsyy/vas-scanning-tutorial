"""Opt-in R and C estimates from unchanged native exports, never display composites."""
import itertools
import cv2
import numpy as np
from native_io import finite_number, polygon_mask

R_PROTOCOL = {"id": "export-image-R/1.0", "background_coefficient": .30,
              "coverage_value_min": 30, "coverage_saturation_min": 70,
              "red_saturation_min": 160, "red_value_min": 140,
              "red_hue_max": 12, "red_hue_wrap_min": 170,
              "min_component_area": 25, "connectivity": 8,
              "formula": "coverage_percent / (red_spots + non_contiguous_regions)",
              "reference": "Lavdas and Salingaros (2022), DOI 10.3390/challe13020056"}
C_PROTOCOL = {"id": "four-report-C/1.0", "background_coefficient": .30,
              "heatmap_probability_cut": 40, "coverage_value_min": 30,
              "coverage_saturation_min": 70, "min_component_area": 25,
              "hotspot_ROI_overlap_min": .50, "gaze_denominator": 4,
              "formula": "(H_approx + P + G + A) / 4",
              "reference": "Adapted from Ro and Huffman (2025), DOI 10.1080/02697459.2024.2342755"}


def components(mask, minimum=25):
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype('uint8'), 8)
    selected = [i for i in range(1, count) if stats[i, cv2.CC_STAT_AREA] >= minimum]
    return len(selected), np.isin(labels, selected)


def native_residual(images):
    residual = np.clip(np.asarray(images['Heatmap']).astype(float) - .30 * np.asarray(images['Original']).astype(float), 0, 255).astype('uint8')
    return residual, cv2.cvtColor(residual, cv2.COLOR_RGB2HSV)


def measure_r(residual, hsv, roi, params=(30, 160, 140, 25, 12)):
    threshold, saturation, value, minimum, hue = params
    coverage = (residual.max(2) >= threshold) & (hsv[:, :, 1] >= 70) & roi
    red = coverage & ((hsv[:, :, 0] <= hue) | (hsv[:, :, 0] >= 170)) & (hsv[:, :, 1] >= saturation) & (hsv[:, :, 2] >= value)
    regions, coverage = components(coverage, minimum)
    red_spots, red = components(red, minimum)
    percent = 100 * int(coverage.sum()) / int(roi.sum())
    denominator = regions + red_spots
    return {"coverage_percent": percent, "red_spots": red_spots,
            "non_contiguous_regions": regions, "R": percent / denominator if denominator else None,
            "roi_pixels": int(roi.sum()), "coverage_pixels": int(coverage.sum())}


def probability_map(images, review, residual):
    legend = review.get('legend')
    if 'Legend' not in images or not legend or not str(legend.get('evidence', '')).strip():
        raise ValueError('C requires the native legend and a visually verified palette box/range')
    box, endpoints = legend.get('box', []), legend.get('range', [])
    image = images['Legend']
    if len(box) != 4 or not all(isinstance(v, int) for v in box) or not (0 <= box[0] < box[2] <= image.width and 0 <= box[1] < box[3] <= image.height):
        raise ValueError('Invalid native legend palette box')
    if len(endpoints) != 2 or not all(finite_number(v) and 0 <= v <= 100 for v in endpoints) or endpoints[0] == endpoints[1]:
        raise ValueError('Verify the legend probability endpoints and direction')
    palette = np.median(np.asarray(image)[box[1]:box[3], box[0]:box[2]], axis=0).astype('float32')
    if len(palette) > 1024:
        palette = palette[np.linspace(0, len(palette)-1, 1024).astype(int)]
    if len(palette) < 8 or np.mean(cv2.cvtColor(palette.astype('uint8')[None, :, :], cv2.COLOR_RGB2HSV)[0, :, 1] > 40) < .75:
        raise ValueError('Palette box does not describe a sufficiently colored native probability bar')
    palette /= np.maximum(np.linalg.norm(palette, axis=1, keepdims=True), 1e-6)
    vectors = residual.reshape(-1, 3).astype('float32')
    vectors /= np.maximum(np.linalg.norm(vectors, axis=1, keepdims=True), 1e-6)
    probabilities = np.linspace(*endpoints, len(palette))
    result = np.empty(len(vectors), 'float32')
    for i in range(0, len(vectors), 8192):
        result[i:i+8192] = probabilities[np.argmax(vectors[i:i+8192] @ palette.T, axis=1)]
    return result.reshape(residual.shape[:2])


def calculate(images, review, which, loops=None):
    if which not in {'r', 'c', 'both'}:
        raise ValueError('Explicitly request r, c or both; no default metric computation')
    regions = review.get('regions', [])
    if not regions or any(not isinstance(r.get('id'), str) or not r['id'].strip() for r in regions) or len({r['id'] for r in regions}) != len(regions):
        raise ValueError('Metrics require uniquely named regions with explicit native-pixel ROIs')
    residual, hsv = native_residual(images)
    size = images['Regions'].size
    result = {'official_3m_score': False, 'R': [], 'C': [], 'warnings': []}
    probability = probability_map(images, review, residual) if which in {'c', 'both'} else None
    if which in {'c', 'both'}:
        if loops is None or len(loops) != len(review.get('hotspots', [])):
            raise ValueError('Verify the complete native hotspot boundaries for C')
        for hotspot in review['hotspots']:
            value = hotspot.get('probability')
            if not finite_number(value) or not 0 <= value <= 100:
                raise ValueError('C requires each hotspot probability read from native evidence; no guessed values')
        hotspot_masks = [polygon_mask(loop['points'], size) for loop in loops]
    for region in regions:
        if not isinstance(region.get('id'), str) or not region['id'].strip():
            raise ValueError('Region IDs must be nonempty strings')
        roi = polygon_mask(region.get('roi', []), size)
        if which in {'r', 'both'}:
            sensitivity = []
            for params in itertools.product([20,30,40], [120,160], [100,140], [9,25], [12,20,30]):
                sensitivity.append({'parameters': list(params), 'R': measure_r(residual, hsv, roi, params)['R']})
            result['R'].append({'region_id': region['id'], 'protocol': R_PROTOCOL, 'primary': measure_r(residual, hsv, roi), 'sensitivity': sensitivity})
        if which in {'c', 'both'}:
            aoi = region.get('aoi', {})
            a = aoi.get('probability')
            box = aoi.get('box', [])
            if not finite_number(a) or not 0 <= a <= 100 or not str(aoi.get('evidence', '')).strip():
                raise ValueError('C requires a native AOI probability and evidence for each region')
            if len(box) != 4 or not all(finite_number(v) for v in box) or not (0 <= box[0] < box[2] <= size[0] and 0 <= box[1] < box[3] <= size[1]):
                raise ValueError('Record the actual native AOI box, distinct from the local ROI')
            coverage = (residual.max(2) >= 30) & (hsv[:, :, 1] >= 70) & (probability >= 40) & roi
            _, coverage = components(coverage, 25)
            h = 100 * int(coverage.sum()) / int(roi.sum())
            eligible = [spot['probability'] for spot, mask in zip(review['hotspots'], hotspot_masks) if (mask & roi).sum() / mask.sum() >= .5]
            p = max(eligible) if eligible else None
            orders = [point['order'] for point in review['gaze'] if cv2.pointPolygonTest(np.asarray(region['roi'], dtype='float32'), (float(point['x']), float(point['y'])), False) >= 0]
            g = len(orders) * 25
            result['C'].append({'region_id': region['id'], 'protocol': C_PROTOCOL, 'H_approx': h, 'P': p, 'G': g, 'A': a,
                                'C_exploratory': (h+p+g+a)/4 if p is not None else None,
                                'gaze_orders': orders, 'native_AOI': aoi,
                                'null_reason': 'No eligible native hotspot; P and C remain null' if p is None else None})
            if roi.sum() > .95 * roi.size or a >= 95:
                result['warnings'].append(f"{region['id']}: full-frame ROI or high AOI probability may be non-discriminative; not a beauty ranking")
    result['notes'] = ['R and C are researcher-defined export-image estimates, not native 3M beauty scores.',
                       'H is color-derived and threshold-dependent; document deviations from the cited papers.',
                       'Calculations use native images only, never the lightened display PNG.']
    return result
