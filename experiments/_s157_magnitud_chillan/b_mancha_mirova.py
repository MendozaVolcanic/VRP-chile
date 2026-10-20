# -*- coding: utf-8 -*-
"""S157, tarea 1.33 (a): ¿la mancha caliente que dibuja MIROVA crece con el ángulo de la pasada?

POR QUÉ. Si MIROVA remuestrea cada gránulo a una malla de celdas de área fija antes de sumar (D17; Coppola
2014 §2.2, Campus 2022 §3.2), un píxel oblicuo, que en el terreno mide hasta ~4,4 veces el nominal, se reparte
en varias celdas: la mancha caliente de su mapa tiene que agrandarse con el cenital y su suma conserva la
energía. Si en cambio MIROVA sumara los píxeles nativos con área nominal (como nosotros), la mancha no
crecería. La tarea 1.14 (§3.2) miró el Npix del OSF de 2025 y no lo vio crecer; aquí se mira directamente el
mapa que MIROVA publicó de Chillán en erupción, en las mismas pasadas de la tabla de a_pasadas.py.

INSTRUMENTO. Las láminas «Latest10NTI» de MIROVA (archivo mendozavolcanic/mirova-tif-archive, data/png) traen
diez miniaturas de 150 x 150 px del mapa de NTI de las últimas pasadas, en escala de grises; el foco caliente
sale blanco puro (R+G+B = 765). Se cuenta, en una ventana de 41 x 41 px centrada en el volcán, cuántos px son
blanco puro. Una miniatura cubre la malla de 50 x 50 km de MIROVA (0,34 km por px; 1.14 y S151 calibraron esa
georreferencia contra GeoTIFF), así que el conteo es un área.

⚠️ VERIFICADOR S157 (H4, REFUTADO como discriminante): un mapa en coordenadas de terreno agranda la mancha
de un píxel oblicuo sume MIROVA el VRP sobre celdas o sobre píxeles nativos, así que este instrumento NO puede
distinguir las dos hipótesis; y el blanco sigue más a la potencia que al área. Se conserva como dato. Texto
original del docstring:

LO QUE NO ES. El blanco puro es el tope de la escala de grises de la lámina, no la máscara de alertados de
MIROVA (A24: la imagen no trae la máscara). Si la escala fuera un estiramiento por percentil, todas las
miniaturas tendrían casi el mismo número de px blancos; si fuera una escala fija en NTI, un píxel oblicuo
(más diluido, NTI más bajo) daría MENOS blanco. Las dos alternativas predicen lo contrario de crecer con el
ángulo. Controles: (1) una misma pasada en dos láminas distintas tiene que dar el mismo conteo; (2) las
pasadas de día y las nubladas se excluyen (NaN en la lámina).

ENTRADA LEÍDA A OJO (lo único no automático): qué pasada es cada miniatura, del rótulo rojo/negro sobre cada
una. Va en PANELES con el md5 de la lámina para que se pueda comprobar abriéndola. El cenital sale de nuestro
record de la misma pasada y sensor (±2 min), y el VRP de MIROVA de la tabla de a_pasadas_salida.json.

Uso: python -I experiments/_s157_magnitud_chillan/b_mancha_mirova.py --png <carpeta con las láminas bajadas>
     (las baja por la API de GitHub si no están; no hace pull del archivo, que pesa 17 GB: memoria S143)
"""
import argparse
import hashlib
import io
import json
import math
import statistics as st
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from PIL import Image

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
REPO_PNG = "data/png/ChillanNevadosde/"
X0 = [15, 180, 345, 510, 675]   # disposición de la lámina, medida en S151 (experiments/_s151_seleccion_mirova)
Y0 = [165, 400]
LADO = 150
MEDIA_VENTANA = 20
KM_POR_PX = 50.0 / LADO

