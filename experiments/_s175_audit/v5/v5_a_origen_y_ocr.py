# -*- coding: utf-8 -*-
"""V5-A: verificacion independiente de 301 (distancia del OCR como vara) y 303 (origen de la distancia).

Dos preguntas del instrumento:
 1. Si la distancia del OCR fuera una buena vara, ¿esto lo veria? Si: compara OCR contra tabla (CONS) en las MISMAS pasadas
    y contra NUESTRA posicion (tercer arbitro, medida desde mirova_center); si el OCR fuera bueno, sus residuos serian como los de la tabla.
 2. Si el instrumento estuviera muerto: el control positivo es la separacion tabla-vs-ocr de las pasadas V31 (arreglo de Mirova-v1#20)
    y el placebo es permutar las pasadas (residuo contra un par ajeno), que tiene que dar residuos enormes.
Universo: i2_pares.csv de la re-corrida (881 pasadas nuestras pos+pub, ventana 2026-06-11..2026-11-07 del banco). Pareo OCR/CONS +-120 s (TOL_S del banco).
Importa solo para parsear (referencia_mirova_unificada de la copia 752d348bc); no modifica nada. Correr con python -B.
"""
import collections, csv, json, os, random, statistics as st, sys
from datetime import datetime
sys.dont_write_bytecode = True
ROOT = r"C:\Users\nmend\vrp-temporales\s175_audit\f5\root"
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
from referencia_mirova_unificada import leer_pasadas, SNAP_CONS, SNAP_OCR
H = os.path.dirname(os.path.abspath(__file__))
TOL = {"VIIRS375": 0.75, "VIIRS750": 1.5, "MODIS": 3.0}
dt = lambda s: datetime.strptime(s[:16], "%Y-%m-%d %H:%M")
V31 = "2026-10-09 14:01"

pares = list(csv.DictReader(open(os.path.join(H, "rerun", "i2_pares.csv"), encoding="utf-8")))
print("pares nuestros pos+pub:", len(pares))

# --- 303: residuo por origen y por fuente de la distancia
res = collections.defaultdict(list)
for p in pares:
    if not p["dist_mirova"] or not p["d_final_hotspot"] or not p["d_desde_mirova_center"]:
        continue
    dm = float(p["dist_mirova"])
    res[(p["fuente_dist"], "vent(final_hotspot_dist_km)")].append(abs(float(p["d_final_hotspot"]) - dm))
    res[(p["fuente_dist"], "mirova_center")].append(abs(float(p["d_desde_mirova_center"]) - dm))
out = {"residuo_por_origen": {}}
for k, l in sorted(res.items()):
    l.sort()
    out["residuo_por_origen"]["|".join(k)] = {"n": len(l), "mediana_km": round(st.median(l), 3), "p90_km": round(l[int(0.9 * len(l))], 3)}
    print(k, out["residuo_por_origen"]["|".join(k)])
# por volcan (CONS): donde el origen importa
pv = collections.defaultdict(lambda: {"vent": [], "mc": []})
for p in pares:
    if p["fuente_dist"] != "CONS" or not p["d_final_hotspot"] or not p["d_desde_mirova_center"]:
        continue
    dm = float(p["dist_mirova"])
    pv[p["vol"]]["vent"].append(abs(float(p["d_final_hotspot"]) - dm))
    pv[p["vol"]]["mc"].append(abs(float(p["d_desde_mirova_center"]) - dm))
out["cons_por_volcan_mediana_residuo_vent_vs_mc"] = {v: {"n": len(d["vent"]), "vent": round(st.median(d["vent"]), 2), "mc": round(st.median(d["mc"]), 2)} for v, d in sorted(pv.items())}
for v, d in sorted(out["cons_por_volcan_mediana_residuo_vent_vs_mc"].items()):
    print("CONS", v, d)

# --- 301: OCR contra tabla en las mismas pasadas, con nuestra posicion de arbitro
cons = leer_pasadas(SNAP_CONS, "CONS", "principal")
ocr = leer_pasadas(SNAP_OCR, "OCR", "principal")
ic = collections.defaultdict(list); io = collections.defaultdict(list)
for f in cons:
    if f["tipo"].startswith("ALERTA") and f["dist_km"] and f["dist_km"] > 0:
        ic[(f["volcano"], f["sensor_bucket"])].append((dt(f["fecha_utc"]), f))
