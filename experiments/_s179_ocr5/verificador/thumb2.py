# Puntos brillantes locales (lum - mediana 9x9) dentro de las dos primeras miniaturas de la pagina Latest.
import sys
from PIL import Image, ImageFilter
import numpy as np
f=sys.argv[1]
im=Image.open(f).convert('L')
a=np.asarray(im).astype(int); med=np.asarray(im.filter(ImageFilter.MedianFilter(9))).astype(int)
rgb=np.asarray(Image.open(f).convert('RGB')).astype(int)
green=(rgb[:,:,1]>200)&(rgb[:,:,0]<90)&(rgb[:,:,2]<90)
for name,(xa,xb) in (('miniatura1',(8,172)),('miniatura2',(173,337))):
    ys,xs=np.nonzero(green[155:325,xa:xb]); x0,x1,y0,y1=xs.min()+xa,xs.max()+xa,ys.min()+155,ys.max()+155
    # interior: quitar 4 px de marco
    X0,X1,Y0,Y1=x0+4,x1-4,y0+4,y1-4
    cx,cy=(X0+X1)/2,(Y0+Y1)/2; hw,hh=(X1-X0)/2,(Y1-Y0)/2
    d=(a-med)[Y0:Y1+1,X0:X1+1]
    print(f,name,'marco',(x0,y0,x1,y1),'centro',(cx,cy),'semiancho',hw,hh)
    idx=np.argsort(d.ravel())[::-1][:10]
    for i in idx:
        y,x=divmod(i,d.shape[1]); px,py=X0+x,Y0+y
        fx,fy=(px-cx)/hw,(py-cy)/hh
        print(f'   x={px} y={py} contraste={d[y,x]} lum={a[py,px]}  dx={fx:+.2f} dy={fy:+.2f} (fraccion del semiancho)  r={np.hypot(fx,fy):.2f}  r*25km={25*np.hypot(fx,fy):.1f}')
