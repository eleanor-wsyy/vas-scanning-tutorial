"""Native VAS report workflow: default rendering; R/C only via explicit metrics command."""
import argparse
import hashlib
import io
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from native_io import prepare, load_case, load_review, polygon_mask, read, sha, write_new
from native_annotations import resolve_font
from outline_paths import associate_native_loops, remove_label_occlusions, smooth_closed
from label_layout import place_labels


def hotspot_loops(images, review):
    spots = review.get('hotspots', [])
    loops = [None] * len(spots)
    automatic = []
    for i, spot in enumerate(spots):
        if 'native_contour' in spot:
            points = np.asarray(spot['native_contour'], dtype=float)
            polygon_mask(points, images['Regions'].size)
            if (points < 0).any() or (points[:, 0] >= images['Regions'].width).any() or (points[:, 1] >= images['Regions'].height).any():
                raise ValueError('Verified native hotspot contour extends outside its image')
            loops[i] = {'points': points, 'outer_points': points, 'origin': 'reviewed native contour'}
        else:
            automatic.append(i)
    if len(automatic) > 12:
        raise ValueError("Review native contours explicitly when more than 12 badges require matching")
    if automatic:
        boxes = [spots[i]['source_box'] for i in automatic]
        targets = [spots[i] for i in automatic]
        for i, loop in zip(automatic, associate_native_loops(images['Regions'], boxes, targets)):
            loops[i] = loop
    return loops


def render(case, review_path=None, weight=.45, width=None, output=None, font=None):
    if not isinstance(weight, (float, int)) or not np.isfinite(weight) or not 0 <= weight <= 1:
        raise ValueError('Heatmap blend weight must be between 0 and 1')
    manifest, images, review, review_hash = load_review(case, review_path, annotations=True)
    original, heat = images['Original'], images['Heatmap']
    nw, nh = original.size
    width = width or (1200 if nh > nw else 2048)
    if not isinstance(width, int) or not 200 <= width <= 4096:
        raise ValueError('Output width must be 200–4096 pixels')
    height = round(nh * width / nw)
    if width * height > 12_000_000:
        raise ValueError('Output exceeds 12 megapixels; choose a smaller width')
    size, scale = (width, height), width / nw
    spots, points = review['hotspots'], sorted(review['gaze'], key=lambda point: point['order'])
    boxes = [spot['source_box'] for spot in spots]
    loops = hotspot_loops(images, review)
    base = Image.blend(original, heat, weight).resize(size, Image.Resampling.LANCZOS).convert('RGBA')
    high = Image.new('L', (width*4, height*4), 0)
    draw = ImageDraw.Draw(high)
    outlines = []
    for spot, loop in zip(spots, loops):
        cleaned, connectors = remove_label_occlusions(loop['outer_points'], boxes)
        smoothed, displacement = smooth_closed(cleaned)
        xy = [tuple(round(value*scale*4) for value in point) for point in smoothed]
        draw.line(xy + [xy[0]], fill=255, width=round(3.2*4), joint='curve')
        outlines.append({'source_box': spot['source_box'], 'native_points': np.asarray(loop['outer_points']).tolist(),
                         'label_occlusion_connectors': connectors, 'max_smoothing_displacement_native_px': displacement})
    overlay = Image.new('RGBA', size, '#ffe332')
    overlay.putalpha(high.resize(size, Image.Resampling.LANCZOS))
    base = Image.alpha_composite(base, overlay)
    crops = [images['Regions'].crop((x,y,x+w,y+h)).resize((max(1,round(w*scale)),max(1,round(h*scale))), Image.Resampling.LANCZOS) for x,y,w,h in boxes]
    normalized = [[p['box'][0]/nw, p['box'][1]/nh, p['box'][2]/nw, p['box'][3]/nh] for p in review['panels']]
    layout = {'probability_label_panels': normalized, 'probability_label_targets': spots, 'probability_label_mapping_evidence': review['evidence']}
    placements = place_labels(layout, boxes, [crop.size for crop in crops], (nw,nh), size, points) if boxes else []
    draw = ImageDraw.Draw(base)
    gaze_xy = [(point['x']*scale, point['y']*scale) for point in points]
    draw.line(gaze_xy, fill='#eb1717', width=3, joint='curve')
    for crop, placement in zip(crops, placements):
        if placement['moved']:
            draw.line([tuple(placement['hotspot_anchor_output']), tuple(placement['leader_endpoint'])], fill='#ffe332', width=2)
        base.paste(crop, tuple(placement['destination_box'][:2]))
    draw = ImageDraw.Draw(base)
    radius = 16 if nh > nw else 22
    number_font = ImageFont.truetype(resolve_font(font), 22 if nh > nw else 29)
    for point, (x,y) in zip(points, gaze_xy):
        draw.ellipse((x-radius,y-radius,x+radius,y+radius), fill='white', outline='#d51b1b', width=2)
        draw.text((x,y), str(point['order']), fill='#c81616', font=number_font, anchor='mm')
    path = Path(output) if output else Path(case) / 'figure.png'
    buffer = io.BytesIO()
    base.convert('RGB').save(buffer, format='PNG')
    data = buffer.getvalue()
    if path.exists() and path.read_bytes() != data:
        raise FileExistsError('Existing figure differs; choose a new --output, never overwrite archived results')
    if not path.exists():
        with path.open('xb') as stream:
            stream.write(data)
    result = {'schema_version': 1, 'report_sha256': manifest['report_sha256'], 'review_sha256': review_hash, 'review_file': str((Path(review_path) if review_path else Path(case)/'review.json').resolve()),
              'output_file': str(path.resolve()), 'output_sha256': hashlib.sha256(data).hexdigest(), 'output_size': list(size),
              'display_heatmap_weight': weight, 'display_original_weight': 1-weight,
              'percentages_source': 'Copied native label bitmaps; no OCR values redrawn',
              'gaze': points, 'probability_label_boxes': boxes, 'probability_label_placements': placements,
              'native_outline_paths': outlines, 'footer_added': False, 'metrics_computed': [],
              'state': 'needs_visual_review', 'visual_QA_passed': False,
              'note': 'Blend weight is for the exported heatmap image, not raw saliency opacity.'}
    write_new(path.with_suffix('.composition.json'), result)
    return result


