# -*- coding: utf-8 -*-
"""S161: arma los datos del mapa interactivo y las cifras de resumen que cita el README.

1. Fondo satelital: el visor de Artifacts bloquea toda imagen de otro servidor, así que no se pueden pedir teselas en
   línea. Se bajan teselas Sentinel-2 cloudless 2016 de EOX (CC BY 4.0; «Sentinel-2 cloudless - https://s2maps.eu by
   EOX IT Services GmbH (Contains modified Copernicus Sentinel data 2016)») y se pegan en mosaicos JPEG en Web
   Mercator: uno de zoom 12 que cubre el TIF de MIROVA y 22 km alrededor del cráter, y uno de zoom 14 alrededor del
   cráter (y de la fuente de VE-01 o de VE-02). Las teselas quedan en la carpeta temporal; los mosaicos en artefacto/
   (no se commitean: se regeneran con este script).
2. datos_mapa.js: geometría (cráter, centro del TIF, caja y anillo reales de la grilla de MIROVA, radio interno),
   focos con su persistencia mensual (01 y 02), cúmulos publicados por etiqueta de MIROVA (02), VE-01 y VE-02 (02 y 03)
   y los mapas de frecuencia nocturna y diurna de los TIF (01) como imágenes.
3. Cifras (salida 04_construir_mapa_salida.txt): (a) concordancia mensual del cráter entre los TIF de MIROVA (noche) y
   nuestros records VIIRS 375; (b) dónde caen y cuánto se repiten los cúmulos que publicamos lejos del cráter en
   negativos limpios y en pasadas con alerta.
P1 (roto): la concordancia del cráter debe ir en la misma dirección mes a mes en los dos instrumentos si los dos miden
el cráter; P2 (muerto): n por celda impreso.
Uso: python -I 04_construir_mapa.py > 04_construir_mapa_salida.txt
"""
from __future__ import annotations

import base64
import io as _io
import json
import math
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comun161 as C  # noqa: E402

C.utf8_stdout()
AQ = Path(__file__).resolve().parent
ART = AQ / "artefacto"
ART.mkdir(exist_ok=True)
TESELAS = C.SCRATCH / "teselas_eox"
URL = "https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless_3857/default/g/{z}/{y}/{x}.jpg"


def p(*a):
    print(" ".join(str(x) for x in a))


def lonlat_a_tesela(lon, lat, z):
    n = 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def tesela_a_lonlat(x, y, z):
    n = 2 ** z
    lon = x / n * 360 - 180
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    return lon, lat


def mosaico(nombre, z, lat0, lat1, lon0, lon1, calidad=80):
    x0, y0 = lonlat_a_tesela(lon0, lat1, z)
    x1, y1 = lonlat_a_tesela(lon1, lat0, z)
    xs, ys = range(int(x0), int(x1) + 1), range(int(y0), int(y1) + 1)
    img = Image.new("RGB", (256 * len(xs), 256 * len(ys)))
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            f = TESELAS / str(z) / str(y) / f"{x}.jpg"
            if not f.exists():
                f.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run(["curl", "-sSf", "-o", str(f), URL.format(z=z, y=y, x=x)], check=True)
            img.paste(Image.open(f).convert("RGB"), (256 * i, 256 * j))
    out = ART / f"{nombre}.jpg"
    img.save(out, quality=calidad, optimize=True)
    w, n_ = tesela_a_lonlat(xs[0], ys[0], z)
    e, s = tesela_a_lonlat(xs[-1] + 1, ys[-1] + 1, z)
    p(f"  mosaico {out.name}: zoom {z}, {len(xs)} x {len(ys)} teselas, {out.stat().st_size / 1e6:.2f} MB, "
      f"bounds S {s:.4f} N {n_:.4f} W {w:.4f} E {e:.4f}")
    return {"archivo": out.name, "bounds": [[s, w], [n_, e]], "zoom": z}


def caja_km(lat, lon, km):
    dlat = km / 111.195
    dlon = km / (111.195 * math.cos(math.radians(lat)))
    return lat - dlat, lat + dlat, lon - dlon, lon + dlon


def png_b64(path):
    return "data:image/png;base64," + base64.b64encode(Path(path).read_bytes()).decode()


