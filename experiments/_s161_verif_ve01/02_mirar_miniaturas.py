"""VE01-V: recorte ampliado de las miniaturas 05:18 (col 2) y 04:54 (col 3) del panel Latest10NTI de MIROVA,
con dos marcas: circulo verde = posicion del crater (vent de volcanoes.yaml) y circulo rojo = nuestro pixel de 04:54,
ambos con la identidad interior = bounds del TIF (corregida dy=-1 como la otra sesion). Ademas, valor de gris en esas
dos posiciones y en su vecindad 3x3, para no depender del ojo.
P1: si la miniatura no tuviera nada en esas posiciones, el valor seria el del fondo (se imprime la mediana del recorte).
P2: control: la 05:18 (MIROVA 0,04 MW, en la tabla a 5,41 km) es el caso contra el que se compara."""
import sys, numpy as np
from PIL import Image, ImageDraw
PNG = sys.argv[1]
im = Image.open(PNG).convert('RGB'); A = np.array(im).astype(float).mean(axis=2)
# bounds del TIF VIIRS375 EPSG:4326 de Tupungatito: centro (-33.4253,-69.7984) segun comun161; se leen de un TIF real
import rasterio, glob
f = sorted(glob.glob(r'C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s144_conteo_tif\_dl_tif\*\data\tif\Tupungatito\20260908_051201_VIIRS375.tif'))[0]
with rasterio.open(f) as d: b = d.bounds; print('TIF', f[-28:],'bounds', b, 'shape', d.shape, 'crs', d.crs)
VENT = (-33.389044, -69.826374); OUR = (-33.36927, -69.72791)
def px(lat, lon, dy=-1):
    fy = (b.top - lat) / (b.top - b.bottom); fx = (lon - b.left) / (b.right - b.left)
    return fy * 150 - 0.5 + dy, fx * 150 - 0.5
y0 = 165
for col, nombre in ((2, '05:18'), (3, '04:54')):
    x0 = 15 + 165 * col
    I = A[y0:y0+150, x0:x0+150]
    med = np.median(I); mad = np.median(np.abs(I - med)) * 1.4826
    print(f'\nminiatura {nombre}: mediana {med:.1f}, MAD {mad:.1f}, p99 {np.percentile(I,99):.1f}, max {I.max():.1f} en {np.unravel_index(I.argmax(), I.shape)}')
    for et, (la, lo) in (('crater', VENT), ('nuestro pixel', OUR)):
        y, x = px(la, lo); yi, xi = int(round(y)), int(round(x))
        v = I[yi-1:yi+2, xi-1:xi+2]
        print(f'  {et}: px ({y:.1f},{x:.1f}) max 3x3 {v.max():.1f} = {(v.max()-med)/mad:+.1f} MAD; valor central {I[yi,xi]:.1f}')
    C = im.crop((x0-2, y0-2, x0+152, y0+152)).resize((154*4, 154*4), Image.NEAREST)
    D = ImageDraw.Draw(C)
    for (la, lo), colr in ((VENT, (0,255,0)), (OUR, (255,0,0))):
        y, x = px(la, lo); cy, cx = (y+2.5)*4, (x+2.5)*4
        D.ellipse((cx-14, cy-14, cx+14, cy+14), outline=colr, width=2)
    C.save(f'02_miniatura_{nombre.replace(":","")}_marcas.png')
