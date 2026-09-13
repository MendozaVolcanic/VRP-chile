"""S137 - mide en las figuras del Apendice A de Coppola 2016a el dNTI de fondo del propio autor.

POR QUE. El probe de sigma midio que nuestro dNTI de fondo tiene sigma 0,007 con banda 21 y 0,002 con
banda 22. El de MIROVA nunca se habia medido. Las figuras A2 y A6 traen los paneles dNTI y dETI con
su barra de color: se puede reconstruir el valor de cada celda y estimar la rugosidad del fondo del
autor, en la misma escena y la misma hora que nuestras pasadas.

COMO, y la version 1 que fallo. La primera version armaba la tabla color-valor con los extremos de la
barra y leia el MARCO de la barra como si fuera escala (el control lo delato: la mediana del dNTI,
que por construccion es cero, salio en -0,0007). Esta version:
  1. toma la barra sin su marco (4 filas de margen dentro de la linea negra);
  2. ancla el valor de cada fila a las MARCAS DE GRADUACION medidas en la imagen a 400 dpi, no a los
     bordes: la escala no es simetrica (en A6 dNTI el tope es +0,0116 y el piso -0,01);
  3. asigna cada pixel del panel al color mas cercano de la barra;
  4. ademas del calculo por pixel, toma UNA muestra por celda de la grilla del autor (51 x 51 km),
     porque el reescalado de imprenta mezcla celdas vecinas en los bordes y eso achica la varianza.

CONTROL PRE-REGISTRADO: la mediana del dNTI debe quedar dentro de +-0,0003. Si no, la conversion
sigue mal y el sigma no se reporta como medicion.

LIMITES: el raster de imprenta suaviza (sesgo hacia sigma menor, que el muestreo por celda atenua
pero no elimina), la escena incluye lago o costa (por eso estimadores robustos y una region sin ellos),
y el pixel caliente satura el tope de la escala, asi que su valor es solo una cota inferior.

READ-ONLY: lee documentacion/sp426.5.pdf, escribe en experiments/_s137/out_figuras/.
"""
import io
import json
import sys
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[2]
PDF = RAIZ / "documentacion" / "sp426.5.pdf"
OUT = Path(__file__).resolve().parent / "out_figuras"
DPI = 400
BASE = 160.0          # las cajas de abajo se leyeron sobre el render a 160 dpi
Y_RECORTE_BARRA = 395  # fila (a 160 dpi) donde empieza el recorte en que se midieron las marcas
CELDAS = 51
TOL_MEDIANA = 0.0003

# Marcas de graduacion medidas a 400 dpi sobre el recorte que empieza en Y_RECORTE_BARRA, como
# (fila, valor rotulado). Dos marcas bastan para la recta; la tercera, cuando existe, es control.
# pagina, nombre, caja del panel (160 dpi), columnas de la barra (160 dpi), marcas
PANELES = [
    (19, "A2_dNTI", (140, 398, 318, 598), (326, 356), [(68.5, 0.01), (171.5, 0.005), (377.0, -0.005)]),
    (19, "A2_dETI", (730, 398, 910, 598), (916, 946), [(44.5, 0.015), (129.5, 0.01), (217.0, 0.005)]),
    (21, "A6_dNTI", (140, 398, 318, 598), (326, 356), [(62.0, 0.01), (164.5, 0.005), (270.0, 0.0)]),
    (21, "A6_dETI", (730, 398, 910, 598), (916, 946), [(29.5, 0.01), (140.5, 0.005), (366.5, -0.005)]),
]


def recta_desde_marcas(marcas):
    """Ajuste lineal fila -> valor con todas las marcas. Devuelve (pendiente, ordenada, residuo max)."""
    f = np.array([m[0] for m in marcas])
    v = np.array([m[1] for m in marcas])
    a, b = np.polyfit(f, v, 1)
    return float(a), float(b), float(np.max(np.abs(a * f + b - v)))


def recuadro_oscuro(gris, umbral=60, frac=0.5):
    osc = gris < umbral
    fil = np.where(osc.mean(axis=1) > frac)[0]
    col = np.where(osc.mean(axis=0) > frac)[0]
    if len(fil) < 2 or len(col) < 2:
        return None
    return int(fil.min()), int(fil.max()), int(col.min()), int(col.max())


def interior_panel(panel):
    """Recorta el marco negro grueso: avanza desde el borde hasta que la fila/columna deja de ser negra."""
    g = panel.mean(axis=2)
    marco = recuadro_oscuro(g)
    if marco is None:
        return None
    y0, y1, x0, x1 = marco
    sub = g[y0:y1 + 1, x0:x1 + 1]
    def avanzar(perfil):
        i = 0
        while i < len(perfil) // 4 and perfil[i] < 60:
            i += 1
        return i + 2
    top = avanzar(sub.mean(axis=1))
    bot = avanzar(sub.mean(axis=1)[::-1])
    izq = avanzar(sub.mean(axis=0))
    der = avanzar(sub.mean(axis=0)[::-1])
    return panel[y0 + top:y1 + 1 - bot, x0 + izq:x1 + 1 - der]


