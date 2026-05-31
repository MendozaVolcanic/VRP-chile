"""S93 — Experimento decisivo del brainstorming: impacto de la co-validación path D.

Pregunta: si activamos PATH_D_REQUIRES_COVALIDATION (rechaza path D contextual
cuando NO hay NINGUN pixel BT/NTI duro en la escena), ¿cuantas anomalias REALES
confirmadas por MIROVA perdemos (contextual-puras) vs cuantos ARTEFACTOS eliminamos?

Aprox offline (A18: el reproc real puede diferir; esto es para DIRECCION del diseño).
Cota: un record con n_bt>0 o n_nti>0 HOY → la co-validacion lo preserva con certeza.
Un record contextual-only (n_bt==0 AND n_nti==0) → candidato a zerarse.

NO toca pipeline. Fuente de verdad reproducible (§0.5). Correr → stdout.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.mirova_csv_loader import load_mirova_alertas

TIER_A = ["PuyehueCordonCaulle","Villarrica","Lascar","Copahue","NevadosDeChillan",
          "Llaima","Chaiten","PlanchonPeteroa","Lastarria","Isluga","Tupungatito"]
CONS = os.path.join(REPO, "latest_consolidado.csv")
OCR = os.path.join(REPO, "data/mirova_reference/registro_vrp_ocr.csv")
import datetime as dt

def our_bucket(s):
    s = str(s or "").upper()
    if "MODIS" in s: return "MODIS"
    if s.endswith("_750"): return "VIIRS750"
    if s.startswith("VIIRS"): return "VIIRS375"
    return None

def mir_bucket(s):
    s = str(s or "").upper()
    if s == "MODIS": return "MODIS"
    if s == "VIIRS375": return "VIIRS375"
    if s == "VIIRS": return "VIIRS750"
    return None

def parse(s):
    try: return dt.datetime.fromisoformat(str(s).replace("Z","").strip())
    except Exception: return None

tot = {"tp":0,"tp_ctxonly":0,"tp_hard":0,"fp":0,"fp_ctxonly":0,"fp_hard":0}
per_vol = {}
for vol in TIER_A:
    f = os.path.join(REPO, f"data/mirova_equivalent/{vol}.json")
    d = json.load(open(f, encoding="utf-8"))
    recs = d["records"] if isinstance(d, dict) and "records" in d else d
    try:
        al = load_mirova_alertas(CONS, OCR, volcano=vol)
    except Exception as e:
        print(f"  [{vol}] loader error: {e}"); continue
    # alertas MIROVA VRP>0 indexadas por bucket -> lista de datetimes
    # loader devuelve list[dict] con keys: sensor_bucket, vrp_mw, fecha_utc
    mir = {}
    for r in al:
        if (r.get("vrp_mw") or 0) <= 0: continue
        b = r.get("sensor_bucket")
        t = parse(r.get("fecha_utc"))
        if b and t: mir.setdefault(b, []).append(t)
    v = {"tp":0,"tp_ctxonly":0,"fp":0,"fp_ctxonly":0}
    for rec in recs:
        pc = rec.get("primary_cluster") or {}
        vrp = pc.get("vrp_mw") or 0
        if vrp <= 0: continue
        b = our_bucket(rec.get("sensor"))
        t = parse(rec.get("datetime_utc"))
        if not b or not t: continue
        ctx_only = (rec.get("diag_n_bt_path") == 0 and rec.get("diag_n_nti_path") == 0)
        # match: alerta MIROVA mismo bucket +-60min
        matched = any(abs((t - mt).total_seconds()) <= 3600 for mt in mir.get(b, []))
        cat = "tp" if matched else "fp"
        v[cat] += 1
        if ctx_only: v[cat + "_ctxonly"] += 1
        tot[cat] += 1
        tot[cat + ("_ctxonly" if ctx_only else "_hard")] += 1
    per_vol[vol] = v

print("="*78)
print("IMPACTO CO-VALIDACION PATH D (aprox offline, cota por record actual)")
print("="*78)
print(f"{'Volcan':<22}{'TP':>5}{'TP-ctxOnly':>12}{'(=pierde)':>10}  {'FP':>5}{'FP-ctxOnly':>12}{'(=elimina)':>11}")
for vol in TIER_A:
    v = per_vol.get(vol, {})
    tp, tpc = v.get("tp",0), v.get("tp_ctxonly",0)
    fp, fpc = v.get("fp",0), v.get("fp_ctxonly",0)
    print(f"{vol:<22}{tp:>5}{tpc:>12}{(f'{100*tpc/tp:.0f}%' if tp else '-'):>10}  {fp:>5}{fpc:>12}{(f'{100*fpc/fp:.0f}%' if fp else '-'):>11}")
print("-"*78)
print(f"{'TOTAL':<22}{tot['tp']:>5}{tot['tp_ctxonly']:>12}{(f'{100*tot[chr(39)+chr(39)] if False else 100*tot['tp_ctxonly']/tot['tp']:.0f}%' if tot['tp'] else '-'):>10}  {tot['fp']:>5}{tot['fp_ctxonly']:>12}{(f'{100*tot['fp_ctxonly']/tot['fp']:.0f}%' if tot['fp'] else '-'):>11}")
print()
print("LECTURA:")
print(f"  TP que se PERDERIAN con co-validacion (contextual-puros): {tot['tp_ctxonly']} de {tot['tp']} ({100*tot['tp_ctxonly']/max(tot['tp'],1):.0f}%)")
print(f"  FP/artefactos que se ELIMINARIAN (contextual-puros): {tot['fp_ctxonly']} de {tot['fp']} ({100*tot['fp_ctxonly']/max(tot['fp'],1):.0f}%)")
print("  NOTA A18: cota optimista — la co-validacion es a nivel ESCENA (si hay")
print("  algun pixel duro en la pasada, el path D co-valida). Records ctx-only")
print("  que comparten pasada con un foco duro NO se pierden. Reproc real lo confirma.")
