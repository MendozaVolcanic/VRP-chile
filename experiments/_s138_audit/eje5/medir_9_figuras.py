"""S138 eje 5 - mide la POSICION de la mascara de alerta del autor en las NUEVE figuras del Apendice A.

POR QUE. La bateria de S136 declara "conforme" un positivo cuando publicamos un cumulo con VRP > 0 a
menos de 5 km de la coordenada GVP. Eso no dice si publicamos el objeto que el autor marco: en A2 el
autor detecta a ~9,6 km al E (S137). S137 midio la posicion solo en A2. Aca se mide en los nueve
paneles "ALERT Mask" con un unico procedimiento, con controles de instrumento, y se convierte a
lat/lon con dos centros posibles (GVP del catalogo actual, y Volc_LAT/LON del archivo global de
MIROVA, que es el centro que MIROVA usa para su grilla).

LAS DOS PREGUNTAS DEL INSTRUMENTO.
 1. Si la mascara estuviera en otro lado, esta medicion lo veria? Si: el centroide se calcula sobre
    los pixeles blancos del panel; un panel sintetico con un pixel en una celda conocida debe dar la
    distancia y el rumbo de esa celda (control positivo).
 2. Si el instrumento estuviera muerto, se veria distinto? Si: un panel NEGATIVO (A4, A7, A9) debe dar
    "sin mascara" (0 pixeles blancos), y una escala invertida a proposito debe cambiar el resultado
    (rumbo espejado en N-S; distancia doble con 2 km por celda). Si los controles no cambian el
    resultado, el numero no vale.

GEOMETRIA DE LAS FIGURAS (leida en el PDF, p. 3 y Apendice A): grilla de 51 x 51 celdas de 1 km,
ejes 10..50 de abajo hacia arriba (norte arriba: en A6 el lago Villarrica, que esta al NW, aparece
arriba a la izquierda; en A2 la costa sur aparece abajo; en A5 el valle del Tambo, al E, a la derecha).
La cumbre esta en el centro del panel (celda 26, 26).

READ-ONLY: lee documentacion/sp426.5.pdf y los JSON commiteados de los brazos; escribe SOLO en
experiments/_s138_audit/eje5/out/.
Uso: PYTHONIOENCODING=utf-8 python experiments/_s138_audit/eje5/medir_9_figuras.py
"""
import io
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
RAIZ = HERE.parents[2]
PDF = RAIZ / "documentacion" / "sp426.5.pdf"
OUT = HERE / "out"
DPI = 200
BASE = 110.0     # las cajas de abajo se leyeron sobre el render a 110 dpi (745 x 1075 px)
CELDAS = 51
KM_POR_CELDA = 1.0

# caso, pagina PDF, caja generosa del panel ALERT Mask a 110 dpi (x0, y0, x1, y1), pasada del titulo
# de la figura (leida en el raster de la figura, no en el caption: el caption solo da la fecha).
FIGURAS = [
    ("A1", 18, (285, 745, 415, 900), "2012-01-08 15:15:00"),
    ("A2", 19, (285, 265, 415, 415), "2010-04-07 04:40:00"),
    ("A3", 19, (285, 755, 415, 910), "2009-08-16 19:35:00"),
    ("A4", 20, (285, 270, 415, 420), "2013-07-03 19:30:00"),
    ("A5", 20, (285, 735, 415, 890), "2008-04-03 03:20:00"),
    ("A6", 21, (285, 265, 415, 415), "2009-06-24 05:55:00"),
    ("A7", 21, (285, 745, 415, 900), "2012-11-20 10:40:00"),
    ("A8", 22, (285, 265, 415, 415), "2010-02-08 00:55:00"),
    ("A9", 22, (285, 745, 415, 900), "2010-01-19 01:15:00"),
]

# Centro alternativo: Volc_LAT / Volc_LON del archivo global de MIROVA
# (data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv, primera fila de cada IDvolc; Dubbi no esta).
CENTRO_MIROVA = {
    "A1": (55.978, 160.587), "A2": (63.63, -19.62), "A3": (13.6, 40.67), "A4": None,
    "A5": (-16.355, -70.903), "A6": (-39.42, -71.93), "A7": (55.83, 160.33),
    "A8": (37.734, 15.004), "A9": (38.789, 15.213),
}


