# Busca los pixeles mas brillantes dentro de cada miniatura (marco verde) y su distancia al centro en fraccion del semiancho.
import sys
from PIL import Image
import numpy as np
f=sys.argv[1]; boxes=[tuple(map(int,b.split(','))) for b in sys.argv[2:]]
a=np.asarray(Image.open(f).convert('RGB')).astype(int)
for (x0,y0,x1,y1) in boxes:
    sub=a[y0:y1,x0:x1]; lum=sub.mean(axis=2)
    cx,cy=(x1-x0-1)/2,(y1-y0-1)/2
    idx=np.argsort(lum.ravel())[::-1][:12]
    print(f,(x0,y0,x1,y1),'centro',(cx,cy))
    for i in idx:
        y,x=divmod(i,lum.shape[1]); print('   x',x0+x,'y',y0+y,'lum',round(lum[y,x]),'dx',round((x-cx)/cx,2),'dy',round((y-cy)/cy,2))
