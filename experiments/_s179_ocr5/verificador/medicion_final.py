# Medicion final de las cinco pasadas en el panel "Last Month" de MIROVA.
# Supuestos (nombrados en el informe):
#  S1 el panel cubre 35 dias entre los bordes x=275.5 y x=807.5 (rotulos de borde a 35 dias; grilla cada 7 dias = 106.4 px)
#  S2 la estrella verde es la pasada del rotulo "Last Update" (comprobado en octubre por su VRP)
#  S3 triangulo: dato = fila de la base - 1.8 px (calibrado con 1.62 MW Isluga y 1.20 MW Lascar, leidos en la pagina Latest)
import datetime as dt, numpy as np
from PIL import Image
PXD=(807.5-275.5)/35.0
def load(f): return np.asarray(Image.open(f).convert('RGB')).astype(int)
def masks(a):
    R,G,B=a[:,:,0],a[:,:,1],a[:,:,2]; lum=(R+G+B)/3
    neutral=(abs(R-G)<25)&(abs(G-B)<25)
    return neutral&(lum<160), (R>180)&(G<110)&(B<110), (G>180)&(R<120)&(B<120)
def star_x(a):
    dark,red,green=masks(a); cols=np.nonzero(green[112:294].sum(axis=0)>0)[0]; cols=cols[(cols>600)]
    return (cols.min()+cols.max())/2, cols.min(), cols.max()
def yaxis(a,vals_rows):
    # ajuste lineal valor->fila con las lineas de grilla dadas
    rows=np.array([r for r,v in vals_rows],float); vals=np.array([v for r,v in vals_rows],float)
    m,b=np.polyfit(vals,rows,1); return m,b   # fila = m*valor + b
def black_square(a,xp,w=4):
    dark,_,_=masks(a); dark=dark.copy()
    # quitar la linea punteada vertical (rayas de 2 px cada 4 px): columnas oscuras en filas 113,117,121 y claras en 115,119
    for x in range(700,760):
        if dark[113,x] and dark[117,x] and dark[121,x] and not dark[115,x] and not dark[119,x]: dark[:,x]=False
    sub=dark[112:292,int(round(xp))-w:int(round(xp))+w+1]
    ys,xs=np.nonzero(sub); top=ys.min()+112
    xsq=xs[ys<=ys.min()+6]+int(round(xp))-w
    return top+3, (xsq.min()+xsq.max())/2
def black_tri_base(a,xp,ymin=113,ymax=290,w=4):
    dark,_,_=masks(a); x0=int(round(xp))-w; sub=dark[ymin:ymax,x0:x0+2*w+1]
    cnt=sub.sum(axis=1); r=int(np.argmax(cnt)); return ymin+r, int(cnt[r])
def stem_reaches_top(a,xp,w=1):
    dark,_,_=masks(a); x0=int(round(xp))-w
    return [(x,int(dark[112:250,x].sum())) for x in range(x0,x0+2*w+1)]
D='scraper/'
casos=[
 ('Isluga 2026-03-20 05:06',2.21,D+'abr_05-24-00_Isluga_VIIRS375',dt.datetime(2026,4,4,5,48,1),dt.datetime(2026,3,20,5,6),[(126,2.0),(168,1.5),(210,1.0),(252,0.5)]),
 ('Isluga 2026-03-24 05:30',1.51,D+'abr_05-24-00_Isluga_VIIRS375',dt.datetime(2026,4,4,5,48,1),dt.datetime(2026,3,24,5,30),[(126,2.0),(168,1.5),(210,1.0),(252,0.5)]),
 ('Lascar 2026-03-15 05:00',1.54,D+'abr_05-00-01_Lascar_VIIRS375',dt.datetime(2026,4,1,5,0,1),dt.datetime(2026,3,15,5,0),[(169,8.0),(200,6.0),(232,4.0),(263,2.0)]),
 ('Isluga 2026-10-03 05:18',1.62,D+'05-18-00_Isluga_VIIRS375',dt.datetime(2026,10,3,5,36,1),dt.datetime(2026,10,3,5,18),[(152,2.5),(209,1.5),(266,0.5)]),
 ('Lascar 2026-10-01 05:18',1.20,D+'05-18-02_Lascar_VIIRS375',dt.datetime(2026,10,1,6,18,1),dt.datetime(2026,10,1,5,18,2),[(119,8.0),(163,6.0),(207,4.0),(251,2.0)]),
]
DISTGRID=[(147,20.0),(184,15.0),(221,10.0),(258,5.0)]
for nombre,vrp_scr,base,t_star,t_pass,vg in casos:
    av=load(base+'_VRP.png'); ad=load(base+'_Dist.png')
    sxv,_,_=star_x(av); sxd,_,_=star_x(ad)
    dd=(t_star-t_pass).total_seconds()/86400
    xpv=sxv-dd*PXD; xpd=sxd-dd*PXD
    mv,bv=yaxis(av,vg); md,bd=yaxis(ad,DISTGRID)
    ysq,xsq=black_square(ad,xpd)
    dist=(ysq-bd)/md
    print(f'{nombre}: estrella x VRP={sxv} Dist={sxd}; dias antes de la estrella={dd:.3f}; x esperado VRP={xpv:.1f} Dist={xpd:.1f}')
    print(f'   Dist: cuadrado negro centro x={xsq:.1f} (desfase {xsq-xpd:+.1f} px = {(xsq-xpd)/PXD*24:+.1f} h), fila centro={ysq} -> {dist:.1f} km')
    tope=(112-bv)/mv
    reach=stem_reaches_top(av,xpv)
    if max(c for _,c in reach)>=130:
        print(f'   VRP: tallo negro llega al tope del panel (columnas {reach}); tope del eje = {((110.5-bv)/mv):.2f} MW -> VRP > tope, fuera de escala; scraper {vrp_scr}')
    else:
        rb,n=black_tri_base(av,xpv)
        v=((rb-1.8)-bv)/mv
        print(f'   VRP: base del triangulo negro en fila {rb} ({n} px oscuros) -> {v:.2f} MW (1 px = {abs(1/mv):.3f} MW); scraper {vrp_scr}')