def hav(la1, lo1, la2, lo2):
    R = 6371.0088
    p = math.radians
    dla, dlo = p(la2 - la1), p(lo2 - lo1)
    a = math.sin(dla / 2) ** 2 + math.cos(p(la1)) * math.cos(p(la2)) * math.sin(dlo / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def punto_desde(lat, lon, dist_km, rumbo_deg):
    R = 6371.0088
    d = dist_km / R
    br = math.radians(rumbo_deg)
    la1, lo1 = math.radians(lat), math.radians(lon)
    la2 = math.asin(math.sin(la1) * math.cos(d) + math.cos(la1) * math.sin(d) * math.cos(br))
    lo2 = lo1 + math.atan2(math.sin(br) * math.sin(d) * math.cos(la1),
                           math.cos(d) - math.sin(la1) * math.sin(la2))
    return math.degrees(la2), math.degrees(lo2)


def rumbo(lat1, lon1, lat2, lon2):
    p = math.radians
    dlo = p(lon2 - lon1)
    y = math.sin(dlo) * math.cos(p(lat2))
    x = math.cos(p(lat1)) * math.sin(p(lat2)) - math.sin(p(lat1)) * math.cos(p(lat2)) * math.cos(dlo)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def recuadro_oscuro(gris, umbral=60, frac=0.5):
    """Caja que encierra las filas y columnas mayoritariamente oscuras: el marco del panel (y su
    interior si es negro). La barra de color de al lado es oscura solo en su mitad baja, asi que no
    pasa el criterio de fraccion y queda fuera."""
    osc = gris < umbral
    fil = np.where(osc.mean(axis=1) > frac)[0]
    col = np.where(osc.mean(axis=0) > frac)[0]
    if len(fil) < 2 or len(col) < 2:
        return None
    return int(fil.min()), int(fil.max()), int(col.min()), int(col.max())


def caja_panel(gris, umbral=150, ancho_min=120):
    """Caja del panel: la componente conexa mas grande de pixeles no blancos (negro en los positivos,
    gris uniforme en los negativos, mas su marco) cuya caja sea aproximadamente cuadrada. La barra de
    color de al lado y el borde del panel vecino son componentes angostas y quedan fuera.
    (La version 1 usaba filas/columnas mayoritariamente oscuras y fallo: en los negativos el marco es
    fino y anti-aliased, y en tres figuras la caja se comia la barra de color, dando 23 km al E.)"""
    from scipy import ndimage
    lab, n = ndimage.label(gris < umbral)
    mejor = None
    for i, sl in enumerate(ndimage.find_objects(lab), start=1):
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        if w < ancho_min or h < ancho_min or not (0.8 <= w / h <= 1.25):
            continue
        area = w * h
        if mejor is None or area > mejor[0]:
            mejor = (area, sl[0].start, sl[0].stop - 1, sl[1].start, sl[1].stop - 1)
    return None if mejor is None else mejor[1:]


def medir_panel(panel_rgb, margen=5, umbral_blanco=170, km_por_celda=KM_POR_CELDA, norte_arriba=True):
    """Devuelve la posicion del centroide de los pixeles blancos del panel respecto del centro.

    panel_rgb: recorte generoso que contiene el panel ALERT Mask entero.
    """
    g = panel_rgb.mean(axis=2)
    caja = caja_panel(g)
    if caja is None:
        return {"error": "no se encontro el marco del panel"}
    y0, y1, x0, x1 = caja
    interior = panel_rgb[y0 + margen:y1 + 1 - margen, x0 + margen:x1 + 1 - margen]
    gi = interior.mean(axis=2)
    h, w = gi.shape
    blancos = gi > umbral_blanco
    n_px = int(blancos.sum())
    celda_px = (h / CELDAS) * (w / CELDAS)
    res = {"marco_px": [int(x1 - x0 + 1), int(y1 - y0 + 1)], "interior_px": [int(w), int(h)],
           "gris_interior_mediana": round(float(np.median(gi)), 1),
           "n_px_blancos": n_px, "n_celdas_aprox": round(n_px / celda_px, 2)}
    if n_px == 0:
        res.update({"mascara": "sin mascara", "dist_km": None, "rumbo_deg": None,
                    "dx_km": None, "dy_km": None})
        return res
    ys, xs = np.nonzero(blancos)
    xc, yc = xs.mean() + 0.5, ys.mean() + 0.5
    dx_c = (xc - w / 2.0) / w * CELDAS
    dy_c = (h / 2.0 - yc) / h * CELDAS
    if not norte_arriba:
        dy_c = -dy_c
    dx, dy = dx_c * km_por_celda, dy_c * km_por_celda
    dist = math.hypot(dx, dy)
    rmb = (math.degrees(math.atan2(dx, dy)) + 360.0) % 360.0
    # extension de la mascara: caja de los blancos, en celdas
    ext_x = (xs.max() - xs.min() + 1) / w * CELDAS
    ext_y = (ys.max() - ys.min() + 1) / h * CELDAS
    res.update({"mascara": "con mascara", "dx_km": round(dx, 2), "dy_km": round(dy, 2),
                "dist_km": round(dist, 2), "rumbo_deg": round(rmb, 1),
                "extension_celdas": [round(ext_x, 1), round(ext_y, 1)],
                "celda_centroide": [round(xc / w * CELDAS + 0.5, 1), round((h - yc) / h * CELDAS + 0.5, 1)]})
    return res


def panel_sintetico(celda_x, celda_y, tam=306, marco=3):
    """Panel negro con marco y UN pixel blanco del tamano de una celda en (celda_x, celda_y),
    numeradas 1..51 desde la esquina inferior izquierda como en los ejes del autor."""
    img = np.full((tam + 2 * marco, tam + 2 * marco, 3), 255, dtype=np.uint8)
    img[marco:-marco, marco:-marco] = 0
    img[:marco, :] = 0; img[-marco:, :] = 0; img[:, :marco] = 0; img[:, -marco:] = 0
    c = tam / CELDAS
    x0 = int(marco + (celda_x - 1) * c)
    y0 = int(marco + (CELDAS - celda_y) * c)
    img[y0:int(y0 + c), x0:int(x0 + c)] = 255
    return img


def main():
    import fitz
    import PIL.Image as Image
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    import yaml
    casos = {c["caso"]: c for c in yaml.safe_load(
        (RAIZ / "experiments" / "_s136" / "apendice_a.yaml").read_text(encoding="utf-8"))["casos"]}

    print("=== CONTROLES DE INSTRUMENTO (antes de medir nada real) ===")
    controles = {}
    # control positivo: pixel en la celda (36, 26) => 10 km al E, rumbo 90
    m = medir_panel(panel_sintetico(36, 26))
    controles["positivo_36_26"] = m
    ok1 = m["mascara"] == "con mascara" and abs(m["dist_km"] - 10.0) <= 0.6 and abs(m["rumbo_deg"] - 90) <= 3
    print(f"control positivo celda (36,26): dist={m['dist_km']} rumbo={m['rumbo_deg']} n_celdas={m['n_celdas_aprox']} -> {'OK' if ok1 else 'FALLA'}")
    # control positivo 2: celda (26, 36) => 10 km al N, rumbo 0
    m2 = medir_panel(panel_sintetico(26, 36))
    controles["positivo_26_36"] = m2
    ok2 = abs(m2["dist_km"] - 10.0) <= 0.6 and (m2["rumbo_deg"] <= 3 or m2["rumbo_deg"] >= 357)
    print(f"control positivo celda (26,36): dist={m2['dist_km']} rumbo={m2['rumbo_deg']} -> {'OK' if ok2 else 'FALLA'}")
    # escala invertida a proposito: norte abajo => el rumbo del (26,36) debe pasar a ~180
    m3 = medir_panel(panel_sintetico(26, 36), norte_arriba=False)
    controles["norte_abajo_26_36"] = m3
    ok3 = abs(m3["rumbo_deg"] - 180) <= 3
    print(f"control escala invertida N-S: rumbo={m3['rumbo_deg']} (esperado ~180) -> {'OK, el instrumento responde' if ok3 else 'FALLA'}")
    # 2 km por celda => la distancia debe doblarse
    m4 = medir_panel(panel_sintetico(36, 26), km_por_celda=2.0)
    controles["dos_km_por_celda_36_26"] = m4
    ok4 = abs(m4["dist_km"] - 20.0) <= 1.2
    print(f"control 2 km/celda: dist={m4['dist_km']} (esperado ~20) -> {'OK, el instrumento responde' if ok4 else 'FALLA'}")
    # panel vacio
    m5 = medir_panel(panel_sintetico(1, 1)[:, :, :] * 0 + np.array([0, 0, 0], dtype=np.uint8))
    controles["vacio"] = m5
    print(f"control panel sin blancos: {m5.get('mascara', m5)}")
    controles_ok = ok1 and ok2 and ok3 and ok4
    print(f"controles sinteticos: {'TODOS OK' if controles_ok else 'ALGUNO FALLA, no reportar mediciones'}")

    print("\n=== LAS NUEVE FIGURAS ===")
    doc = fitz.open(str(PDF))
    s = DPI / BASE
    res = []
    for caso, pag, caja, pasada in FIGURAS:
        pix = doc[pag - 1].get_pixmap(dpi=DPI)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3]
        x0, y0, x1, y1 = [int(round(c * s)) for c in caja]
        rec = img[y0:y1, x0:x1]
        Image.fromarray(rec).save(OUT / f"{caso}_alert_mask_recorte.png")
        m = medir_panel(rec)
        c = casos[caso]
        fila = {"caso": caso, "name": c["name"], "veredicto_paper": c["veredicto"], "pagina": pag,
                "pasada_figura_utc": pasada, "medicion": m}
        # Posicion del autor en lat/lon, con los dos centros posibles
        if m.get("mascara") == "con mascara":
            gvp = (c["lat"], c["lon"])
            pa_gvp = punto_desde(gvp[0], gvp[1], m["dist_km"], m["rumbo_deg"])
            fila["autor_latlon_centro_gvp"] = [round(pa_gvp[0], 5), round(pa_gvp[1], 5)]
            cm = CENTRO_MIROVA.get(caso)
            if cm:
                pa_m = punto_desde(cm[0], cm[1], m["dist_km"], m["rumbo_deg"])
                fila["autor_latlon_centro_mirova"] = [round(pa_m[0], 5), round(pa_m[1], 5)]
                fila["centro_mirova"] = list(cm)
                fila["gvp_vs_centro_mirova_km"] = round(hav(gvp[0], gvp[1], cm[0], cm[1]), 2)
                fila["autor_dist_a_gvp_si_centro_mirova_km"] = round(hav(pa_m[0], pa_m[1], gvp[0], gvp[1]), 2)
        res.append(fila)
        print(f"{caso} {c['name']:18} {c['veredicto']:10} pasada {pasada}  {m.get('mascara')}  "
              f"dist={m.get('dist_km')} km  rumbo={m.get('rumbo_deg')}  n_celdas~{m.get('n_celdas_aprox')}  "
              f"gris_int={m.get('gris_interior_mediana')}  marco={m.get('marco_px')}")
    # control con datos reales: los tres negativos deben dar "sin mascara"
    neg = [r for r in res if r["veredicto_paper"] == "no_detecta"]
    ctrl_neg = all(r["medicion"].get("mascara") == "sin mascara" for r in neg)
    print(f"\ncontrol negativos reales (A4, A7, A9) sin mascara: {'OK' if ctrl_neg else 'FALLA'}")
    salida = {"controles_sinteticos": controles, "controles_sinteticos_ok": controles_ok,
              "control_negativos_reales_ok": ctrl_neg, "figuras": res,
              "nota": "distancias en km sobre la grilla de 1 km del autor; rumbo desde el norte, "
                      "horario; norte arriba verificado con lago (A6), costa (A2) y valle (A5)"}
    (OUT / "figuras_9.json").write_text(json.dumps(salida, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\nescrito {OUT / 'figuras_9.json'}")


if __name__ == "__main__":
    main()
