# Ubica el marco y la grilla del panel "Last Month" (parte superior derecha) de cada PNG.
import sys, glob
from PIL import Image
import numpy as np
for f in sorted(glob.glob('scraper/*Dist.png')+glob.glob('scraper/*VRP.png')+glob.glob('png/*Dist.png')+glob.glob('png/*VRP.png')):
    a=np.asarray(Image.open(f).convert('RGB')).astype(int)
    # region panel superior: y 100..300, x 250..820
    sub=a[100:300,250:830]
    gray=(abs(sub[:,:,0]-sub[:,:,1])<12)&(abs(sub[:,:,1]-sub[:,:,2])<12)
    lum=sub.mean(axis=2)
    # columnas con muchas celdas "no blancas" grises => grilla vertical / marco
    colcount=((lum<235)&gray).sum(axis=0)
    rowcount=((lum<235)&gray).sum(axis=1)
    cols=[(250+i,int(c)) for i,c in enumerate(colcount) if c>150]
    rows=[(100+i,int(c)) for i,c in enumerate(rowcount) if c>400]
    print(f); print('  cols',cols); print('  rows',rows)