for f in ocr:
    if f["tipo"].startswith("ALERTA_TERMICA") and f["dist_km"] and f["dist_km"] > 0:
        io[(f["volcano"], f["sensor_bucket"])].append((dt(f["fecha_utc"]), f))
filas = []
for p in pares:
    if not p["d_desde_mirova_center"]:
        continue
    key = (p["vol"], p["b"]); t = dt(p["dt"])
    c = [f for tt, f in ic.get(key, []) if abs((tt - t).total_seconds()) <= 120]
    o = [f for tt, f in io.get(key, []) if abs((tt - t).total_seconds()) <= 120]
    if c and o:
        filas.append({"vol": p["vol"], "b": p["b"], "dt": p["dt"], "d_cons": c[0]["dist_km"], "d_ocr": o[0]["dist_km"],
                      "d_ours_mc": float(p["d_desde_mirova_center"]), "fecha_ocr": o[0]["fecha_utc"]})
print("pasadas nuestras con fila CONS y OCR de alerta a +-120 s:", len(filas))
def resumen(sel, nombre):
    if not sel:
        return {"n": 0}
    dif = [abs(f["d_ocr"] - f["d_cons"]) for f in sel]
    mas_cerca_cons = sum(abs(f["d_cons"] - f["d_ours_mc"]) < abs(f["d_ocr"] - f["d_ours_mc"]) for f in sel if abs(f["d_ocr"] - f["d_cons"]) > 1)
    n_gt1 = sum(d > 1 for d in dif)
    r = {"n": len(sel), "n_ocr_vs_tabla_mayor_1km": n_gt1, "mediana_abs_dif": round(st.median(dif), 3),
         "de_esas_cuantas_la_tabla_esta_mas_cerca_de_nuestro_punto": mas_cerca_cons,
         "res_ours_vs_cons_mediana": round(st.median(abs(f["d_cons"] - f["d_ours_mc"]) for f in sel), 3),
         "res_ours_vs_ocr_mediana": round(st.median(abs(f["d_ocr"] - f["d_ours_mc"]) for f in sel), 3)}
    print(nombre, r)
    return r
out["ocr_vs_tabla_pasadas_con_ambas"] = {
    "antes_V31": resumen([f for f in filas if f["fecha_ocr"][:16] < V31], "antes_V31"),
    "desde_V31": resumen([f for f in filas if f["fecha_ocr"][:16] >= V31], "desde_V31"),
    "todas": resumen(filas, "todas")}
# placebo: emparejar cada OCR con la tabla de OTRA pasada (permutacion dentro del mismo sensor) -> residuo esperado enorme
rng = random.Random(5)
for b in TOL:
    sel = [f for f in filas if f["b"] == b]
    if len(sel) < 5:
        continue
    d_cons = [f["d_cons"] for f in sel]; rng.shuffle(d_cons)
    placebo = [abs(f["d_ocr"] - d) for f, d in zip(sel, d_cons)]
    print("placebo", b, len(sel), "mediana|ocr-tabla ajena|", round(st.median(placebo), 2), "real", round(st.median(abs(f["d_ocr"] - f["d_cons"]) for f in sel), 2))
    out.setdefault("placebo", {})[b] = {"n": len(sel), "mediana_placebo": round(st.median(placebo), 2), "mediana_real": round(st.median(abs(f["d_ocr"] - f["d_cons"]) for f in sel), 2)}

# --- 301 segunda mitad: de los (iii) por origen mirova_center, cuantos se apoyan en distancia OCR (fuente_dist)
iii = [p for p in pares if p["clase"] == "iii"]
out["iii_por_fuente"] = dict(collections.Counter(p["fuente_dist"] for p in iii))
out["iii_por_fuente_y_estrato"] = dict(collections.Counter(p["estrato"] for p in iii))
out["todos_por_fuente"] = dict(collections.Counter(p["fuente_dist"] for p in pares))
out["iii_tasa_por_fuente"] = {s: f"{sum(1 for p in iii if p['fuente_dist']==s)}/{sum(1 for p in pares if p['fuente_dist']==s)}" for s in ("CONS", "OCR")}
print("iii por fuente", out["iii_por_fuente"], out["iii_tasa_por_fuente"], "estrato", out["iii_por_fuente_y_estrato"])
json.dump(out, open(os.path.join(H, "v5_a_origen_y_ocr_out.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
