# -*- coding: utf-8 -*-
"""COB 08 (S159). Para los 40 granulos nocturnos que CMR sirve (con GEO) y de los que no hay record (clase sin_rec_B de 04),
y para 80 granulos 'ok' de control, baja el poligono del granulo desde CMR y mide cuanto cae el volcan dentro o fuera de la huella
(km al borde, positivo = dentro). Hipotesis: los faltantes son granulos que tocan la caja de +-25 km pero no contienen al
volcan (borde del barrido), asi que no hay pixeles que procesar.
Pregunta 1: si el volcan SIEMPRE cayera dentro, la hipotesis estaria refutada y el control lo mostraria igual: se imprimen
ambos grupos. Pregunta 2: sin poligono = 'SIN DATO', no 'dentro'. Distancias en proyeccion local equirectangular (error < 1 % a esta escala)."""
import sys, io, json, time, math, urllib.parse, urllib.request
from pathlib import Path
import numpy as np, pandas as pd, yaml
from shapely.geometry import Polygon, Point
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
WT = Path(r"C:\vrp-trabajo\s159-pruebas"); HERE = WT / "experiments/_s159/cob"
sys.path.insert(0, str(HERE)); import cmrpub as cmr
VOL = {v["name"]: v for v in yaml.safe_load(open(WT / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
d = pd.read_csv(HERE / "huecos_vs_cmr.csv", parse_dates=["t"])
B = d[d.clase == "sin_rec_B"]
OK = d[d.clase == "ok"].sample(80, random_state=159)
POL = HERE / "_poligonos.json"
cache = json.loads(POL.read_text()) if POL.exists() else {}
last = [0.0]

def poligono(vol, sensor, t):
    k = f"{vol}|{sensor}|{t:%Y%m%d%H%M}"
    if k in cache: return cache[k]
    sn, vs = cmr.PRODUCTOS[sensor][0][0]
    out = None
    for ver in vs:
        v = VOL[vol]; dd = 25 / 111.0
        q = {"short_name": sn, "version": ver, "page_size": "50",
             "temporal": f"{(t - pd.Timedelta(minutes=1)):%Y-%m-%dT%H:%M:%SZ},{(t + pd.Timedelta(minutes=1)):%Y-%m-%dT%H:%M:%SZ}",
             "bounding_box": f"{v['lon']-dd:.5f},{v['lat']-dd:.5f},{v['lon']+dd:.5f},{v['lat']+dd:.5f}"}
        w = 1.0 - (time.time() - last[0])
        if w > 0: time.sleep(w)
        r = json.loads(urllib.request.urlopen(urllib.request.Request(cmr.BASE + "?" + urllib.parse.urlencode(q), headers={"User-Agent": "vrp-chile-audit-s159"}), timeout=90).read())
        last[0] = time.time()
        for e in r["feed"]["entry"]:
            if abs((pd.Timestamp(e["time_start"]).tz_localize(None) - t).total_seconds()) <= 60 and e.get("polygons"):
                out = e["polygons"][0][0]; break
        if out: break
    cache[k] = out; POL.write_text(json.dumps(cache)); return out

def km_dentro(vol, txt):
    if not txt: return None
    a0 = np.array(txt.split(), float).reshape(-1, 2)  # lat lon; aristas = geodesicas (no rectas en lat/lon): se densifican
    from pyproj import Geod
    g = Geod(ellps="WGS84"); pts = []
    for i in range(len(a0) - 1):
        la1, lo1 = a0[i]; la2, lo2 = a0[i + 1]
        pts.append((la1, lo1))
        for lo, la in g.npts(lo1, la1, lo2, la2, 60): pts.append((la, lo))
    a = np.array(pts)
    lat0, lon0 = VOL[vol]["lat"], VOL[vol]["lon"]
    x = (a[:, 1] - lon0) * 111.32 * math.cos(math.radians(lat0)); y = (a[:, 0] - lat0) * 110.57
    pg = Polygon(np.c_[x, y])
    if not pg.is_valid: pg = pg.buffer(0)
    p = Point(0, 0)
    dist = pg.exterior.distance(p) if pg.geom_type == "Polygon" else pg.boundary.distance(p)
    return dist if pg.contains(p) else -dist

res = []
for nom, g in (("sin_rec_B", B), ("ok_control", OK)):
    for _, r in g.iterrows():
        km = km_dentro(r.vol, poligono(r.vol, r.sensor, r.t))
        res.append(dict(grupo=nom, vol=r.vol, sensor=r.sensor, t=r.t, km_borde=km))
R = pd.DataFrame(res); R.to_csv(HERE / "poligonos_resultado.csv", index=False)
for nom, g in R.groupby("grupo"):
    x = g.km_borde.dropna()
    print(f"\n{nom}: n={len(g)} con poligono={len(x)} | volcan DENTRO de la huella: {int((x>0).sum())} | FUERA: {int((x<=0).sum())}")
    print("  km al borde (+ dentro): min %.1f  p10 %.1f  mediana %.1f  p90 %.1f  max %.1f" % tuple(np.percentile(x, [0, 10, 50, 90, 100])))
    print("  dentro a < 25 km del borde: ", int(((x > 0) & (x < 25)).sum()), "| fuera:", int((x <= 0).sum()))
print("\nDETALLE sin_rec_B:"); print(R[R.grupo == "sin_rec_B"].sort_values("t").to_string())