def metrics(case, which, review_path=None, output=None):
    # Import only when the user explicitly requests a calculation.
    from vas_metrics import calculate
    manifest, images, review, review_hash = load_review(case, review_path, annotations=which in {'c', 'both'})
    loops = hotspot_loops(images, review) if which in {'c','both'} else None
    result = calculate(images, review, which, loops)
    result.update(report_sha256=manifest['report_sha256'], review_sha256=review_hash, requested_metrics=which)
    path = Path(output) if output else Path(case) / ('metrics-' + which + '.json')
    write_new(path, result)
    return result


def approve(case, composition, evidence):
    if not evidence.strip():
        raise ValueError('Record final native-versus-figure visual review evidence')
    manifest, _ = load_case(case)
    data = read(composition)
    if data['report_sha256'] != manifest['report_sha256'] or sha(data['output_file']) != data['output_sha256']:
        raise ValueError('Figure or report changed since composition')
    if sha(data['review_file']) != data['review_sha256']:
        raise ValueError('Review changed; re-render or use the exact reviewed record')
    verification = {'report_sha256': data['report_sha256'], 'review_sha256': data['review_sha256'],
                    'output_sha256': data['output_sha256'], 'visual_QA_passed': True, 'evidence': evidence}
    write_new(Path(composition).with_suffix('.verified.json'), verification)
    return verification


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('prepare', help='Import an existing report; produce review candidates, never scan or compute metrics')
    p.add_argument('--report', required=True); p.add_argument('--case', required=True); p.add_argument('--result-url')
    p = commands.add_parser('render', help='Default deliverable: light heatmap + native percentages + ordered gaze points, no R/C')
    p.add_argument('--case', required=True); p.add_argument('--review'); p.add_argument('--heatmap-weight', type=float, default=.45)
    p.add_argument('--width', type=int); p.add_argument('--output'); p.add_argument('--font')
    p = commands.add_parser('metrics', help='Explicit opt-in calculation; never inferred from a rendering request')
    p.add_argument('--case', required=True); p.add_argument('--review'); p.add_argument('--calculate', choices=['r','c','both'], required=True); p.add_argument('--output')
    p = commands.add_parser('approve', help='Record final visual QA after viewing native evidence and the composite')
    p.add_argument('--case', required=True); p.add_argument('--composition', required=True); p.add_argument('--evidence', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'prepare':
            result = prepare(args.report, args.case, args.result_url)
        elif args.command == 'render':
            result = render(args.case, args.review, args.heatmap_weight, args.width, args.output, args.font)
        elif args.command == 'metrics':
            result = metrics(args.case, args.calculate, args.review, args.output)
        else:
            result = approve(args.case, args.composition, args.evidence)
        print({'command': args.command, 'case': args.case, 'status': 'complete', 'metrics_requested': getattr(args,'calculate',None)})
        return 0
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
