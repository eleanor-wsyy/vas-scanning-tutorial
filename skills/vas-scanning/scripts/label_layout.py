"""Place authentic probability bitmaps beside verified hotspots within their panels."""
import math
import cv2


def panel_bounds(run, width, height):
    panels = run.get('probability_label_panels') or run.get('input_panel_bounds')
    if not panels:
        raise ValueError('Record verified normalized panel bounds before placing labels; never assume a 50% split')
    result = []
    for b in panels:
        if len(b) != 4 or not (0 <= b[0] < b[2] <= 1 and 0 <= b[1] < b[3] <= 1):
            raise ValueError('Panel bounds must be normalized [left, top, right, bottom]')
        result.append((math.ceil(b[0]*width), math.ceil(b[1]*height), math.floor(b[2]*width), math.floor(b[3]*height)))
    return result


def overlap(a, b, pad=0):
    return a[0] < b[2]+pad and a[2] > b[0]-pad and a[1] < b[3]+pad and a[3] > b[1]-pad


def distance(point, rect):
    x, y = point
    return math.hypot(max(rect[0]-x, 0, x-rect[2]), max(rect[1]-y, 0, y-rect[3]))


def place_labels(run, boxes, sizes, native_size, output_size, points):
    nw, nh = native_size; width, height = output_size
    sx, sy = width/nw, height/nh
    panels = panel_bounds(run, width, height)
    targets = run.get('probability_label_targets', [])
    if len(targets) != len(boxes) or not run.get('probability_label_mapping_evidence'):
        raise ValueError('Visually map every native label to its hotspot and panel; provide probability_label_targets and evidence')
    gaze = [(p['x']*sx, p['y']*sy) for p in points]
    radius = 16 if width == 1200 else 22
    marker_boxes = [(x-radius-4,y-radius-4,x+radius+4,y+radius+4) for x,y in gaze]
    used_targets = set(); placed = []; records = []; gap = 8
    for box, (cw, ch) in zip(boxes, sizes):
        matches = [(i,t) for i,t in enumerate(targets) if len(t.get('source_box',[])) == 4 and max(abs(a-b) for a,b in zip(box,t['source_box'])) <= 7]
        if len(matches) != 1 or matches[0][0] in used_targets:
            raise ValueError('Label/hotspot mapping missing or ambiguous; recheck native screenshot')
        i,t = matches[0]; used_targets.add(i)
        pi = t['panel_index']
        if not isinstance(pi,int) or not 0 <= pi < len(panels):
            raise ValueError('Invalid hotspot panel index')
        anchor = t['hotspot_anchor']; ax,ay = anchor[0]*sx,anchor[1]*sy
        bounds = panels[pi]
        if not (bounds[0] <= ax <= bounds[2] and bounds[1] <= ay <= bounds[3]):
            raise ValueError('Verified hotspot anchor must be inside its own panel')
        native = (round(max(0,box[0]-2)*sx),round(max(0,box[1]-2)*sy))
        # Keep an already clear nearby label; otherwise search immediately around its actual hotspot.
        candidates = [native]
        for delta in (0, 12, 24, 40):
            d = gap+delta
            candidates += [(ax+d,ay-ch/2),(ax-cw-d,ay-ch/2),
                           (ax-cw/2,ay+d),(ax-cw/2,ay-ch-d),
                           (ax+d,ay+d),(ax-cw-d,ay+d),
                           (ax+d,ay-ch-d),(ax-cw-d,ay-ch-d)]
        choices = []
        for xx,yy in candidates:
            xx,yy = round(xx),round(yy); rect=(xx,yy,xx+cw,yy+ch)
            if not (bounds[0]+3 <= xx and bounds[1]+3 <= yy and rect[2] <= bounds[2]-3 and rect[3] <= bounds[3]-3):
                continue
            dist = distance((ax,ay),rect)
            if dist > 72 or overlap(rect,(ax-3,ay-3,ax+3,ay+3)):
                continue
            if any(overlap(rect,b,4) for b in placed+marker_boxes):
                continue
            # Do not draw red gaze-path segments through the copied probability digits.
            blocked = any(cv2.clipLine((xx-4,yy-4,cw+8,ch+8),tuple(map(round,a)),tuple(map(round,b)))[0] for a,b in zip(gaze,gaze[1:]))
            if blocked:
                continue
            movement=math.hypot(xx-native[0],yy-native[1])
            choices.append((dist+.04*movement,rect))
        if not choices:
            raise ValueError('No clear nearby same-panel position; adjust the verified contour anchor and inspect again')
        rect=min(choices,key=lambda c:c[0])[1];placed.append(rect)
        endpoint=(min(rect[2]-1,max(rect[0],ax)),min(rect[3]-1,max(rect[1],ay)))
        records.append({'source_box':box,'panel_index':pi,'panel_bounds':list(bounds),
                        'hotspot_anchor_native':list(anchor),'hotspot_anchor_output':[ax,ay],
                        'destination_box':list(rect),'leader_endpoint':list(endpoint),
                        'anchor_to_label_gap_px':distance((ax,ay),rect),
                        'moved':rect[:2] != native})
    return records


def validate_placements(comp):
    placements=comp.get('probability_label_placements')
    if not placements or len(placements) != len(comp['probability_label_boxes']):
        raise ValueError('Recompose with verified same-panel label placements before delivery')
    for p in placements:
        x,y,r,b=p['destination_box'];l,t,pr,pb=p['panel_bounds']
        if not (l <= x < r <= pr and t <= y < b <= pb) or p['anchor_to_label_gap_px'] > 72:
            raise ValueError('Probability label crosses panels or is too far from its hotspot')
    if len({tuple(p['source_box']) for p in placements}) != len(placements):
        raise ValueError('Duplicate probability source bitmap')
