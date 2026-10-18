import sys
from PIL import Image
import numpy as np
from scipy import ndimage
f=sys.argv[1]
a=np.asarray(Image.open(f).convert('RGB')).astype(int)
P=a[95:305,240:800]
# y-axis calibration from tick labels: find dark horizontal axis line (bottom of panel) and top
# gridlines: rows where many pixels light-gray (~(235,235,235)) across plot
g=(np.abs(P[:,:,0]-P[:,:,1])<6)&(np.abs(P[:,:,1]-P[:,:,2])<6)&(P[:,:,0]>200)&(P[:,:,0]<245)
rows=[i+95 for i in range(P.shape[0]) if g[i].sum()>250]
print('gridline rows', rows)
grn=(a[:,:,1]>180)&(a[:,:,0]<120)&(a[:,:,2]<120)
grn[:95,:]=False; grn[305:,:]=False; grn[:,:240]=False
lab,n=ndimage.label(grn)
for i in range(1,n+1):
    ys,xs=np.where(lab==i)
    if len(ys)>20: print('green star centroid x=%.1f y=%.1f npix=%d'%(xs.mean(),ys.mean(),len(ys)))
