# -*- coding: utf-8 -*-
"""F2 - libreria comun. Decisiones VERIFICADAS en 00_ y 01_ de esta sesion.

TIMESTAMP DE LA PASADA: se usa SOLO filas donde acquisition_utc existe Y coincide
con el timestamp del nombre de archivo (<=60 s). Medido en 01_: el 14% de las filas
con ambos campos discrepan 1-2 h (misma orbita, granulo distinto) y el 17.6% no
tiene acquisition_utc. Confiar en el nombre en esos casos arriesga emparejar el TIF
con una pasada que no es. Se paga cobertura para no arriesgar el emparejamiento.
Read-only sobre el repo canonico.
"""
import csv, io, json, math, os, re, sys, urllib.request, datetime as dt

RAIZ = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
WT   = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s134-f2"
AQUI = os.path.dirname(os.path.abspath(__file__))
TIFDIR = os.path.abspath(os.path.join(AQUI, "..", "tif"))
BASE = "https://raw.githubusercontent.com/MendozaVolcanic/mirova-tif-archive/main/"
sys.path.insert(0, WT)

RE_FN = re.compile(r"(\d{8})_(\d{6})_([A-Za-z0-9]+)(_lm)?\.tif$")
ALIAS = {"ChillanNevadosde": "NevadosDeChillan"}
IBAND = ("VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21")   # sin sufijo = I-band (A48)

_UTF8 = [False]
def utf8():
    # idempotente: envolver stdout dos veces cierra el primer wrapper
    if _UTF8[0]: return
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    _UTF8[0] = True

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin((p2-p1)/2)**2 +
         math.cos(p1)*math.cos(p2)*math.sin(math.radians(lon2-lon1)/2)**2)
    return 2*R*math.asin(math.sqrt(a))

def parse_utc(s):
    if not s: return None
    try: t = dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError: return None
    return (t.replace(tzinfo=dt.timezone.utc) if t.tzinfo is None
            else t.astimezone(dt.timezone.utc))

def catalogo():
    import yaml
    d = yaml.safe_load(open(os.path.join(RAIZ, "volcanoes.yaml"), encoding="utf-8"))
    return {v["name"]: v for v in d["volcanoes"]}

def indice(estricto=True):
    """Filas del indice con ts de pasada resuelto. estricto=True -> solo filas
    donde nombre y acquisition_utc coinciden (<=60 s)."""
    out = []
    for r in csv.DictReader(open(os.path.join(AQUI, "index.csv"), encoding="utf-8")):
        p = r["tif_path"].replace("\\", "/")
        m = RE_FN.search(p)
        if not m: continue
        tfn = dt.datetime.strptime(m.group(1)+m.group(2), "%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc)
        ta = parse_utc(r["acquisition_utc"])
        concuerda = ta is not None and abs((tfn-ta).total_seconds()) <= 60
        if estricto and not concuerda: continue
        r["ts"] = ta if ta is not None else tfn
        r["concuerda"] = concuerda
        r["variante"] = "lm" if m.group(4) else "last"
        r["vol"] = ALIAS.get(r["volcano"], r["volcano"])
        r["tif_path"] = p
        out.append(r)
    return out

def alertas(vol=None):
    from pipeline.mirova_csv_loader import load_mirova_alertas
    base = os.path.join(RAIZ, "data", "mirova_reference", "mirova_v1_snapshot")
    a = load_mirova_alertas(
        cons_path=os.path.join(base, "registro_vrp_consolidado.csv"),
        ocr_path=os.path.join(base, "registro_vrp_ocr.csv"), volcano=vol)
    for x in a:
        x["_ts"] = dt.datetime.fromtimestamp(int(x["timestamp"]), dt.timezone.utc)
    return a

def records(vol, sensores=None, desde=None):
    p = os.path.join(RAIZ, "data", "mirova_equivalent", vol + ".json")
    out = []
    for r in json.load(open(p, encoding="utf-8"))["records"]:
        t = parse_utc(r.get("datetime_utc"))
        if t is None: continue
        if desde and t < desde: continue
        if sensores and r.get("sensor") not in sensores: continue
        r["_ts"] = t
        out.append(r)
    return out

def bajar(tif_path):
    dst = os.path.join(TIFDIR, tif_path.replace("/", "__"))
    os.makedirs(TIFDIR, exist_ok=True)
    if not os.path.exists(dst) or os.path.getsize(dst) < 1000:
        urllib.request.urlretrieve(BASE + tif_path, dst)
    return dst

def leer_tif(tif_path):
    """(arr, lat, lon) - grillas de centro de celda. Solo POSICION, nunca magnitud (A24)."""
    import numpy as np, rasterio
    with rasterio.open(bajar(tif_path)) as s:
        a = s.read(1).astype(float)
        if s.nodata is not None: a = np.where(a == s.nodata, np.nan, a)
        T, crs = s.transform, str(s.crs)
        h, w = a.shape
        geo = s.crs is not None and s.crs.is_geographic
    j, i = np.meshgrid(np.arange(w), np.arange(h))
    x = T.c + (j+0.5)*T.a + (i+0.5)*T.b
    y = T.f + (j+0.5)*T.d + (i+0.5)*T.e
    if not geo:
        from rasterio.warp import transform as wtr
        lo, la = wtr(crs, "EPSG:4326", x.ravel(), y.ravel())
        return a, np.array(la).reshape(a.shape), np.array(lo).reshape(a.shape), crs
    return a, y, x, crs

def grilla_dist_km(lat, lon, lat0, lon0):
    import numpy as np
    dn = (lat-lat0)*111.320
    de = (lon-lon0)*111.320*math.cos(math.radians(lat0))
    return np.hypot(dn, de)

def mediana(xs):
    xs = sorted(x for x in xs if x is not None and x == x)
    if not xs: return None
    n = len(xs)
    return xs[n//2] if n % 2 else (xs[n//2-1]+xs[n//2])/2
