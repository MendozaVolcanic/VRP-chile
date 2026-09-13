"""S139 eje 4: el primer pase, ¿separa noches ALERTA de noches silenciosas de MIROVA?

Anticipa (sin reprocesar) lo que puede hacer el segundo pase condicionado (D19/D2) y cualquier
cambio que limpie el primer pase (D21): si el primer pase dispara igual en positivos y negativos,
condicionar el segundo pase no discrimina; si dispara sólo en positivos, sí.

Preguntas del instrumento:
1. Si el primer pase estuviera roto (siempre 0), la fracción seria 0 en ambos grupos: se ve.
2. Instrumento muerto: los campos diag_* pueden faltar (None) en records viejos; se cuentan como
   SIN DATO aparte, nunca como 0.
Unidad: noche local por volcan y sensor; una noche "dispara" si alguna pasada tiene el diag > 0.
Ventana: 2026-01-10 a 2026-09-07 (la del CSV). Mismas definiciones que 01_linea_base_noches.py.
"""
import json, sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import importlib.util
spec = importlib.util.spec_from_file_location("lb", Path(__file__).parent / "01_linea_base_noches.py")
# reusar definiciones sin re-ejecutar el reporte: se copia lo minimo
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
lb_out = json.load(open(Path(__file__).parent / "out/linea_base_noches.json"))
from pipeline.mirova_csv_loader import load_mirova_alertas, normalize_volcano_name  # noqa
import csv

SNAP = REPO / "data/mirova_reference/mirova_v1_snapshot"
CONS, OCR = SNAP / "registro_vrp_consolidado.csv", SNAP / "registro_vrp_ocr.csv"
FOCAL = ["Lascar", "Lastarria", "Isluga", "PlanchonPeteroa", "PuyehueCordonCaulle"]
NEVADO = ["Llaima", "Copahue", "Villarrica", "NevadosDeChillan", "Tupungatito", "Chaiten"]
RMIN, RMAX = datetime(2026, 1, 10, 19, 6), datetime(2026, 9, 8, 13, 30)
night = lambda dt: (dt - timedelta(hours=12)).date()
bucket = lambda s: "MODIS" if s.startswith("MODIS") else ("VIIRS750" if s.endswith("_750") else "VIIRS375")

rutina = defaultdict(set)
for path in (CONS, OCR):
    for row in csv.DictReader(open(path, encoding="utf-8")):
        vol = normalize_volcano_name(row.get("Volcan"))
        if vol and (row.get("Tipo_Registro") or "").strip() == "RUTINA":
            try:
                rutina[vol].add(night(datetime.strptime(row["Fecha_Satelite_UTC"][:19], "%Y-%m-%d %H:%M:%S")))
            except Exception:
                pass

agg = defaultdict(lambda: defaultdict(int))
vrp = defaultdict(list)
for vol in FOCAL + NEVADO:
    reg = "focal" if vol in FOCAL else "nevado"
    al_any = set()
    for a in load_mirova_alertas(cons_path=CONS, ocr_path=OCR, volcano=vol):
        al_any.add(night(datetime(1970, 1, 1) + timedelta(seconds=int(a["timestamp"]))))
    recs = json.load(open(REPO / f"data/mirova_equivalent/{vol}.json", encoding="utf-8"))["records"]
    per = defaultdict(lambda: {"fp": False, "fp_sum": False, "sin_dato": True, "max_vrp": 0.0, "recap": False})
    for r in recs:
        dt = datetime.strptime(r["datetime_utc"][:16], "%Y-%m-%d %H:%M")
        if not (RMIN <= dt <= RMAX):
            continue
        k = (bucket(r["sensor"]), night(dt))
        p = per[k]
        fpp, fps, rc = r.get("diag_n_first_pass_pixels"), r.get("diag_n_first_pass_summit"), r.get("diag_n_second_pass_recapture")
        if fpp is not None:
            p["sin_dato"] = False
            p["fp"] |= fpp > 0
            p["fp_sum"] |= (fps or 0) > 0
            p["recap"] |= (rc or 0) > 0
        pc = r.get("primary_cluster") or {}
        p["max_vrp"] = max(p["max_vrp"], pc.get("vrp_mw") or 0)
    for (b, n), p in per.items():
        grp = "pos" if n in al_any else ("neg" if n in rutina[vol] else None)
        if grp is None:
            continue
        key = f"{reg}_{b}_{grp}"
        agg[key]["noches"] += 1
        if p["sin_dato"]:
            agg[key]["sin_dato"] += 1
            continue
        agg[key]["primer_pase_escena"] += p["fp"]
        agg[key]["primer_pase_summit"] += p["fp_sum"]
        agg[key]["recaptura_2do"] += p["recap"]
        vrp[key].append(p["max_vrp"])


def auc(pos, neg):
    if not pos or not neg:
        return None
    s = 0.0
    for x in pos:
        for y in neg:
            s += 1.0 if x > y else (0.5 if x == y else 0.0)
    return s / (len(pos) * len(neg))


res = {}
for key in sorted(agg):
    res[key] = dict(agg[key])
for reg in ("focal", "nevado"):
    for b in ("MODIS", "VIIRS750", "VIIRS375"):
        res[f"AUC_maxvrp_{reg}_{b}"] = auc(vrp[f"{reg}_{b}_pos"], vrp[f"{reg}_{b}_neg"])
json.dump(res, open(Path(__file__).parent / "out/primer_pase_discrimina.json", "w"), indent=1)
for k, v in res.items():
    print(k, v)
