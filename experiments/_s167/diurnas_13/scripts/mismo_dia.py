# Para cada objetivo: pasadas diurnas del brazo del mismo volcan y dia (pub, disp, posicion) frente a la fila de MIROVA de esa hora.
import sys, io, json, glob, math, csv, unicodedata
from pathlib import Path
from datetime import datetime, timedelta
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = Path("D:/vrp-trabajo/temporales/s167_diurno_lectura"); OUT = Path("D:/vrp-trabajo/temporales/s167_diurnas_13")
sys.path.insert(0, str(BASE/"codigo/scripts")); import os; os.chdir(BASE/"codigo")
import banco_paridad as bp, yaml
cfg = {v["name"]: v for v in yaml.safe_load(open("volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
idx = json.loads((OUT/"brazo_idx.json").read_text(encoding="utf-8"))
ctx = json.loads((OUT/"contexto_13.json").read_text(encoding="utf-8"))
raices = sorted(glob.glob(str(BASE/"corridas/experiments/_s151_ab_diurno/salidas/*")))
def hav(a, b, c, d):
    p1, p2 = math.radians(a), math.radians(c)
    return 2*6371*math.asin(math.sqrt(math.sin((p2-p1)/2)**2+math.cos(p1)*math.cos(p2)*math.sin(math.radians(d-b)/2)**2))
def rumbo(a, b, c, d):
    y = math.sin(math.radians(d-b))*math.cos(math.radians(c)); x = math.cos(math.radians(a))*math.sin(math.radians(c))-math.sin(math.radians(a))*math.cos(math.radians(c))*math.cos(math.radians(d-b))
    return round((math.degrees(math.atan2(y, x))+360) % 360)
def norm(s): return "".join(c for c in unicodedata.normalize("NFD", s) if c.isalnum()).lower()
AL = {norm(k): k for k in cfg}; AL.update({"puyehuecordoncaulle": "PuyehueCordonCaulle", "nevadosdechillan": "NevadosDeChillan"})
ref = []
for fn, canal in (("registro_vrp_consolidado.csv", "CONS"), ("registro_vrp_ocr.csv", "OCR"), ("consolidado_filas_perdidas.csv", "PERD"), ("respaldo_20260408.csv", "RESP")):
    for row in csv.DictReader(open(BASE/"ref"/fn, encoding="utf-8")):
        try: t = datetime.strptime(row["Fecha_Satelite_UTC"][:16], "%Y-%m-%d %H:%M")
        except Exception: continue
        s = row["Sensor"]; b = "MODIS" if s.startswith("MODIS") else ("VIIRS375" if "375" in s else "VIIRS750")
        ref.append((AL.get(norm(row["Volcan"])), b, t, canal, row["Tipo_Registro"], row["VRP_MW"], row["Distancia_km"]))
raw = {}
def rawrec(vol, b, tt):
    if vol not in raw:
        raw[vol] = {}
        for rz in raices:
            p = Path(rz)/"_s154_ab_diurno_k_on"/("%s.json" % vol)
            if p.exists():
                for x in json.loads(p.read_text(encoding="utf-8"))["records"]:
                    raw[vol].setdefault((bp.bucket(x.get("sensor")), x.get("datetime_utc")), x)
    return raw[vol].get((b, tt))
vistos = set()
for c in ctx:
    vol, dia = c["vol"], c["t"][:10]
    if (vol, dia) in vistos: continue
    vistos.add((vol, dia)); v = cfg[vol]
    print("=" * 90); print(vol, dia, "(inner %s km)" % v["inner_radius_km"])
    filas = sorted([(k.split("|")[1], k.split("|")[2], d) for k, d in idx.items() if k.startswith(vol+"|") and k.split("|")[2][:10] == dia and d["es_dia"]], key=lambda z: (z[1], z[0]))
    for b, tt, d in filas:
        t = datetime.strptime(tt, "%Y-%m-%d %H:%M")
        m = [(cn, tp, vr, ds) for vv, bb, tm, cn, tp, vr, ds in ref if vv == vol and bb == b and abs((tm-t).total_seconds()) <= 120]
        r = rawrec(vol, b, tt); pos = ""
        if r and d["pub"] and r.get("final_hotspot_lat") is not None:
            pos = "%.2f km rumbo %d tmax %.1f tbg %.1f nti %.3f" % (hav(v["vent_lat"], v["vent_lon"], r["final_hotspot_lat"], r["final_hotspot_lon"]), rumbo(v["vent_lat"], v["vent_lon"], r["final_hotspot_lat"], r["final_hotspot_lon"]), r.get("t_max_k") or 0, r.get("t_bg_k") or 0, r.get("nti_max") or 0)
        print("  %s %s %s pub=%s disp=%.3f | MIROVA: %s | %s" % (b, tt[11:], (r or {}).get("sensor"), d["pub"], d["disp"] or 0, m if m else "NO LISTADA", pos))
    extra = sorted([(bb, tm.strftime("%H:%M"), cn, tp, vr, ds) for vv, bb, tm, cn, tp, vr, ds in ref if vv == vol and tm.strftime("%Y-%m-%d") == dia and tm.hour >= 12 and bb != "MODIS"
                    and not any(abs((tm-datetime.strptime(tt, "%Y-%m-%d %H:%M")).total_seconds()) <= 120 and b == bb for b, tt, _ in filas)])
    if extra: print("  filas diurnas de MIROVA sin record del brazo:", extra)
# Tupungatito: todas las publicaciones diurnas del brazo en W2-W6 con posicion, y alertas diurnas de MIROVA en la referencia completa
print("=" * 90); print("Tupungatito, publicaciones diurnas del brazo W2-W6")
v = cfg["Tupungatito"]
for k, d in sorted(idx.items()):
    vol, b, tt = k.split("|")
    if vol != "Tupungatito" or not d["es_dia"] or not d["pub"]: continue
    r = rawrec(vol, b, tt)
    print("  ", b, tt, "disp %.3f" % d["disp"], "%.2f km rumbo %d tmax %.1f tbg %.1f" % (hav(v["vent_lat"], v["vent_lon"], r["final_hotspot_lat"], r["final_hotspot_lon"]), rumbo(v["vent_lat"], v["vent_lon"], r["final_hotspot_lat"], r["final_hotspot_lon"]), r.get("t_max_k"), r.get("t_bg_k")))
print("Tupungatito, alertas diurnas (12 a 23 UTC) de MIROVA en toda la referencia")
for vv, bb, tm, cn, tp, vr, ds in sorted(ref, key=lambda z: z[2]):
    if vv == "Tupungatito" and "ALERTA" in tp and 12 <= tm.hour <= 23: print("  ", bb, tm, cn, tp, vr, ds)
print("vent Tupungatito", v["vent_lat"], v["vent_lon"], "centro", v["lat"], v["lon"], "mirova_center", v.get("mirova_center_lat"), v.get("mirova_center_lon"))
