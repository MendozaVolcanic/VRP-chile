#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A/B Villarrica: perfil congelado (produccion) vs operacional uniforme (issue #513).

PREGUNTA: Villarrica corre en produccion con un perfil congelado en abril, con
32 constantes distintas de las de los otros 10 Tier A. Su serie no es
comparable con la del resto. Antes de migrarla al operacional hay que MEDIR
que cambia: recall y magnitud vs MIROVA en la misma ventana, y si el escalon
de junio (0.06 -> 2.1 MW medianos) persiste o era del perfil.

METODO: se reusan VERBATIM los criterios del auto-audit canonico
(scripts/auto_audit_weekly.py, que a su vez congela el Eje 2 de AUDIT_S119).
No se re-derivan umbrales ni definiciones (regla S91 + A50: la respuesta ya
esta en el repo).
  - CRATER   : pc.vrp_mw>0 AND pc.centroid_dist_km<=inner AND vrp<=CAP  (A10)
  - DASHBOARD: CRATER AND distance_class in {summit, None}
  - MIROVA   : loader canonico CONS union OCR (A11), max VRP por noche-sensor
"""
import json
import os
import statistics
import sys
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
from pipeline.mirova_csv_loader import load_mirova_alertas  # noqa: E402
from scripts.auto_audit_weekly import our_bucket, CAP, SENSORS  # noqa: E402

SNAP = os.path.join(ROOT, "data", "mirova_reference", "mirova_v1_snapshot")
CONS = os.path.join(SNAP, "registro_vrp_consolidado.csv")
OCR = os.path.join(SNAP, "registro_vrp_ocr.csv")

VOL = "Villarrica"
INNER = 5          # radio interno oficial MIROVA (KML) para Villarrica
WIN = ("2026-04-01", "2026-08-24")

SERIES = {
    "produccion (perfil congelado)": os.path.join(
        ROOT, "data", "mirova_equivalent", VOL + ".json"),
    "A/B (operacional uniforme)": os.path.join(
        ROOT, "data", "_s124_villarrica_op_ab", VOL + ".json"),
}


def in_win(dt):
    return bool(dt) and WIN[0] <= dt[:10] <= WIN[1]


def cargar_nuestro(path):
    """-> {(bucket, fecha): {crater:[vrp], dash:[vrp]}}, n_records_ventana"""
    d = json.load(open(path, encoding="utf-8"))
    out = defaultdict(lambda: {"crater": [], "dash": []})
    n = 0
    for rec in d["records"]:
        dt = rec.get("datetime_utc")
        if not in_win(dt):
            continue
        n += 1
        b = our_bucket(rec.get("sensor", ""))
        if b is None:
            continue
        pc = rec.get("primary_cluster") or {}
        vrp = pc.get("vrp_mw") or 0.0
        cdist = pc.get("centroid_dist_km")
        if (0 < vrp <= CAP) and (cdist is not None and cdist <= INNER):
            key = (b, dt[:10])
            out[key]["crater"].append(vrp)
            dclass = rec.get("distance_class")
            if not dclass or dclass == "summit":
                out[key]["dash"].append(vrp)
    return out, n


def cargar_mirova():
    mir = defaultdict(float)
    for a in load_mirova_alertas(cons_path=CONS, ocr_path=OCR, volcano=VOL):
        dt = a["fecha_utc"] or ""
        if not in_win(dt) or a["sensor_bucket"] not in SENSORS:
            continue
        mir[(a["sensor_bucket"], dt[:10])] = max(
            mir[(a["sensor_bucket"], dt[:10])], a["vrp_mw"] or 0.0)
    return mir


def med(xs):
    return statistics.median(xs) if xs else None


def fmt(x, n=2):
    return "  -  " if x is None else f"{x:.{n}f}"


def main():
    mir = cargar_mirova()
    n_alerta = len(mir)
    print(f"=== A/B Villarrica  {WIN[0]} .. {WIN[1]} ===")
    print(f"MIROVA (CONS union OCR): {n_alerta} noches-sensor con ALERTA\n")

    resultados = {}
    for nombre, path in SERIES.items():
        if not os.path.exists(path):
            print(f"FALTA: {path}")
            continue
        ours, n_rec = cargar_nuestro(path)
        resultados[nombre] = (ours, n_rec)

    # --- 1. Recall y magnitud por bucket de sensor ---
    print("--- Recall vs MIROVA y magnitud (ratio nuestro/MIROVA) ---")
    print(f"{'serie':<32} {'sensor':<9} {'n_MIR':>6} {'rec_crater':>11} "
          f"{'rec_dash':>9} {'ratio_med':>10}")
    for nombre, (ours, _) in resultados.items():
        for s in SENSORS:
            noches = [(b, f) for (b, f) in mir if b == s]
            if not noches:
                continue
            c = sum(1 for k in noches if ours.get(k, {}).get("crater"))
            dsh = sum(1 for k in noches if ours.get(k, {}).get("dash"))
            ratios = [max(ours[k]["dash"]) / mir[k]
                      for k in noches
                      if ours.get(k, {}).get("dash") and mir[k] > 0]
            print(f"{nombre:<32} {s:<9} {len(noches):>6} "
                  f"{c / len(noches) * 100:>10.1f}% {dsh / len(noches) * 100:>8.1f}% "
                  f"{fmt(med(ratios)):>10}")

    # --- 2. El escalon de junio: mediana mensual de la magnitud publicada ---
    print("\n--- Mediana mensual del VRP publicado (dashboard, MW) ---")
    meses = sorted({f[:7] for (_, f) in mir} |
                   {f[:7] for (ours, _) in resultados.values() for (_, f) in ours})
    print(f"{'mes':<9} " + " ".join(f"{n[:26]:>28}" for n in resultados) +
          f"{'MIROVA':>12}")
    for m in meses:
        fila = f"{m:<9} "
        for nombre, (ours, _) in resultados.items():
            vals = [v for (b, f), o in ours.items() if f[:7] == m
                    for v in o["dash"]]
            fila += f"{fmt(med(vals)):>28} " if vals else f"{'-':>28} "
        mvals = [v for (b, f), v in mir.items() if f[:7] == m and v > 0]
        fila += f"{fmt(med(mvals)):>11}"
        print(fila)

    # --- 3. Volumen ---
    print("\n--- Volumen de deteccion en la ventana ---")
    for nombre, (ours, n_rec) in resultados.items():
        n_dash = sum(1 for o in ours.values() if o["dash"])
        n_crat = sum(1 for o in ours.values() if o["crater"])
        print(f"{nombre:<32} records={n_rec:>5}  noches_crater={n_crat:>4}  "
              f"noches_dash={n_dash:>4}")


if __name__ == "__main__":
    main()
