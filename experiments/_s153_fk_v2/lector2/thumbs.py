import sys
from PIL import Image
import numpy as np
from scipy import ndimage
f=sys.argv[1]
im=np.asarray(Image.open(f).convert('RGB')).astype(int)
# thumbnail boxes: find green borders? use fixed grid from layout: rows y 163-315 and 342-494 approx, cols start x 13,180,345,511,677
cols=[(13,165),(180,331),(345,496),(511,662),(677,828)]
rows=[(163,315),(342,494)]
for ri,(y0,y1) in enumerate(rows):
    for ci,(x0,x1) in enumerate(cols):
        sub=im[y0+3:y1-3,x0+3:x1-3]
        g=sub.mean(axis=2); sat=sub.max(axis=2)-sub.min(axis=2)
        mask=(g>235)&(sat<25)
        lab,n=ndimage.label(mask)
        cy=(y1-y0)/2; cx=(x1-x0)/2
        out=[]
        for i in range(1,n+1):
            ys,xs=np.where(lab==i)
            if len(ys)<2: continue
            yy=ys.mean()+3; xx=xs.mean()+3
            out.append((len(ys), round(xx-cx,1), round(yy-cy,1)))
        out.sort(reverse=True)
        print(ri,ci,'bright blobs (npix, dx_px east, dy_px south):',out[:6])
