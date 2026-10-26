"""VE01-V: nulo de la georreferencia de la miniatura (A110), con el instrumento de la otra sesion (rerun/03, funciones
correl/hp/tifs_noche) pero placebos del MISMO volcan, que tienen la misma textura y la geometria equivocada:
 (a) TIF espejado izquierda-derecha y arriba-abajo y rotado 180 grados (misma estadistica de textura, posicion falsa);
 (b) superficie r(dy, dx) en +-6 px para la miniatura 04:54 contra el mejor TIF: anchura del pico y segundo maximo fuera de +-2 px;
 (c) placebo del punto caliente: z de pasa-alto (miniatura menos mediana 5x5, en MAD) en la posicion de nuestro pixel en las 10
     miniaturas del panel; si fuera textura del terreno saldria alto tambien en las otras pasadas despejadas.
P1: si la georreferencia encajara por textura cualquiera, los espejos darian r parecido al del TIF correcto.
P2: control positivo: el TIF correcto sin espejo (debe reproducir r 0,711 de la otra sesion)."""
import sys, io, numpy as np
sys.path.insert(0, 'rerun')
import comun161 as C
import importlib.util
spec = importlib.util.spec_from_file_location('m03', 'rerun/03_ve01_ve02_png.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
# stdout ya lo envuelve comun161.utf8_stdout() al importar el modulo 03
from scipy.ndimage import median_filter
png = m.bajar('Tupungatito/20260929_122836_VIIRS375_Latest10NTI.png')
tifs = m.tifs_noche('Tupungatito')
print('TIF nocturnos despejados del mismo volcan:', len(tifs))
for col, nom in ((3, '04:54'), (2, '05:18')):
    I, _ = m.miniatura(png, 0, col)
    res = sorted(((m.correl(I, A), f, A) for f, A, b in tifs), key=lambda x: -x[0][0][0])
    (r, dy, dx), r00 = res[0][0]
    print(f'\nminiatura {nom}: TIF correcto (control +) r={r:.3f} en ({dy},{dx}); mediana de los 40 r={np.median([x[0][0][0] for x in res]):.3f}')
    for nombre, fn in (('espejo izq-der', np.fliplr), ('espejo arr-abj', np.flipud), ('rotado 180', lambda a: np.rot90(a, 2)), ('transpuesto', np.transpose)):
        rs = [m.correl(I, fn(A))[0][0] for _, _, A in res[:10]]
        print(f'   placebo {nombre:15s} (10 mejores TIF): r max {max(rs):.3f}, mediana {np.median(rs):.3f}')
    # (b) superficie de r para el mejor TIF
    from scipy.ndimage import zoom
    A = res[0][2]
    Z = zoom(A, (I.shape[0] / A.shape[0], I.shape[1] / A.shape[1]), order=1)
    a, bb = m.hp(Z), m.hp(I)
    S = np.zeros((13, 13))
    for i, ddy in enumerate(range(-6, 7)):
        for j, ddx in enumerate(range(-6, 7)):
            aa = np.roll(np.roll(a, ddy, 0), ddx, 1)[8:-8, 8:-8]
            S[i, j] = np.corrcoef(aa.ravel(), bb[8:-8, 8:-8].ravel())[0, 1]
    lejos = np.ones_like(S, bool); lejos[4:9, 4:9] = False
    i, j = np.unravel_index(np.argmax(np.where(lejos, S, -9)), S.shape)
    print(f'   superficie r: max {S.max():.3f} en ({np.unravel_index(S.argmax(), S.shape)[0]-6},{np.unravel_index(S.argmax(), S.shape)[1]-6}); '
          f'segundo max fuera de +-2 px {S[i, j]:.3f} en ({i-6},{j-6}); r a +-3 px del pico: '
          + ', '.join(f'{S[6+dd if 0<=6+dd<13 else 0, 6]:.2f}' for dd in (-3, 3)))
# (c) placebo del punto caliente en las 10 miniaturas
b = tifs[0][2]
def px(la, lo, dy=-1):
    return int(round((b.top - la) / (b.top - b.bottom) * 150 - 0.5 + dy)), int(round((lo - b.left) / (b.right - b.left) * 150 - 0.5))
yo, xo = px(-33.36927, -69.72791); yc, xc = px(-33.389044, -69.826374)
print(f'\nposicion de nuestro pixel en la miniatura: ({yo},{xo}); crater ({yc},{xc}); bounds TIF {b}')
rot = ['06:36', '06:00', '05:18', '04:54', '28-sep 19:36', '28-sep 19:18', '28-sep 18:42', '28-sep 18:00', '28-sep 17:36', '28-sep 06:54']
for k, nom in enumerate(rot):
    fila, col = divmod(k, 5)
    y0 = 165 if fila == 0 else None
    if fila == 1:
        # segunda fila del panel: se mide su y0 buscando el marco por la misma diferencia que en la fila 0 (rotulo a 152, imagen a 165)
        y0 = 400
    m.FILA_Y0[fila] = y0
    I, _ = m.miniatura(png, fila, col)
    h = I - median_filter(I, size=5, mode='nearest'); mad = np.median(np.abs(h - np.median(h))) * 1.4826
    z = h / mad
    print(f'  {nom:14s} z en nuestro pixel (max 3x3) {z[yo-1:yo+2, xo-1:xo+2].max():6.1f} | en el crater {z[yc-1:yc+2, xc-1:xc+2].max():6.1f} | p99.9 de la miniatura {np.percentile(z, 99.9):5.1f}')
