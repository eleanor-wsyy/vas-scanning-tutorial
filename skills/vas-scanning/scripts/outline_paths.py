"""Trace closed native hotspot loops before removing label rectangles.
This changes annotation rendering only: no heatmap, probability or gaze prediction is generated.
"""
import hashlib
import cv2
import numpy as np
from PIL import Image, ImageDraw


def native_candidates(regions, boxes):
    a=np.asarray(regions.convert('RGB'));hsv=cv2.cvtColor(a,cv2.COLOR_RGB2HSV)
    cyan=(a[:,:,0]<110)&(a[:,:,1]>170)&(a[:,:,2]>170)
    masks=[(0,cv2.inRange(hsv,(0,130,100),(10,255,255))|cv2.inRange(hsv,(168,130,100),(180,255,255))),
           (1,cv2.inRange(hsv,(20,100,90),(40,255,255))),
           (2,cyan.astype('uint8')*255)]
    candidates=[]
    for color,mask in masks:
        mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
        cs,hi=cv2.findContours(mask,cv2.RETR_TREE,cv2.CHAIN_APPROX_NONE)
        for n,c in enumerate(cs):
            if hi is None or hi[0,n,3]<0:continue
            area=cv2.contourArea(c);x,y,w,h=cv2.boundingRect(c)
            if area<85 or min(w,h)<9:continue
            if any(x>=lx-6 and y>=ly-6 and x+w<=lx+lw+6 and y+h<=ly+lh+6 for lx,ly,lw,lh in boxes):continue
            candidates.append({'points':c.reshape(-1,2),'outer_points':cs[hi[0,n,3]].reshape(-1,2),'area':area,'color':color,'bounds':[x,y,w,h]})
    # Multiple color thresholds may find the same loop. Keep the larger native loop.
    dedup=[]
    for c in sorted(candidates,key=lambda c:c['area'],reverse=True):
        if any(d['color']==c['color'] and cv2.pointPolygonTest(d['points'].reshape(-1,1,2),tuple(map(float,c['points'].mean(axis=0))),False)>=0 for d in dedup):continue
        dedup.append(c)
    return dedup


def border_color(regions, box):
    a=np.asarray(regions.convert('RGB'));x,y,w,h=box
    roi=a[max(0,y-3):y+h+3,max(0,x-3):x+w+3];hsv=cv2.cvtColor(roi,cv2.COLOR_RGB2HSV)
    masks=[((hsv[:,:,0]<11)|(hsv[:,:,0]>167)),(hsv[:,:,0]>=20)&(hsv[:,:,0]<=40),(hsv[:,:,0]>=70)&(hsv[:,:,0]<=110)]
    return max(range(3),key=lambda i:int(np.sum(masks[i]&(hsv[:,:,1]>110)&(hsv[:,:,2]>100))))


def box_distance(points, box):
    x,y,w,h=box;p=points.astype(float)
    dx=np.maximum(np.maximum(x-p[:,0],p[:,0]-(x+w)),0)
    dy=np.maximum(np.maximum(y-p[:,1],p[:,1]-(y+h)),0)
    return np.hypot(dx,dy)


def associate_native_loops(regions, boxes, targets=None):
    candidates=native_candidates(regions,boxes);n=len(boxes)
    if len(candidates)<n:raise ValueError('Closed native hotspot loops missing: inspect native source; never invent a region')
    colors=[border_color(regions,b) for b in boxes];costs=[]
    for c in candidates:
        row=[]
        for j,b in enumerate(boxes):
            if c['color']!=colors[j]:row.append(float('inf'));continue
            cost=float(box_distance(c['points'],b).min())
            target=next((t for t in (targets or []) if len(t.get('source_box',[]))==4 and max(abs(a-v) for a,v in zip(b,t['source_box']))<=7),None)
            if target:cost+=float(np.linalg.norm(c['points']-np.asarray(target['hotspot_anchor']),axis=1).min())*2
            row.append(cost if cost<160 else float('inf'))
        costs.append(row)
    # Small exact bipartite assignment: one genuine loop for each native numerical tag.
    dp={0:(0.0,[])}
    for ci,row in enumerate(costs):
        new=dict(dp)
        for bits,(cost,assignment) in dp.items():
            for j,v in enumerate(row):
                if bits&(1<<j) or not np.isfinite(v):continue
                nb=bits|(1<<j);nc=cost+v
                if nb not in new or nc<new[nb][0]:new[nb]=(nc,assignment+[(j,ci)])
        dp=new
    full=(1<<n)-1
    if full not in dp:raise ValueError('Cannot associate native loops uniquely; review label/contour mapping')
    selected=[None]*n
    for j,ci in dp[full][1]:selected[j]=candidates[ci]
    return selected


