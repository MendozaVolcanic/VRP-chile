"""VE01-V: recorte ampliado x8 de la serie Last Month (x 335..395, y 100..300) de la imagen Distance VIIRS375 de MIROVA,
con regla: grilla horizontal medida en filas 110/147/184/221/258 = 25/20/15/10/5 km (7,4 px/km, cero en y=295);
grilla vertical 382 = 30-Sep (15,2 px/dia entre 382, 488, 595, 701). Imprime, por columna 345..380, las filas con
pixeles rojos o negros saturados (marcadores y tallos) convertidas a km."""
import sys, numpy as np
from PIL import Image
im = Image.open(sys.argv[1]).convert('RGB'); A = np.array(im).astype(int)
R, G, B = A[..., 0], A[..., 1], A[..., 2]
km = lambda y: (295 - y) / 7.4
dia = lambda x: (x - 382) / 15.2   # dias desde 2026-09-30 00:00
for x in range(345, 381):
    rojas = [y for y in range(100, 296) if R[y, x] > 180 and G[y, x] < 120 and B[y, x] < 120]
    negras = [y for y in range(100, 296) if R[y, x] < 110 and G[y, x] < 110 and B[y, x] < 110]
    if rojas or negras:
        f = lambda ys: f'{len(ys)} px, tope y={min(ys)} ({km(min(ys)):.2f} km)' if ys else '-'
        print(f'x {x} (30-Sep {dia(x):+.2f} d): rojo {f(rojas)} | negro {f(negras)}')
im.crop((335, 100, 395, 300)).resize((60 * 8, 200 * 8), Image.NEAREST).save('05b_serie_dist_28_29sep_x8.png')