# lámina -> (sensor, [pasada de cada miniatura en orden de lectura; None = día, nublada o sin dato])
PANELES = {
    "20261018_091701_VIIRS750_Latest10NTI.png": ("VIIRS750", [
        "2026-10-18 06:48", "2026-10-18 06:00", "2026-10-18 05:42", "2026-10-18 05:06", None,
        None, None, None, "2026-10-17 06:18", "2026-10-17 06:00"]),
    "20261018_093004_VIIRS375_Latest10NTI.png": ("VIIRS375", [
        "2026-10-18 06:48", "2026-10-18 06:00", "2026-10-18 05:42", "2026-10-18 05:06", None,
        None, None, None, "2026-10-17 06:18", "2026-10-17 06:00"]),
    "20261018_080827_VIIRS750_Latest10NTI.png": ("VIIRS750", [
        "2026-10-18 05:42", "2026-10-18 05:06", None, None, None,
        None, "2026-10-17 06:18", "2026-10-17 06:00", "2026-10-17 05:24", "2026-10-17 04:42"]),
    "20261018_082654_VIIRS375_Latest10NTI.png": ("VIIRS375", [
        "2026-10-18 06:00", "2026-10-18 05:06", None, None, None,
        None, "2026-10-17 06:18", "2026-10-17 06:00", "2026-10-17 05:24", "2026-10-17 04:42"]),
}


def bajar(nombre, carpeta):
    dest = carpeta / nombre
    if not dest.exists():
        b = subprocess.run(["gh", "api", "-H", "Accept: application/vnd.github.raw",
                            f"repos/MendozaVolcanic/mirova-tif-archive/contents/{REPO_PNG}{nombre}"],
                           capture_output=True, check=True).stdout
        dest.write_bytes(b)
    return dest


def miniaturas(path):
    lum = np.asarray(Image.open(path).convert("RGB")).astype(int).sum(axis=2)
    return [lum[y:y + LADO, x:x + LADO] for y in Y0 for x in X0]


def blanco_central(m):
    c = LADO // 2
    v = m[c - MEDIA_VENTANA:c + MEDIA_VENTANA + 1, c - MEDIA_VENTANA:c + MEDIA_VENTANA + 1]
    return int((v >= 765).sum())


