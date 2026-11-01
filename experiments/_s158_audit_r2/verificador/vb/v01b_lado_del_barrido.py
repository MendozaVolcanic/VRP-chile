"""VB v01b: firma del lado del barrido. La interpolacion con zoom deja +2 px en la columna 0 y -1 px en la 1353:
el corrimiento hacia el satelite NO es simetrico entre los dos lados de la traza. Si el mecanismo es el que
dice el hallazgo 1, los pares MODIS - VIIRS375 de un lado deben dar ~3x mas que los del otro, y el lado debe
cambiar entre pasadas ascendentes y descendentes (la columna 0 cae al otro lado del suelo).
Si el corrimiento viniera de otra causa (paralaje, fuente distinta), no tiene por que ser asimetrico ni cambiar con la orbita.
Lado: satelite al ESTE del pixel si sensor_azimuth en (0,180). Pasada: dia si solar_zenith < 90.
Prediccion por record: geometria esferica con H=705 km, R=6371 km, beta=1/705 rad, centro en columna 676,5,
delta(c) = 2 - 3c/1353 px; se informa la prediccion suponiendo columna 0 al este y al oeste.
Mismos pares que v01 (<=60 min, <=10 km). Denominador: pares. Ventana: corpus de hoy.
"""
import sys, io, math, runpy, os
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import contextlib
_src = open("v01_modis_vs_viirs_pareado.py", encoding="utf-8").read().split(chr(10) + "resumen(")[0]
_src = _src.replace('sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")', "")
ns = {"__file__": os.path.abspath("v01_modis_vs_viirs_pareado.py")}
exec(compile(_src, "v01", "exec"), ns)
pares = ns["res"]["MODIS"]
import glob, json, os
REPO = ns["REPO"]
# recuperar solar zenith y azimut por (sensor, datetime)
meta = {}
for f in glob.glob(os.path.join(REPO, "data/mirova_equivalent/*.json")):
    for r in json.load(open(f))["records"]:
        if r["sensor"].startswith("MODIS"):
            meta[(os.path.basename(f)[:-5], r["sensor"], r["datetime_utc"])] = (r.get("solar_zenith_deg"), r.get("sensor_azimuth_deg"))
R, H, beta = 6371.0, 705.0, 1.0 / 705.0
def theta_de_z(z):
    return math.asin(math.sin(math.radians(z)) * R / (R + H))
def ancho(th):
    def arc(t):
        return R * (math.asin(min(1.0, (R + H) / R * math.sin(t))) - t)
    return abs(arc(th + beta / 2) - arc(th - beta / 2))
def pred(z, lado_col0):  # lado_col0 True = el pixel esta del lado de la columna 0
    th = theta_de_z(z)
    c = 676.5 - th / beta if lado_col0 else 676.5 + th / beta
    d = 2 - 3 * c / 1353
    return (d if c < 676.5 else -d) * ancho(th)
grupos = {}
for (vol, z, a, p, ac, sen, dt) in pares:
    sz, az = meta[(vol, sen, dt)]
    dia = sz is not None and sz < 90
    este = 0 < az < 180
    grupos.setdefault((sen.split("_")[1], "dia" if dia else "noche", "sat_al_este" if este else "sat_al_oeste"), []).append((z, a))
for k in sorted(grupos):
    s = grupos[k]
    for lo, hi in ((0, 25), (25, 45), (45, 60)):
        ss = [x for x in s if lo <= x[0] < hi]
        if not ss: continue
        zz = np.median([x[0] for x in ss])
        print(f"{k} cenit[{lo},{hi}) n={len(ss)} mediana hacia_satelite={np.median([x[1] for x in ss]):+.2f} km | "
              f"prediccion si pixel del lado col0: {pred(zz, True):+.2f} / del otro lado: {pred(zz, False):+.2f} (cenit mediano {zz:.0f})")
