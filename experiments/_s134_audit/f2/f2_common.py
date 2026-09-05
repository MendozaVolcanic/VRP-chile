# -*- coding: utf-8 -*-
"""F2 · utilidades compartidas: catalogo, records, alertas MIROVA, indice de TIF."""
import csv, json, math, os, re, sys, io, datetime as dt
sys.path.insert(0, "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s134-f2")

RAIZ = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
AQUI = os.path.dirname(os.path.abspath(__file__))
IDX = os.path.join(AQUI, "index.csv")

def utf8():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1; dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))

def catalogo():
    import yaml
    d = yaml.safe_load(open(os.path.join(RAIZ, "volcanoes.yaml"), encoding="utf-8"))
    return {v["name"]: v for v in d["volcanoes"]}

def parse_utc(s):
    if not s: return None
    s = s.replace("Z", "+00:00")
    try: t = dt.datetime.fromisoformat(s)
    except ValueError: return None
    if t.tzinfo is None: t = t.replace(tzinfo=dt.timezone.utc)
    return t.astimezone(dt.timezone.utc)

# --- alias del indice de TIF -> stem canonico del proyecto
ALIAS_TIF = {"ChillanNevadosde": "NevadosDeChillan"}

_RE_FN = re.compile(r"(\d{8})_(\d{6})_([A-Za-z0-9]+)(_lm)?\.tif$")

def indice_tif():
    """Devuelve filas del indice con ts resuelto y volcan canonizado."""
    out = []
    for r in csv.DictReader(open(IDX, encoding="utf-8")):
        m = _RE_FN.search(r["tif_path"])
        if not m: continue
        ts_fn = dt.datetime.strptime(m.group(1)+m.group(2), "%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc)
        r["ts_filename"] = ts_fn
        r["ts_acq"] = parse_utc(r["acquisition_utc"])
        r["variante"] = "lm" if m.group(4) else "last"
        r["ts_lm"] = parse_utc(r["last_modified_utc"])
        r["vol"] = ALIAS_TIF.get(r["volcano"], r["volcano"])
        out.append(r)
    return out

def records(vol, sensores=None, desde=None):
    p = os.path.join(RAIZ, "data", "mirova_equivalent", vol + ".json")
    recs = json.load(open(p, encoding="utf-8"))["records"]
    out = []
    for r in recs:
        t = parse_utc(r.get("datetime_utc"))
        if t is None: continue
        if desde and t < desde: continue
        if sensores and r.get("sensor") not in sensores: continue
        r["_ts"] = t
        out.append(r)
    return out

# I-band = VIIRS_<plataforma> sin sufijo (convencion del proyecto, A48)
IBAND = ("VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21")

def alertas(vol=None):
    from pipeline.mirova_csv_loader import load_mirova_alertas
    base = os.path.join(RAIZ, "data", "mirova_reference", "mirova_v1_snapshot")
    a = load_mirova_alertas(
        cons_path=os.path.join(base, "registro_vrp_consolidado.csv"),
        ocr_path=os.path.join(base, "registro_vrp_ocr.csv"),
        volcano=vol)
    for x in a:
        try:
            x["_ts"] = dt.datetime.fromtimestamp(int(x["timestamp"]), dt.timezone.utc)
        except (KeyError, TypeError, ValueError):
            x["_ts"] = parse_utc(str(x.get("fecha_utc") or "").replace(" ", "T"))
    return a

SENSOR_BUCKET = {"VIIRS_SNPP": "VIIRS375", "VIIRS_NOAA20": "VIIRS375", "VIIRS_NOAA21": "VIIRS375"}

def emparejar(vol, desde, bucket="VIIRS375", tol_s=1200):
    """Alertas MIROVA x TIF x nuestro record, emparejadas POR PASADA (+-tol)."""
    idx = [r for r in indice_tif() if r["vol"] == vol and r["sensor"] == bucket]
    recs = records(vol, IBAND if bucket == "VIIRS375" else None, desde)
    out = []
    for a in alertas(vol):
        if a["_ts"] < desde or a["sensor_bucket"] != bucket:
            continue
        t = a["_ts"]
        tifs = sorted(idx, key=lambda r: abs((r["ts_filename"] - t).total_seconds()))
        tif = tifs[0] if tifs and abs((tifs[0]["ts_filename"] - t).total_seconds()) <= tol_s else None
        rs = sorted(recs, key=lambda r: abs((r["_ts"] - t).total_seconds()))
        rec = rs[0] if rs and abs((rs[0]["_ts"] - t).total_seconds()) <= tol_s else None
        out.append({"alerta": a, "tif": tif, "rec": rec})
    return out
