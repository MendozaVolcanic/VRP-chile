"""S130 · ¿Detectamos lo mismo que MIROVA en sus 3 sensores, con y sin el piso VRP?

POR QUE: Nicolas condiciono el retiro del piso a verificar la paridad de DETECCION
por sensor. El instrumento que ya existe (scripts/auto_audit_weekly.py) NO sirve tal
cual para esta pregunta: mide sobre `primary_cluster.vrp_mw`, y el piso de store.py
toca `record.vrp_mw` — es CIEGO al cambio. Ademas su columna `recall_dash` no usa el
predicado que el dashboard usa de verdad (`isValidDetection`, index.html:1372).

Este script mide el mismo recall por bucket de sensor bajo TRES predicados sobre las
mismas noches-ALERTA de MIROVA, para que la comparacion sea de manzanas con manzanas:

  A · audit   — pc.vrp_mw > 0 intra-inner: lo que hoy reporta auto_audit_weekly.
  B · dash    — isValidDetection() del frontend, tal como corre HOY (con piso).
  C · sin_piso— igual que B pero restaurando vrp_mw = diag_vrp_raw_mw en los pisados.

C - B es exactamente lo que el retiro del piso le devuelve al dashboard. La resta es
exacta (no es una simulacion): el piso es un post-proceso sobre un valor que el propio
store.py preserva crudo en diag_vrp_raw_mw, asi que no hay reseleccion de cluster de
por medio y A18 no aplica.

Ventana: TODA la data (no los 60 dias del audit) para que el n por sensor aguante la
estratificacion. D2 (cobertura del CSV, 79,2 %) acota los tres predicados por igual,
asi que la comparacion RELATIVA entre ellos no se ve afectada.
"""
import json
import os
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from pipeline.mirova_csv_loader import load_mirova_alertas  # noqa: E402

SNAP = os.path.join(ROOT, "data", "mirova_reference", "mirova_v1_snapshot")
CONS = os.path.join(SNAP, "registro_vrp_consolidado.csv")
OCR = os.path.join(SNAP, "registro_vrp_ocr.csv")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resultado_paridad.json")

# Mismos parametros que scripts/auto_audit_weekly.py (no se reinventan)
VOLS = ["Lascar", "Lastarria", "Isluga", "Llaima", "Villarrica", "Chaiten",
        "Copahue", "NevadosDeChillan", "PlanchonPeteroa", "PuyehueCordonCaulle",
        "Tupungatito"]
INNER = {"Lascar": 5, "Lastarria": 3, "Tupungatito": 7, "PlanchonPeteroa": 3,
         "Copahue": 4, "PuyehueCordonCaulle": 20, "Isluga": 5,
         "NevadosDeChillan": 5, "Llaima": 5, "Villarrica": 5, "Chaiten": 5}
SENSORS = ["MODIS", "VIIRS750", "VIIRS375"]
CAP = 50000


def our_bucket(sensor):
    if sensor.startswith("MODIS"):
        return "MODIS"
    if sensor.endswith("_750"):
        return "VIIRS750"
    if sensor.startswith("VIIRS"):
        return "VIIRS375"
    return None


def is_valid_detection(vrp_mw, rec):
    """Replica exacta de isValidDetection() — frontend/index.html:1372."""
    if (vrp_mw or 0) > 0:
        return True
    return rec.get("triggered_test1") is True


def is_summit_detection(vrp_mw, rec):
    """Replica exacta de isSummitDetection() — frontend/index.html:1378."""
    if (vrp_mw or 0) == 0 and rec.get("discarded_reason") and not rec.get("triggered_test1"):
        return False
    dc = rec.get("distance_class")
    if dc == "summit":
        return True
    if dc == "far":
        return False
    return (rec.get("vrp_vent_mw") or 0) > 0


