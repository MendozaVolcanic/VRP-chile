# -*- coding: utf-8 -*-
"""Recalculo independiente (verificador S151) desde los JSON crudos y los CSV congelados.
No usa banco_paridad ni armar_tabla ni node. Predicado aproximado del tablero:
mirovaEqVrp(r, inner=5) > 0 y no cirrus (t_max<273.15 y >10 MW) y no campo difuso."""
import csv, json, sys, io
from datetime import datetime, timedelta
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = Path(sys.argv[1]); REF = Path(sys.argv[2])
BR = {"C0": "_s146_ab_control", "T0": "_s150_sin_tope_d9", "E": "_s150_etiqueta_cumulo", "B": "_s146_ab_sin_test1",
      "F": "_s147_ab_sin_test1_max", "J": "_s149_ab_sin_test1_b22", "K": "_s149_ab_sin_test1_b22_max",
      "KE": "_s150_k_etiqueta", "KET": "_s150_k_etiqueta_sin_tope", "G": "_s149_ab_sin_test1_gemelo"}
INNER = 5.0


def bucket(s):
    s = s.upper()
    if s.startswith("MODIS"): return "MODIS"
    if s.endswith("_750"): return "VIIRS750"
    return "VIIRS375"


def eq(r):
    pc = r.get("primary_cluster")
    if not pc: return r.get("vrp_mw") or 0
    if r.get("distance_class") and r["distance_class"] != "summit": return 0
    if pc.get("centroid_dist_km") is not None and pc["centroid_dist_km"] > INNER: return 0
    return pc.get("vrp_mw") or 0


def pub(r, conf):
    v = eq(r)
    if v <= 0: return 0
    if not conf and r.get("t_max_k") is not None and r["t_max_k"] < 273.15 and v > 10: return 0
    pc = r.get("primary_cluster") or {}
    if not conf and r.get("t_max_k") is not None and r["t_max_k"] < 278.15 and (pc.get("n_pixels") or 0) >= 100 and v >= 50 and v / pc["n_pixels"] < 1: return 0
    return 1


# referencia
ref = []
for fn, src in (("registro_vrp_consolidado.csv", "CONS"), ("registro_vrp_ocr.csv", "OCR")):
    for f in csv.DictReader(open(REF / fn, encoding="utf-8")):
        if "Chill" not in f["Volcan"]: continue
        t = f["Fecha_Satelite_UTC"]
        if not ("2026-09-14" <= t[:10] <= "2026-10-07"): continue
        s = {"VIIRS": "VIIRS750", "VIIRS375": "VIIRS375", "MODIS": "MODIS"}.get(f["Sensor"], f["Sensor"])
        ref.append(dict(t=datetime.strptime(t[:16], "%Y-%m-%d %H:%M"), s=s, tipo=f["Tipo_Registro"], vrp=float(f["VRP_MW"] or 0), src=src, dist=f["Distancia_km"]))
alertas = [x for x in ref if x["tipo"].startswith("ALERTA")]
print("alertas MIROVA NdC en ventana (CONS+OCR):", len(alertas))

R = {}
for n, p in BR.items():
    R[n] = {}
    for r in json.load(open(D / p / "NevadosDeChillan.json", encoding="utf-8"))["records"]:
        R[n][(bucket(r["sensor"]), r["datetime_utc"][:16])] = r


def buscar(n, a):
    for (s, t), r in R[n].items():
        if s == a["s"] and abs(datetime.strptime(t, "%Y-%m-%d %H:%M") - a["t"]) <= timedelta(minutes=6):
            return r
    return None


# dedupe alertas por (sensor, hora)
vistas = {}
for a in alertas:
    k = (a["s"], a["t"]); vistas.setdefault(k, a)
    if a["src"] == "CONS": vistas[k] = a
print("\n== alertas (sensor, hora, MW, fuente) y decision por brazo (1 publica)")
print("%-8s %-16s %6s %4s %4s | " % ("sensor", "hora", "MW", "src", "sza") + " ".join("%3s" % n for n in BR))
for k in sorted(vistas, key=lambda k: (k[0], k[1])):
    a = vistas[k]; fila = []
    sza = None
    for n in BR:
        r = buscar(n, a)
        if r is None: fila.append("  -"); continue
        sza = r.get("solar_zenith_deg")
        fila.append("%3d" % pub(r, True))
    print("%-8s %-16s %6.2f %4s %4s | " % (a["s"], a["t"].strftime("%m-%d %H:%M"), a["vrp"], a["src"], ("%.0f" % sza) if sza else "?") + " ".join(fila))

print("\n== MODIS topadas en C0 (d9_capped) y decision C0/T0, distance_class, pc dist, t_max")
for k, r in sorted(R["C0"].items()):
    pc = r.get("primary_cluster") or {}
    if not pc.get("d9_capped"): continue
    t = R["T0"].get(k)
    print(k, "C0 pub", pub(r, False), r["distance_class"], "pc_dist %.2f" % (pc.get("centroid_dist_km") or -1), "vrp", pc.get("vrp_mw"),
          "| T0 pub", pub(t, False) if t else None, t and t["distance_class"], t and (t.get("primary_cluster") or {}).get("vrp_mw"), "tmax", r.get("t_max_k"))
print("\n== d9_capped por brazo:", {n: sum(1 for r in R[n].values() if (r.get("primary_cluster") or {}).get("d9_capped")) for n in BR})
print("== MODIS KE vs KET: pasadas con pc.vrp distinto")
for k in sorted(R["KE"]):
    if k[0] != "MODIS": continue
    a, b = R["KE"][k], R["KET"].get(k)
    va, vb = (a.get("primary_cluster") or {}).get("vrp_mw"), b and (b.get("primary_cluster") or {}).get("vrp_mw")
    if va != vb: print("  ", k, va, vb)
print("== max pc.vrp MODIS por brazo:", {n: max(((r.get("primary_cluster") or {}).get("vrp_mw") or 0) for (s, _), r in R[n].items() if s == "MODIS") for n in BR})

print("\n== publicaciones 26 y 27 sep por brazo (predicado aprox., sin filtro diurno), con sza")
for n in ("C0", "B", "F", "K", "KE"):
    for k, r in sorted(R[n].items()):
        if k[1][:10] in ("2026-09-26", "2026-09-27") and pub(r, False):
            print("  ", n, k, "%.3f MW" % eq(r), "pc_dist", (r.get("primary_cluster") or {}).get("centroid_dist_km"), "sza", r.get("solar_zenith_deg"))
print("\n== filas de referencia NdC del 25 al 27 sep:")
for x in sorted(ref, key=lambda x: x["t"]):
    if "2026-09-25" <= x["t"].strftime("%Y-%m-%d") <= "2026-09-27":
        print("  ", x["t"], x["s"], x["tipo"], x["vrp"], x["dist"], x["src"])