def main():
    tif = json.load(open(AQ / "01_tif_persistencia.json", encoding="utf-8"))
    capas = json.load(open(AQ / "02_capas_mapa.json", encoding="utf-8"))
    rec = pd.read_csv(AQ / "02_records_foco_mes.csv")
    tif_foco = pd.read_csv(AQ / "01_tif_foco_por_tif.csv")
    tif_tif = pd.read_csv(AQ / "01_tif_por_tif.csv")
    sal03 = (AQ / "03_ve01_ve02_png_salida.txt").read_text(encoding="utf-8")
    m = re.search(r"=== VE-01: .*?máximos locales z >= 6: \d+\n\s+z\s+([\d.]+) en px \((\d+),(\d+)\) -> ([-\d.]+) / ([-\d.]+)", sal03, re.S)
    ve01_mirova = dict(z=float(m.group(1)), lat=float(m.group(4)), lon=float(m.group(5)))
    p("VE-01, punto de MIROVA leído de 03:", ve01_mirova)
    datos = {"volcanes": {}, "meses_records": capas["meses"]}
    p("\n1. mosaicos Sentinel-2 cloudless 2016 (EOX, CC BY 4.0)")
    for vol in C.VOLS:
        g = C.GEO[vol]
        vent = g["vent"]
        left, bottom, right, top = tif[vol]["bounds"]
        la0, la1, lo0, lo1 = caja_km(*vent, 22)
        A = mosaico(f"sat_{vol}_z12", 12, min(bottom, la0), max(top, la1), min(left, lo0), max(right, lo1))
        boxes = [caja_km(*vent, 6)]
        if vol == "Tupungatito":
            boxes.append(caja_km(-33.36927, -69.72791, 3))
        if vol == "PuyehueCordonCaulle":
            boxes.append(caja_km(-40.60205, -72.21125, 3))
        B = mosaico(f"sat_{vol}_z14", 14, min(b[0] for b in boxes), max(b[1] for b in boxes),
                    min(b[2] for b in boxes), max(b[3] for b in boxes))
        focos = tif[vol]["focos"]
        tab_tif = tif[vol].get("tabla", {})
        # tablas mensuales de records por sensor
        rv = rec[rec.vol == vol]
        recs_tab = {}
        for sens, d in rv.groupby("sensores"):
            recs_tab[sens] = {fo: {r.mes: [int(r.n_det), int(r.n_pub), int(r.n_pasadas), float(r.nulo_det)] for r in dd.itertuples()}
                              for fo, dd in d.groupby("foco")}
        tif_meses = {fr: {mes: int(n) for mes, n in tif_tif[(tif_tif.vol == vol) & (tif_tif.franja == fr)].groupby("mes").size().items()}
                     for fr in ("noche", "dia")}
        datos["volcanes"][vol] = dict(
            nombre=C.NOMBRE[vol], vent=vent, tif_centro=g["tif_centro"], mirova_center=g["mirova_center"], inner_km=g["inner_km"],
            caja=C.rect_grilla(vol, 30, 36, 30, 36), anillo=C.rect_grilla(vol, 22, 42, 24, 42),
            tif_bounds=[[bottom, left], [top, right]], sat=[A, B],
            frecuencia={fr: png_b64(AQ / f"01_frecuencia_{vol}_{fr}.png") for fr in ("noche", "dia")
                        if (AQ / f"01_frecuencia_{vol}_{fr}.png").exists()},
            focos=[dict(id=fo["id"], nombre=fo["nombre"], lat=fo["lat"], lon=fo["lon"], origen=fo["origen"],
                        dist=round(C.dist_km(*vent, fo["lat"], fo["lon"]), 2),
                        oct=C.octante(C.rumbo(*vent, fo["lat"], fo["lon"]))) for fo in focos],
            tif=tab_tif, tif_meses=tif_meses, records=recs_tab, capas=capas["capas"][vol])
    datos["ve"] = dict(ve01_mirova=ve01_mirova, records=capas["ve"])
    js = "window.DATOS = " + json.dumps(datos, ensure_ascii=False, separators=(",", ":")) + ";\n"
    (ART / "datos_mapa.js").write_text(js, encoding="utf-8")
    p(f"\n  datos_mapa.js: {len(js) / 1e6:.2f} MB")

    p("\n2. (a) cráter mes a mes: TIF de MIROVA de noche (presente / TIF) contra nuestros records VIIRS 375 (detectado / pasadas)")
    for vol in C.VOLS:
        t = tif_foco[(tif_foco.vol == vol) & (tif_foco.foco == "crater") & (tif_foco.franja == "noche") & tif_foco.presente.notna()]
        r = rec[(rec.vol == vol) & (rec.foco == "crater") & (rec.sensores == "VIIRS 375")]
        pares = []
        for mes, s in t.groupby("mes"):
            rr = r[r.mes == mes]
            if len(rr):
                pares.append((mes, 100 * s.presente.mean(), len(s), 100 * rr.n_det.iloc[0] / rr.n_pasadas.iloc[0], int(rr.n_pasadas.iloc[0])))
        p(f"  {vol}: " + "; ".join(f"{mes} TIF {a:.0f} % (n {na}) / nuestro {b:.0f} % (n {nb})" for mes, a, na, b, nb in pares))
        if len(pares) >= 3:
            rho = pd.Series([x[1] for x in pares]).corr(pd.Series([x[3] for x in pares]), method="spearman")
            p(f"    Spearman de los {len(pares)} meses: {rho:.2f}")

    p("\n2. (b) cúmulos publicados: distancia al cráter y repetición (otro cúmulo publicado de la misma etiqueta a <= 1 km)")
    for vol in C.VOLS:
        g = C.GEO[vol]
        cs = capas["capas"][vol]
        for lab in ("neg_limpio", "pos"):
            s = [c for c in cs if c["lab"] == lab]
            if not s:
                continue
            d = np.array([c["dv"] for c in s])
            lejos = [c for c in s if c["dv"] > 2]
            rep = 0
            for c in lejos:
                if any(o is not c and C.dist_km(c["lat"], c["lon"], o["lat"], o["lon"]) <= 1.0 for o in lejos):
                    rep += 1
            bandas = Counter("0-2" if x <= 2 else "2-5" if x <= 5 else "5-10" if x <= 10 else "10-20" if x <= 20 else ">20" for x in d)
            p(f"  {vol} {lab}: n {len(s)}; por distancia al cráter {dict(sorted(bandas.items()))}; a más de 2 km {len(lejos)}, "
              f"de ésos con otro a <= 1 km {rep}; por sensor {dict(Counter(c['s'] for c in s))}")
            if lab == "neg_limpio" and lejos:
                p(f"    a más de 2 km por sensor: {dict(Counter(c['s'] for c in lejos))}; VRP p50 {np.median([c['vrp'] for c in lejos]):.3f} MW, "
                  f"máx {max(c['vrp'] for c in lejos):.2f} MW")


if __name__ == "__main__":
    main()