def cenital_nuestro(registros, b, pasada):
    t = datetime.strptime(pasada, "%Y-%m-%d %H:%M")
    for r in registros:
        rb = "VIIRS750" if r["sensor"].endswith("_750") else ("VIIRS375" if r["sensor"].startswith("VIIRS") else "MODIS")
        if rb != b:
            continue
        rt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M")
        if abs(rt - t) <= timedelta(minutes=2):
            return r.get("sensor_zenith_deg"), r
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--png", required=True)
    a = ap.parse_args()
    carpeta = Path(a.png)
    carpeta.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(ROOT / "experiments" / "_s131_audit" / "magnitud"))
    from importlib import import_module
    f_modelo = import_module("02_correccion_area_por_angulo").f_modelo
    with open(ROOT / "data" / "mirova_equivalent" / "NevadosDeChillan.json", encoding="utf-8") as fh:
        registros = json.load(fh)["records"]
    tabla = json.loads((AQUI / "a_pasadas_salida.json").read_text(encoding="utf-8"))["pasadas"]
    mir = {(p["pasada"], p["b"]): p for p in tabla}

    filas, laminas = [], {}
    for nombre, (b, pasadas) in PANELES.items():
        p = bajar(nombre, carpeta)
        laminas[nombre] = hashlib.md5(p.read_bytes()).hexdigest()
        for i, (m, pas) in enumerate(zip(miniaturas(p), pasadas)):
            if pas is None:
                continue
            z, rec = cenital_nuestro(registros, b, pas)
            t = mir.get((pas, b))
            filas.append({"lamina": nombre, "miniatura": i, "b": b, "pasada": pas, "cenital": z,
                          "px_blancos": blanco_central(m), "area_km2": blanco_central(m) * KM_POR_PX ** 2,
                          "f_area": f_modelo(z) if z is not None else None,
                          "M": t["M"] if t else None, "nuestro_D": t["D"] if t else None,
                          "nuestros_alertados_inner": t["n_dentro"] if t else None})

    # control 1: una misma pasada en dos láminas
    dup = {}
    for f in filas:
        dup.setdefault((f["b"], f["pasada"]), []).append(f["px_blancos"])
    control = {f"{k[0]} {k[1]}": v for k, v in dup.items() if len(v) > 1}

    # una fila por (sensor, pasada): mediana de las láminas
    unicas = {}
    for f in filas:
        unicas.setdefault((f["b"], f["pasada"]), f)
    res = []
    for b in ("VIIRS375", "VIIRS750"):
        g = sorted([dict(f, px_blancos=st.median(dup[(f["b"], f["pasada"])]), area_km2=st.median(dup[(f["b"], f["pasada"])]) * KM_POR_PX ** 2) for k, f in unicas.items() if k[0] == b],
                   key=lambda f: f["cenital"] or 0)
        nadir = [f["px_blancos"] for f in g if f["cenital"] is not None and f["cenital"] < 30]
        base = st.median(nadir) if nadir else None
        for f in g:
            f["crecimiento_vs_nadir"] = (f["px_blancos"] / base) if base else None
            res.append(f)
        # El blanco puro es el tope de la escala: una pasada débil deja menos blanco aunque su píxel sea grande.
        # Por eso la pendiente se da también sólo con las pasadas de potencia parecida (MIROVA 9 MW o más).
        for etiqueta, sub in (("todas", g), ("MIROVA>=9MW", [f for f in g if (f["M"] or 0) >= 9.0])):
            sub = [f for f in sub if f["px_blancos"] > 0 and f["f_area"]]
            if len(sub) < 4:
                continue
            xs = [math.log(f["f_area"]) for f in sub]
            ys = [math.log(f["px_blancos"]) for f in sub]
            mx, my = st.mean(xs), st.mean(ys)
            pend = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
            res.append({"b": b, "subconjunto": etiqueta, "pendiente_log_px_vs_log_f_area": pend, "n": len(xs)})

    out = {"meta": {"laminas_md5": laminas, "km_por_px": KM_POR_PX, "ventana_px": 2 * MEDIA_VENTANA + 1,
                    "control_misma_pasada_dos_laminas": control}, "filas": res}
    (AQUI / "b_mancha_mirova_salida.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    L = [f"láminas (md5): {json.dumps(laminas)}",
         f"control, misma pasada en dos láminas (px blancos): {json.dumps(control)}", "",
         "sensor    pasada            cenital f_area | px_blancos  km2   x_nadir | MIROVA MW  nuestro MW  n_nuestros"]
    for f in res:
        if "pendiente_log_px_vs_log_f_area" in f:
            L.append(f"  {f['b']} ({f['subconjunto']}): pendiente log(px blancos) contra log(f_area) = {f['pendiente_log_px_vs_log_f_area']:.2f} "
                     f"(1 = la mancha crece como el área del píxel; 0 = no crece), n {f['n']}")
            continue
        fm = lambda v, s: (s % v) if v is not None else "  -  "  # noqa: E731
        L.append("%-8s  %s  %5s  %5s | %5.1f  %6.2f  %5s | %6s  %6s  %3s" % (
            f["b"], f["pasada"], fm(f["cenital"], "%5.1f"), fm(f["f_area"], "%5.2f"), f["px_blancos"],
            f["area_km2"], fm(f["crecimiento_vs_nadir"], "%5.2f"), fm(f["M"], "%6.2f"), fm(f["nuestro_D"], "%6.2f"),
            fm(f["nuestros_alertados_inner"], "%3d")))
    txt = "\n".join(L)
    (AQUI / "b_mancha_mirova_salida.txt").write_text(txt + "\n", encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
