# -*- coding: utf-8 -*-
"""VERIFICADOR S134 F1 - read-only. Reusa el modulo del auditor y agrega controles propios."""
import io, sys, os, json, math, importlib.util
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import numpy as np
from scipy.stats import spearmanr
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
sys.path.insert(0, ROOT)
spec = importlib.util.spec_from_file_location("f1", os.path.join(HERE, "f1_posicion_magnitud_paridad.py"))
f1 = importlib.util.module_from_spec(spec)
sys.argv = ["x"]
spec.loader.exec_module(f1)  # f1 ya envuelve sys.stdout en UTF-8; no reasignarlo (cierra el buffer)

DESDE = "2026-04-01"
anclas, inner, faltan = f1.cargar_anclas("vent")
anclas_cat, _, _ = f1.cargar_anclas("catalogo")
descr, raw_by_key = [], {}
for vol in f1.TIER:
    recs, info = f1.cargar_records(vol, DESDE)
    for r in recs:
        d = f1.describir(r, vol, anclas[vol], inner[vol], anclas_cat[vol])
        descr.append(d)
        raw_by_key[(vol, r["sensor"], r["granule"])] = r
med = lambda xs: float(np.median(xs)) if len(xs) else None

print("=== V1 . divergencia con el frontend: distance_class falsy / sin primary_cluster ===")
c_nopc = c_null_dc = c_null_dc_pub = 0
for (vol, sen, gr), r in raw_by_key.items():
    pc = r.get("primary_cluster")
    dc = r.get("distance_class")
    if not pc:
        v = f1.fnum(r.get("vrp_mw")) or f1.fnum(r.get("vrp_mir_mw")) or 0
        if v > 0:
            c_nopc += 1
    elif not dc:
        c_null_dc += 1
        cd = f1.fnum(pc.get("centroid_dist_km"))
        if (f1.fnum(pc.get("vrp_mw")) or 0) > 0 and not (cd is not None and cd > inner[vol]):
            c_null_dc_pub += 1
print("  sin primary_cluster PERO con vrp_mw/vrp_mir_mw>0 (frontend publica, script da 0): %d" % c_nopc)
print("  con pc pero distance_class falsy: %d (de los cuales el frontend publicaria: %d)" % (c_null_dc, c_null_dc_pub))
print("  distance_class valores: %s" % dict(Counter(str(r.get("distance_class")) for r in raw_by_key.values())))

alertas = [a for a in f1.load_mirova_alertas(cons_path=f1.CONS, ocr_path=f1.OCR)
           if a["volcano"] in f1.TIER and a["sensor_bucket"] in f1.SENSORES
           and (a["fecha_utc"] or "")[:10] >= DESDE and (a["vrp_mw"] or 0) > 0]
fin_mir = max(a["fecha_utc"] for a in alertas)
descr_par = [o for o in descr if o["datetime_utc"] <= fin_mir]
pares, ours_sin, mir_sin_pasada, fn, amb = f1.parear(descr_par, alertas, 20.0)
print("")
print("=== V2 . ambiguedad del pareo: %d alertas con >=2 granules a +-20 min (de %d) ===" % (amb, len(alertas)))
at = defaultdict(list)
for a in alertas:
    at[(a["volcano"], a["sensor_bucket"])].append(f1.t_mir(a))
n_sib = sum(1 for o in ours_sin if any(abs((o["t"] - x).total_seconds()) <= 1200 for x in at[(o["vol"], o["bucket"])]))
tot375 = sum(1 for o in ours_sin if o["bucket"] == "VIIRS375")
n_sib375 = sum(1 for o in ours_sin if o["bucket"] == "VIIRS375" and any(abs((o["t"] - x).total_seconds()) <= 1200 for x in at[(o["vol"], o["bucket"])]))
print("  'nuestros sin MIROVA' que SI estan a +-20 min de una alerta (hermanos no elegidos): %d de %d . V375: %d de %d" % (n_sib, len(ours_sin), n_sib375, tot375))

print("")
print("=== V3 . H2 sesgo de seleccion: 'sin MIROVA' estratificado por MAGNITUD publicada ===")
p375 = [p for p in pares if p["bucket"] == "VIIRS375"]
s375 = [o for o in ours_sin if o["bucket"] == "VIIRS375"]
print("  pares V375 mag_pub mediana %.3f | sin MIROVA %.3f" % (med([p["mag_pub"] for p in p375]), med([o["mag_pub"] for o in s375])))
for lo, hi, lab in [(0, 0.1, "<0.1 MW"), (0.1, 0.3, "0.1-0.3"), (0.3, 1, "0.3-1"), (1, 3, "1-3"), (3, 1e9, ">3")]:
    a = [p["d_crater"] for p in p375 if lo <= p["mag_pub"] < hi and p["d_crater"] is not None]
    b = [o["d_crater"] for o in s375 if lo <= o["mag_pub"] < hi and o["d_crater"] is not None]
    fa = round(sum(1 for d in a if d <= 0.5) / len(a), 2) if a else None
    fb = round(sum(1 for d in b if d <= 0.5) / len(b), 2) if b else None
    print("   %-9s pares n=%4d d_med=%s <=0.5:%s | sinMIR n=%4d d_med=%s <=0.5:%s" % (
        lab, len(a), round(med(a), 2) if a else None, fa, len(b), round(med(b), 2) if b else None, fb))