def main():
    # 1 · noches ALERTA de MIROVA por (vol, bucket, fecha)
    alertas = load_mirova_alertas(cons_path=CONS, ocr_path=OCR)
    mir = defaultdict(float)
    for a in alertas:
        dt = a["fecha_utc"] or ""
        if not dt or a["sensor_bucket"] not in SENSORS or a["volcano"] not in VOLS:
            continue
        key = (a["volcano"], a["sensor_bucket"], dt[:10])
        mir[key] = max(mir[key], a["vrp_mw"] or 0.0)

    # 2 · nuestras detecciones bajo los tres predicados
    hit = {p: defaultdict(bool) for p in ("audit", "dash", "sin_piso")}
    for vol in VOLS:
        path = os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json")
        d = json.load(open(path, encoding="utf-8"))
        for rec in d["records"]:
            dt = rec.get("datetime_utc")
            if not dt:
                continue
            b = our_bucket(rec.get("sensor", ""))
            if b is None:
                continue
            key = (vol, b, dt[:10])

            pc = rec.get("primary_cluster") or {}
            pcv, cdist = pc.get("vrp_mw") or 0.0, pc.get("centroid_dist_km")
            if (0 < pcv <= CAP) and (cdist is not None and cdist <= INNER[vol]):
                hit["audit"][key] = True

            v_hoy = rec.get("vrp_mw") or 0.0
            if is_valid_detection(v_hoy, rec) and is_summit_detection(v_hoy, rec):
                hit["dash"][key] = True

            # sin piso: el crudo vuelve donde el piso lo puso en cero
            v_sin = rec.get("diag_vrp_raw_mw") if rec.get("diag_vrp_raw_mw") is not None else v_hoy
            if is_valid_detection(v_sin, rec) and is_summit_detection(v_sin, rec):
                hit["sin_piso"][key] = True

    # 3 · recall por sensor bajo cada predicado
    por_sensor = {}
    for s in SENSORS:
        keys = [k for k in mir if k[1] == s]
        n = len(keys)
        row = {"n_noches_alerta_mirova": n}
        for p in ("audit", "dash", "sin_piso"):
            c = sum(1 for k in keys if hit[p][k])
            row[f"recall_{p}_pct"] = round(100 * c / n, 2) if n else None
            row[f"aciertos_{p}"] = c
        row["ganancia_sin_piso_noches"] = row["aciertos_sin_piso"] - row["aciertos_dash"]
        por_sensor[s] = row

    # 4 · por volcan (el piso no muerde parejo)
    por_vol = {}
    for vol in VOLS:
        keys = [k for k in mir if k[0] == vol]
        n = len(keys)
        if not n:
            continue
        d_ = sum(1 for k in keys if hit["dash"][k])
        sp = sum(1 for k in keys if hit["sin_piso"][k])
        por_vol[vol] = {"n_noches_alerta_mirova": n,
                        "recall_dash_pct": round(100 * d_ / n, 2),
                        "recall_sin_piso_pct": round(100 * sp / n, 2),
                        "ganancia_noches": sp - d_}

    # 5 · el criterio que no se negocia: ninguna noche MIROVA se pierde
    perdidas = [k for k in mir if hit["dash"][k] and not hit["sin_piso"][k]]

    res = {
        "definicion": (
            "recall_<p>_pct = de las noches (volcan,bucket,fecha) en que MIROVA declaro "
            "ALERTA (loader canonico CONS union OCR), el % en que NUESTRO pipeline tiene "
            "deteccion bajo el predicado <p>. audit = pc.vrp_mw>0 intra-inner (lo que "
            "reporta auto_audit_weekly). dash = isValidDetection && isSummitDetection del "
            "frontend, con el piso vigente. sin_piso = idem restaurando diag_vrp_raw_mw. "
            "Ventana: toda la data. Cota superior por D2 (cobertura CSV 79,2 %), igual "
            "para los tres predicados."
        ),
        "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_alertas_mirova_total": len(mir),
        "por_sensor": por_sensor,
        "por_volcan": por_vol,
        "noches_mirova_perdidas_al_quitar_piso": len(perdidas),
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)

    print(json.dumps({k: v for k, v in res.items() if k != "definicion"},
                     indent=2, ensure_ascii=False))
    print(f"\n-> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
