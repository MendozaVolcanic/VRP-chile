"""S139 eje 4: (a) intentar reproducir la motivacion del plan (Lascar MODIS 9/75, negativos 432/2.513)
con varias definiciones de negativo; (b) serie mensual de positivos MODIS propios por volcan (poder).

Pregunta 1: si el denominador del orquestador fuera otro, alguna de las variantes lo reproduce o
ninguna: se reporta cual. Pregunta 2: una variante con 0 noches es SIN DATO, no 0 %.
Unidad noche local = fecha(utc - 12 h). Registros MODIS completos (2025-02 a hoy) y ventana del CSV.
"""
import csv, json, sys
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from pipeline.mirova_csv_loader import load_mirova_alertas  # noqa
import yaml
import importlib.util

spec = importlib.util.spec_from_file_location("x", Path(__file__).parent / "01_linea_base_noches.py")
SNAP = REPO / "data/mirova_reference/mirova_v1_snapshot"
CONS, OCR = SNAP / "registro_vrp_consolidado.csv", SNAP / "registro_vrp_ocr.csv"
VOLS = ["Lascar", "Lastarria", "Isluga", "PlanchonPeteroa", "PuyehueCordonCaulle",
        "Llaima", "Copahue", "Villarrica", "NevadosDeChillan", "Tupungatito", "Chaiten"]
RMIN, RMAX = datetime(2026, 1, 10), datetime(2026, 9, 8, 14)
night = lambda dt: (dt - timedelta(hours=12)).date()
vy = yaml.safe_load(open(REPO / "volcanoes.yaml", encoding="utf-8"))
vl = vy["volcanoes"] if isinstance(vy, dict) and "volcanoes" in vy else vy
inner = {(v.get("name") or v.get("id")): v.get("inner_radius_km", 10) for v in vl}


def mev(r, ik):
    pc = r.get("primary_cluster")
    if not pc:
        return r.get("vrp_mw") or 0
    if r.get("distance_class") and r["distance_class"] != "summit":
        return 0
    if pc.get("centroid_dist_km") is not None and pc["centroid_dist_km"] > ik:
        return 0
    return pc.get("vrp_mw") or 0


def summ(r):
    if (r.get("vrp_mw") or 0) == 0 and r.get("discarded_reason") and not r.get("triggered_test1"):
        return False
    if r.get("distance_class") == "summit":
        return True
    if r.get("distance_class") == "far":
        return False
    return (r.get("vrp_vent_mw") or 0) > 0


out = {}
pool = defaultdict(int)
for vol in VOLS:
    ik = inner.get(vol, 10)
    al_modis, al_any = set(), set()
    month_modis = Counter()
    for a in load_mirova_alertas(cons_path=CONS, ocr_path=OCR, volcano=vol):
        dt = datetime(1970, 1, 1) + timedelta(seconds=int(a["timestamp"]))
        al_any.add(night(dt))
        if a["sensor_bucket"] == "MODIS":
            al_modis.add(night(dt))
    for n in al_modis:
        month_modis[n.strftime("%Y-%m")] += 1
    recs = json.load(open(REPO / f"data/mirova_equivalent/{vol}.json", encoding="utf-8"))["records"]
    have_all, have_win, det_all, det_win = set(), set(), set(), set()
    for r in recs:
        if not r["sensor"].startswith("MODIS"):
            continue
        dt = datetime.strptime(r["datetime_utc"][:16], "%Y-%m-%d %H:%M")
        n = night(dt)
        d = summ(r) and mev(r, ik) > 0
        have_all.add(n)
        det_all |= {n} if d else set()
        if RMIN <= dt <= RMAX:
            have_win.add(n)
            det_win |= {n} if d else set()
    v = {
        "pos_modis_ventana": len(al_modis & have_win), "rec_dash": len(al_modis & det_win),
        "negA_sin_alerta_modis_ventana": len(have_win - al_modis), "fpA": len((have_win - al_modis) & det_win),
        "negB_sin_alerta_modis_todo_historial": len(have_all - al_modis), "fpB": len((have_all - al_modis) & det_all),
        "negC_sin_alerta_ninguna_ventana": len(have_win - al_any), "fpC": len((have_win - al_any) & det_win),
        "modis_alerta_por_mes": dict(sorted(month_modis.items())),
    }
    out[vol] = v
    for k, x in v.items():
        if isinstance(x, int):
            pool[k] += x
out["POOL_11"] = dict(pool)
json.dump(out, open(Path(__file__).parent / "out/denominador_y_poder.json", "w"), indent=1)
for k, v in out.items():
    print(k, v)