def remove_label_occlusions(points, boxes):
    """Ignore badge-edge detours, joining only segments hidden by known native labels."""
    p=np.asarray(points);bad=np.zeros(len(p),dtype=bool)
    for x,y,w,h in boxes:
        bad|=(p[:,0]>=x-4)&(p[:,0]<=x+w+4)&(p[:,1]>=y-4)&(p[:,1]<=y+h+4)
    if not bad.any():return p,[]
    if bad.all():raise ValueError('Native label obscures the full hotspot: cannot reconstruct an unknown region')
    start=int(np.flatnonzero(~bad)[0]);p=np.roll(p,-start,axis=0);bad=np.roll(bad,-start);records=[];n=len(p);i=1
    while i<n:
        if not bad[i]:i+=1;continue
        first=i
        while i<n and bad[i]:i+=1
        a=p[first-1];b=p[i%n]
        covered=[]
        hidden=p[first:i]
        for box in boxes:
            x,y,w,h=box
            if np.any((hidden[:,0]>=x-4)&(hidden[:,0]<=x+w+4)&(hidden[:,1]>=y-4)&(hidden[:,1]<=y+h+4)):covered.append(box)
        limit=max(np.hypot(box[2]+10,box[3]+10) for box in covered)
        length=float(np.linalg.norm(a-b))
        if length>limit:raise ValueError('Badge gap is too long: do not invent a missing hotspot boundary')
        records.append({'source_label_boxes':covered,'endpoints_native':[a.tolist(),b.tolist()],
                        'connector_length_native_px':length,'method':'Straight local connector only across original badge-occluded boundary'})
    return p[~bad],records


def smooth_closed(points):
    p=np.asarray(points,dtype=float);p=np.vstack([p,p[0]])
    lengths=np.linalg.norm(np.diff(p,axis=0),axis=1);keep=np.r_[True,lengths>0];p=p[keep]
    distance=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
    sample=np.arange(0,distance[-1],1.0)
    xy=np.stack([np.interp(sample,distance,p[:,i]) for i in range(2)],axis=1)
    weights=np.array([.05449,.24420,.40262,.24420,.05449])
    smoothed=sum(w*np.roll(xy,k-2,axis=0) for k,w in enumerate(weights))
    # Geometry changes are sub-pixel/small raster smoothing, not new hotspot extents.
    displacement=float(np.linalg.norm(smoothed-xy,axis=1).max())
    if displacement>2.0:raise ValueError('Smoothing moved native contour by more than two pixels')
    return smoothed,displacement


def draw_native_outline_alpha(regions, boxes, output_size, targets=None):
    loops=associate_native_loops(regions,boxes,targets);width,height=output_size;sx=width/regions.width;sy=height/regions.height;ss=4
    high=Image.new('L',(width*ss,height*ss),0);dr=ImageDraw.Draw(high);records=[]
    stroke=3.2 if width==1200 else 3.8
    for b,c in zip(boxes,loops):
        cleaned,occlusions=remove_label_occlusions(c['outer_points'],boxes);points,displacement=smooth_closed(cleaned);xy=[(round(x*sx*ss),round(y*sy*ss)) for x,y in points]
        dr.line(xy+[xy[0]],fill=255,width=round(stroke*ss),joint='curve')
        records.append({'source_box':b,'native_color_class':c['color'],'native_bounds':c['bounds'],'native_loop_area_px2':c['area'],
                        'native_points':c['outer_points'].tolist(),'label_occlusion_connectors':occlusions,'closed':True,'max_smoothing_displacement_native_px':displacement})
    return high.resize(output_size,Image.Resampling.LANCZOS),records