print("  mismo corte por VOLCAN:")
for vol in ("Villarrica", "Chaiten", "Tupungatito", "PuyehueCordonCaulle", "PlanchonPeteroa"):
    for lo, hi, lab in [(0, 0.3, "<0.3 MW"), (0.3, 1e9, ">=0.3 MW")]:
        a = [p["d_crater"] for p in p375 if p["vol"] == vol and lo <= p["mag_pub"] < hi]
        b = [o["d_crater"] for o in s375 if o["vol"] == vol and lo <= o["mag_pub"] < hi]
        print("   %-20s %-9s pares n=%3d med=%s | sinMIR n=%3d med=%s" % (
            vol, lab, len(a), round(med(a), 2) if a else None, len(b), round(med(b), 2) if b else None))

print("")
print("=== V4 . H3 confound: n_anomaly_pixels vs NUESTRA magnitud y vs la de MIROVA por separado ===")
for s in ("VIIRS375", "VIIRS750"):
    ps = [p for p in pares if p["bucket"] == s]
    print("  [%s]" % s)
    for lo, hi, lab in [(1, 2, "1 px"), (2, 4, "2-3"), (4, 10, "4-9"), (10, 1e9, ">=10")]:
        q = [p for p in ps if lo <= p["n_anomaly_pixels"] < hi]
        if not q:
            continue
        print("    %-5s n=%4d razon=%s | NUESTRA=%s | MIROVA=%s | pc.n_pixels=%s" % (
            lab, len(q), round(med([x["razon_pub"] for x in q]), 3), round(med([x["mag_pub"] for x in q]), 3),
            round(med([x["mir_vrp"] for x in q]), 3), med([x["n_pixels"] for x in q if x["n_pixels"] is not None])))
    r1 = spearmanr([p["n_anomaly_pixels"] for p in ps], [p["mag_pub"] for p in ps])
    r2 = spearmanr([p["n_anomaly_pixels"] for p in ps], [p["mir_vrp"] for p in ps])
    r3 = spearmanr([p["mir_vrp"] for p in ps], [p["razon_pub"] for p in ps])
    print("    spearman n_px~NUESTRA rho=%.3f | n_px~MIROVA rho=%.3f | MIROVA~razon rho=%.3f" % (r1.statistic, r2.statistic, r3.statistic))

print("")
print("=== V5 . H4 zenith: confound con volcan? ===")
ps = [p for p in pares if p["bucket"] == "VIIRS375" and p["zenith"] is not None]
for lo, hi in [(0, 20), (20, 40), (40, 90)]:
    q = [p for p in ps if lo <= p["zenith"] < hi]
    print("  zen [%d,%d) n=%d razon=%s vols=%s" % (lo, hi, len(q), round(med([x["razon_pub"] for x in q]), 3), dict(Counter(x["vol"] for x in q).most_common(4))))
print("  DENTRO de cada volcan:")
for vol in ("Lascar", "Isluga", "Lastarria", "Tupungatito", "PuyehueCordonCaulle", "PlanchonPeteroa", "Chaiten"):
    row = []
    for lo, hi in [(0, 20), (20, 40), (40, 90)]:
        q = [p["razon_pub"] for p in ps if p["vol"] == vol and lo <= p["zenith"] < hi]
        row.append("[%d,%d)n=%d m=%s" % (lo, hi, len(q), round(med(q), 3) if len(q) >= 5 else None))
    print("    %-20s %s" % (vol, " ".join(row)))

print("")
print("=== V6 . H1: Spearman DENTRO de cada volcan (Simpson) ===")
for vol in f1.TIER:
    q = [(p["d_crater"], p["razon_pub"]) for p in p375 if p["vol"] == vol and p["d_crater"] is not None]
    if len(q) >= 20:
        r = spearmanr([x for x, _ in q], [y for _, y in q])
        print("  %-20s n=%3d rho=%+.3f p=%.3g rango d=[%.2f,%.2f]" % (vol, len(q), r.statistic, r.pvalue, min(x for x, _ in q), max(x for x, _ in q)))