def tabla_barra(img, s, cols_barra, marcas):
    y0 = int(Y_RECORTE_BARRA * s)
    y1 = int(600 * s)
    x0, x1 = int((cols_barra[0] - 4) * s), int((cols_barra[1] + 30) * s)
    g = img[y0:y1, x0:x1].mean(axis=2)
    cols = np.where((g < 245).mean(axis=0) > 0.6)[0]
    grupos = np.split(cols, np.where(np.diff(cols) > 1)[0] + 1)
    barra = max(grupos, key=len)
    c = int((barra.min() + barra.max()) // 2)
    filas = np.where(g[:, c] < 250)[0]
    r_top, r_bot = int(filas.min()) + 4, int(filas.max()) - 4
    a, b, resid = recta_desde_marcas(marcas)
    rows = np.arange(r_top, r_bot + 1)
    colores = img[y0 + rows, x0 + c, :].astype(float)
    return colores, a * rows + b, resid, (float(a * r_top + b), float(a * r_bot + b))


def a_valores(rgb, colores, vals):
    p = rgb.reshape(-1, 3).astype(float)
    out = np.empty(len(p))
    for i in range(0, len(p), 20000):
        d = ((p[i:i + 20000, None, :] - colores[None, :, :]) ** 2).sum(axis=2)
        out[i:i + 20000] = vals[d.argmin(axis=1)]
    return out.reshape(rgb.shape[:2])


def por_celda(v, n=CELDAS):
    """Una muestra en el centro de cada celda de la grilla del autor."""
    h, w = v.shape
    ys = ((np.arange(n) + 0.5) * h / n).astype(int)
    xs = ((np.arange(n) + 0.5) * w / n).astype(int)
    return v[np.ix_(ys, xs)]


def estadisticos(x):
    x = np.asarray(x, dtype=float).ravel()
    med = float(np.median(x))
    mad = float(1.4826 * np.median(np.abs(x - med)))
    p16, p84 = np.percentile(x, [16, 84])
    y = x.copy()
    for _ in range(5):  # desvio con recorte iterativo a 3 sigma
        m, sd = y.mean(), y.std()
        y = y[np.abs(y - m) <= 3 * sd]
    return {"mediana": round(med, 5), "sigma_mad": round(mad, 5),
            "sigma_percentil": round(float((p84 - p16) / 2), 5),
            "sigma_recorte3": round(float(y.std()), 5), "n": int(len(x))}


def main():
    import fitz
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(str(PDF))
    s = DPI / BASE
    res = []
    for pag, nombre, caja, cols_barra, marcas in PANELES:
        pix = doc[pag - 1].get_pixmap(dpi=DPI)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3]
        x0, y0, x1, y1 = [int(round(c * s)) for c in caja]
        dentro = interior_panel(img[y0:y1, x0:x1])
        colores, vals, resid, extremos = tabla_barra(img, s, cols_barra, marcas)
        v = a_valores(dentro, colores, vals)
        celdas = por_celda(v)
        h, w = celdas.shape
        # region sin lago ni costa: mitad derecha, filas centrales (en A6 el lago esta arriba a la
        # izquierda y la colada abajo a la izquierda; en A2 la costa esta abajo)
        region = celdas[int(h * 0.15):int(h * 0.75), int(w * 0.45):]
        cerca = celdas[int(h * 0.35):int(h * 0.65), int(w * 0.35):int(w * 0.80)]
        fila = {
            "panel": nombre, "pagina": pag,
            "escala_barra": [round(extremos[1], 5), round(extremos[0], 5)],
            "residuo_marcas": round(resid, 6),
            "pixel": estadisticos(v),
            "celda": estadisticos(celdas),
            "celda_sin_lago_ni_costa": estadisticos(region),
            "max_celda_zona_cumbre_y_alerta": round(float(cerca.max()), 5),
            "tope_escala": round(extremos[0], 5),
        }
        fila["control_mediana_ok"] = abs(fila["celda"]["mediana"]) <= TOL_MEDIANA
        res.append(fila)
        import PIL.Image as Image
        Image.fromarray(dentro).save(OUT / (nombre + "_recorte.png"))
        print(json.dumps(fila, ensure_ascii=False))
    (OUT / "figuras_apendice.json").write_text(json.dumps(res, indent=1, ensure_ascii=False),
                                               encoding="utf-8")
    print("\nReferencia nuestra (probe de sigma, Lascar y Villarrica 2026): sigma dNTI 0,0070-0,0079 "
          "con banda 21, 0,0017-0,0020 con banda 22.")


if __name__ == "__main__":
    main()
