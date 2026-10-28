"""Identify existing native annotations; never predict attention or fabricate numbers."""
from pathlib import Path
import cv2
import numpy as np
ROOT = Path(__file__).resolve().parent.parent
DIGIT_TEMPLATES = {n: [] for n in range(1, 5)}
with np.load(ROOT / 'assets/native_digit_templates.npz', allow_pickle=False) as data:
    for key in data.files:
        DIGIT_TEMPLATES[int(key.split('_')[1])].append(data[key])


def red_mask(a):
 return ((a[:,:,0]>140)&(a[:,:,1]<110)&(a[:,:,2]<110)).astype('uint8')*255

def resolve_font(explicit=None):
 for f in [explicit,r'C:\Windows\Fonts\arial.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/System/Library/Fonts/Supplemental/Arial.ttf']:
  if f and Path(f).is_file():return str(f)
 raise RuntimeError('A Unicode TrueType font is required; pass --font')

def clean_glyph(a,x,y,r=20):
 x,y=int(round(x)),int(round(y));r=int(round(r));x0=max(0,x-r);y0=max(0,y-r)
 p=a[y0:min(a.shape[0],y+r+1),x0:min(a.shape[1],x+r+1)];m=red_mask(p)
 Y,X=np.indices(m.shape);m[(X+x0-x)**2+(Y+y0-y)**2>r*r]=0
 yy,xx=np.where(m>0)
 if not len(xx):return None
 return cv2.resize(m[yy.min():yy.max()+1,xx.min():xx.max()+1],(32,40),interpolation=cv2.INTER_AREA)/255.

def points_from(a, overrides=None):
 if overrides:
  return overrides
 candidates=[]
 for th in [140,195]:
  mask=((a[:,:,0]>th)&(a[:,:,1]<110)&(a[:,:,2]<110)).astype('uint8')*255
  cs=cv2.HoughCircles(mask,cv2.HOUGH_GRADIENT,1,28,param1=80,param2=11,minRadius=15,maxRadius=39)
  if cs is None:continue
  for x,y,r in cs[0]:
   if any((x-p[0])**2+(y-p[1])**2<64 for p in candidates):continue
   g=clean_glyph(a,x,y,min(20,r*.73))
   if g is None:continue
   errors=sorted((min(float(np.mean((g-t)**2)) for t in ts if t is not None),n) for n,ts in DIGIT_TEMPLATES.items())
   Y,X=np.indices(a.shape[:2]);disk=(X-x)**2+(Y-y)**2<(r*.62)**2
   white=float(np.mean(np.all(a[disk]>205,axis=1))) if np.any(disk) else 0
   if white>.4 and errors[0][0]<.27:candidates.append((float(x),float(y),errors[0][1],errors[0][0],white,float(r)))
 points=[]
 for n in range(1,5):
  opts=[p for p in candidates if p[2]==n]
  if not opts:
   ov=next((v for v in (overrides or []) if v['order']==n),None)
   if ov is None:raise ValueError(f'Missing digit {n}: {candidates}')
   points.append(ov);continue
  p=min(opts,key=lambda p:p[3]);points.append({'order':n,'x':p[0],'y':p[1],'glyph_error':p[3],'white_fill_fraction':p[4],'native_radius':p[5]})
 return points


def label_boxes(regions):
    a = np.asarray(regions.convert('RGB'))
    hsv = cv2.cvtColor(a, cv2.COLOR_RGB2HSV)
    mask = (cv2.inRange(hsv, (0, 140, 140), (8, 255, 255)) |
            cv2.inRange(hsv, (170, 140, 140), (180, 255, 255)) |
            cv2.inRange(hsv, (23, 140, 140), (38, 255, 255)) |
            cv2.inRange(hsv, (78, 140, 140), (102, 255, 255)))
    boxes = []
    connected = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    for contour in cv2.findContours(connected, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[0]:
        x, y, w, h = cv2.boundingRect(contour)
        polygon = cv2.approxPolyDP(contour, .03 * cv2.arcLength(contour, True), True)
        if len(polygon) == 4 and 30 <= w <= 100 and 14 <= h <= 42 and 1.3 < w / h < 4 and cv2.contourArea(contour) > .72 * w * h:
            white = np.mean((a[y:y+h, x:x+w, 0] > 215) & (a[y:y+h, x:x+w, 1] > 210) & (a[y:y+h, x:x+w, 2] > 130))
            if white > .2 and not any(abs(x-b[0]) < 5 and abs(y-b[1]) < 5 for b in boxes):
                boxes.append([x, y, w, h])
    white = ((a[:, :, 0] > 205) & (a[:, :, 1] > 200) & (a[:, :, 2] > 125)).astype('uint8') * 255
    white = cv2.morphologyEx(white, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    for contour in cv2.findContours(white, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]:
        x, y, w, h = cv2.boundingRect(contour)
        if 25 <= w <= 100 and 10 <= h <= 38 and 1.3 < w/h < 5 and cv2.contourArea(contour) > .5*w*h:
            border = mask[max(0, y-6):y+h+6, max(0, x-6):x+w+6]
            if np.mean(border > 0) > .12:
                box = [max(0, x-3), max(0, y-3), w+6, h+6]
                if not any(abs(box[0]-b[0]) < 8 and abs(box[1]-b[1]) < 8 for b in boxes):
                    boxes.append(box)
    return sorted(boxes, key=lambda box: (box[1], box[0]))
