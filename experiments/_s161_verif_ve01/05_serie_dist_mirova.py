"""VE01-V: lee la serie "Last Month" de la imagen Distance VIIRS375 de MIROVA (Tupungatito, captura 2026-10-23 09:11,
data/png de mirova-tif-archive) y ubica los marcadores alrededor del 28 y 29 de septiembre: tiempo (eje x) y distancia
(eje y), y su color (rojo = <7 km, negro = >7 km segun la leyenda de MIROVA). Canal independiente de la miniatura:
no usa georreferencia.
Calibracion de ejes medida sobre la imagen: se buscan las etiquetas de tick por posicion de las lineas verticales
de grilla (gris) y el cero del eje y (fondo del grafico). Control positivo: la pasada 05:18 del 29-sep, que la TABLA
de MIROVA da a 5,41 km, debe aparecer roja cerca de 5,4 km; y la del 28-sep 05:18 (OCR 5,27 km) tambien.
P1: si la imagen no tuviera marcadores en esa fecha, la lista saldria vacia y se diria."""
import sys, numpy as np
from PIL import Image
from scipy.ndimage import label, center_of_mass
im = np.array(Image.open(sys.argv[1]).convert('RGB')).astype(int)
R, G, B = im[..., 0], im[..., 1], im[..., 2]
# area del grafico Last Month: x 285..800, y 105..300 (medido a ojo en la imagen de 850x600, se imprime para control)
y0, y1, x0, x1 = 100, 300, 280, 800
sub = im[y0:y1, x0:x1]
# lineas de grilla verticales: columnas con muchos pixeles gris claro
gris = (abs(sub[..., 0] - sub[..., 1]) < 8) & (abs(sub[..., 1] - sub[..., 2]) < 8) & (sub[..., 0] > 170) & (sub[..., 0] < 235)
cols = np.where(gris.sum(axis=0) > 120)[0] + x0
print('columnas de grilla vertical (gris):', cols.tolist())
filas = np.where(gris.sum(axis=1) > 300)[0] + y0
print('filas de grilla horizontal (gris):', filas.tolist())
# eje x: la imagen rotula 23-Sep, 30-Sep, 07-Oct, 14-Oct, 21-Oct, 28-Oct; eje y 0,5,...,25
rojo = (R > 200) & (G < 80) & (B < 80)
negro = (R < 90) & (G < 90) & (B < 90)
out = []
for nombre, m in (('rojo', rojo), ('negro', negro)):
    mm = np.zeros_like(m); mm[y0:y1, x0:x1] = m[y0:y1, x0:x1]
    lab, n = label(mm)
    for i in range(1, n + 1):
        ys, xs = np.where(lab == i)
        h, w = ys.max() - ys.min() + 1, xs.max() - xs.min() + 1
        if 5 <= h <= 12 and 5 <= w <= 12:      # marcador circular o cuadrado, no el tallo
            out.append((nombre, xs.mean(), ys.mean(), h, w))
print('marcadores (color, x, y, alto, ancho):')
for o in sorted(out, key=lambda o: o[1]):
    print('  %-5s x %6.1f y %6.1f (%dx%d)' % o)
