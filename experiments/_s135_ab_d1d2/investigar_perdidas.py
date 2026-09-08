# -*- coding: utf-8 -*-
"""S135 — investiga, pasada por pasada, cada noche que un brazo del A/B pierde.

POR QUÉ. El criterio de Nicolás (2026-09-07) es cero pérdidas, pero con una instrucción encima:
una pérdida **no descarta el brazo, abre una investigación**. Hacerlo a mano una noche por vez
no escala —el chunk 1 dejó nueve— y además invita a mirar sólo las que uno espera. Esto lo hace
igual para todas.

QUÉ MUESTRA, por cada noche perdida:
  · lo que publicó MIROVA esa noche (hora, sensor, VRP, distancia desde SU centro de grilla);
  · lo que hizo CADA brazo en CADA pasada de esa noche: fuente, clase, cúmulo, magnitud, y la
    distancia del centroide **recalculada desde el centro de MIROVA**, que es el único origen
    con el que la comparación tiene sentido (A93; comparar contra la distancia al cráter mezcla
    orígenes separados por hasta 7,6 km en Puyehue);
  · los diagnósticos que explican el mecanismo: píxeles del primer pase, recapturas del segundo,
    tamaño del footprint del Test 1.

CÓMO LEER EL RESULTADO. Las tres explicaciones posibles del pre-registro:
  1. nos falta algo que MIROVA hace  → el Test 1 dispara y algo aguas abajo lo anula;
  2. la alerta es de una pasada diurna → ya excluida del universo, no debería aparecer acá;
  3. la entrada difiere → la pasada no existe en nuestro lado, o el granule es otro.
La explicación «MIROVA lo revisó a mano» NO es válida: su canal NRT no tiene supervisión.

Uso:  python experiments/_s135_ab_d1d2/investigar_perdidas.py --dir <artefactos> [--brazo D]
"""
import argparse
import io
import json
import math
import os
import sys
from collections import defaultdict
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import yaml  # noqa: E402

from pipeline.mirova_csv_loader import load_mirova_alertas  # noqa: E402
from run_pipeline import is_nighttime  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from evaluar_ab import (BRAZOS, CONTROL, INNER, VOLCANES, cargar, es_v375,  # noqa: E402
                        hav, magnitud, parse_dt, publica_en_crater)

SNAP = os.path.join(ROOT, "data", "mirova_reference", "mirova_v1_snapshot")


def main():
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--brazo", default=None, help="letra (B, D...) o nada para todos")
    args = ap.parse_args()

    res_p = os.path.join(args.dir, "resultado_ab.json")
    if not os.path.exists(res_p):
        print(f"Falta {res_p}: correr antes evaluar_ab.py sobre esa carpeta.")
        return
    res = json.load(open(res_p, encoding="utf-8"))

    vc = yaml.safe_load(open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8"))
    vmap = {v["name"]: v for v in vc["volcanoes"]}

    alertas = load_mirova_alertas(cons_path=os.path.join(SNAP, "registro_vrp_consolidado.csv"),
                                  ocr_path=os.path.join(SNAP, "registro_vrp_ocr.csv"))
    por_noche = defaultdict(list)
    for a in alertas:
        f = a.get("fecha_utc")
        if f and a["sensor_bucket"] == "VIIRS375":
            por_noche[(a["volcano"], f[:10])].append(a)

    datos = {}
    for _, perfil, _ in BRAZOS:
        for vol in VOLCANES:
            recs = cargar(args.dir, perfil, vol)
            if recs is not None:
                datos[(perfil, vol)] = [r for r in recs if es_v375(r)]

    for letra, perfil, desc in BRAZOS:
        if perfil == CONTROL:
            continue
        if args.brazo and letra.upper() != args.brazo.upper():
            continue
        b = res["brazos"].get(perfil) or {}
        perdidas = b.get("criterio1_detalle") or []
        if not perdidas:
            continue
        print("\n" + "#" * 78)
        print(f"# BRAZO {letra} — {desc}: {len(perdidas)} noche(s) perdida(s)")
        print("#" * 78)
        for p in perdidas:
            vol, fecha = p["volcan"], p["fecha"]
            cfg = vmap[vol]
            cm = (cfg.get("mirova_center_lat"), cfg.get("mirova_center_lon"))
            sep = (hav(cfg["vent_lat"], cfg["vent_lon"], cm[0], cm[1])
                   if cm[0] is not None else None)
            print(f"\n=== {vol} {fecha} "
                  f"(inner {INNER[vol]} km · cráter↔centro de MIROVA "
                  f"{('%.3f km' % sep) if sep is not None else 'sin centro'}) ===")
            print("  MIROVA esa noche:")
            for a in sorted(por_noche.get((vol, fecha), []), key=lambda x: x["fecha_utc"]):
                dt = parse_dt(a["fecha_utc"])
                noche = is_nighttime(cfg["lat"], cfg["lon"], dt) if dt else None
                print(f"    {a['fecha_utc'][11:]} {a['vrp_mw']:>7} MW @ {a['dist_km']} km "
                      f"[{a['source']}] {a['clasificacion']}"
                      f"{'' if noche else '  ← PASADA DIURNA'}")
            for l2, p2, _ in BRAZOS:
                rs = [r for r in (datos.get((p2, vol)) or [])
                      if r["datetime_utc"].startswith(fecha)]
                if not rs:
                    continue
                for r in sorted(rs, key=lambda x: x["datetime_utc"]):
                    pc = r.get("primary_cluster") or {}
                    d_cm = (round(hav(cm[0], cm[1], pc["centroid_lat"], pc["centroid_lon"]), 3)
                            if (pc.get("centroid_lat") is not None and cm[0] is not None) else None)
                    pub = "PUB" if publica_en_crater(r, INNER[vol]) else "   "
                    print(f"    {l2} {r['datetime_utc'][11:]} {r['sensor']:<13} {pub} "
                          f"src={str(r.get('final_hotspot_source')):<12} "
                          f"{str(r.get('distance_class')):<6} "
                          f"pc={pc.get('n_pixels')}px {pc.get('vrp_mw')}MW "
                          f"d_centroMIR={d_cm} "
                          f"fp={r.get('diag_n_first_pass_pixels')} "
                          f"2p={r.get('diag_n_second_pass_recapture')} "
                          f"t1={r.get('n_test1_pixels')}")


if __name__ == "__main__":
    main()