print("")
print("=== V7 . H7: los 'sin pasada nuestra' - horas UTC ===")
sp = list(mir_sin_pasada)
print("  total %d | por vol: %s" % (len(sp), dict(Counter(a["volcano"] for a in sp))))
ll = [a for a in sp if a["volcano"] in ("Lascar", "Lastarria")]
horas_ll = [int(a["fecha_utc"][11:13]) for a in ll]
print("  Lascar+Lastarria n=%d fuentes=%s vrp_med=%s rango horas UTC %d-%d todas 17-18h:%s" % (
    len(ll), dict(Counter(a["source"] for a in ll)), round(med([a["vrp_mw"] for a in ll]), 2), min(horas_ll), max(horas_ll), all(17 <= h <= 18 for h in horas_ll)))
print("  hh:mm min=%s max=%s" % (min(a["fecha_utc"][11:16] for a in ll), max(a["fecha_utc"][11:16] for a in ll)))
otras = [a for a in sp if a["volcano"] not in ("Lascar", "Lastarria")]
print("  las otras %d: %s" % (len(otras), dict(Counter((a["volcano"], a["fecha_utc"][11:13]) for a in otras).most_common(12))))
print("  horas UTC de nuestros records V375: %s" % dict(Counter(o["datetime_utc"][11:13] for o in descr if o["bucket"] == "VIIRS375").most_common(8)))
# hay algun record nuestro (de cualquier bucket) en esas horas?
cerc = []
for a in ll:
    ta = f1.t_mir(a)
    dts = [abs((o["t"] - ta).total_seconds()) / 3600.0 for o in descr if o["vol"] == a["volcano"]]
    cerc.append(min(dts) if dts else None)
print("  horas al record NUESTRO mas cercano (cualquier sensor): mediana %.1f h, min %.1f h" % (med(cerc), min(cerc)))

print("")
print("=== V8 . H5 MODIS ===")
descr_pc = [dict(o, mag_pub=o["mag_pc"]) for o in descr_par]
pares_pc, _, _, fn_pc, _ = f1.parear(descr_pc, alertas, 20.0)
mf = [p for p in pares_pc if p["bucket"] == "MODIS"]
far = [p for p in mf if p["distance_class"] == "far"]
print("  MODIS summit-only pares=%d | summit U far=%d %s" % (sum(1 for p in pares if p["bucket"] == "MODIS"), len(mf), dict(Counter(p["distance_class"] for p in mf))))
print("  far n=%d vols=%s d_med=%.2f razon_med=%.3f FN_restantes=%d" % (
    len(far), dict(Counter(p["vol"] for p in far)), med([p["d_crater"] for p in far]), med([p["razon_pc"] for p in far]), sum(1 for p in fn_pc if p["bucket"] == "MODIS")))
print("  razon summit U far MODIS %.3f IQR [%.2f,%.2f]" % (med([p["razon_pc"] for p in mf]), np.percentile([p["razon_pc"] for p in mf], 25), np.percentile([p["razon_pc"] for p in mf], 75)))

print("")
print("=== V9 . H6 Isluga ===")
import yaml
cfg = yaml.safe_load(io.open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8"))
vols = cfg["volcanoes"] if isinstance(cfg, dict) and "volcanoes" in cfg else cfg
items = vols if isinstance(vols, list) else [dict(name=k, **x) for k, x in vols.items()]
isl = [v for v in items if v["name"] == "Isluga"][0]
print("  YAML Isluga: %s" % {k: isl.get(k) for k in ("lat", "lon", "vent_lat", "vent_lon", "inner_radius_km", "radius_km", "mirova_center_lat", "mirova_center_lon")})
si = [o for o in descr if o["vol"] == "Isluga" and o["bucket"] == "VIIRS375" and o["mag_pub"] > 0]
print("  V375 publicados n=%d d_med=%.2f offN=%.2f offE=%.2f cuad=%s" % (
    len(si), med([o["d_crater"] for o in si]), med([o["off_n_km"] for o in si]), med([o["off_e_km"] for o in si]),
    dict(Counter(("N" if o["off_n_km"] > 0 else "S") + ("E" if o["off_e_km"] > 0 else "W") for o in si))))
pi = [p for p in p375 if p["vol"] == "Isluga"]
print("  pares n=%d d_med=%.2f frac<=0.5=%.3f" % (len(pi), med([p["d_crater"] for p in pi]), sum(1 for p in pi if p["d_crater"] <= 0.5) / len(pi)))
clat = med([raw_by_key[(o["vol"], o["sensor"], o["granule"])]["primary_cluster"]["centroid_lat"] for o in si])
clon = med([raw_by_key[(o["vol"], o["sensor"], o["granule"])]["primary_cluster"]["centroid_lon"] for o in si])
print("  centroide mediano publicados: lat %.4f lon %.4f | vent %.4f %.4f | catalogo %.4f %.4f" % (
    clat, clon, anclas["Isluga"][0], anclas["Isluga"][1], anclas_cat["Isluga"][0], anclas_cat["Isluga"][1]))
