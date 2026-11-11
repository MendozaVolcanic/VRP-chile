# Diferencia pixel a pixel entre la captura del scraper y la captura posterior del mismo dia.
import sys
from PIL import Image
import numpy as np
a=np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(int); b=np.asarray(Image.open(sys.argv[2]).convert('RGB')).astype(int)
d=(abs(a-b).sum(axis=2)>60)
ys,xs=np.nonzero(d)
print(sys.argv[1],'vs',sys.argv[2],'pixeles distintos:',d.sum())
if d.sum():
    # por panel
    for name,(y0,y1) in (('cabecera',(0,100)),('LastMonth',(100,300)),('LastYear',(340,560))):
        m=(ys>=y0)&(ys<y1)
        if m.sum(): print('  ',name,m.sum(),'x',xs[m].min(),xs[m].max(),'y',ys[m].min(),ys[m].max())
