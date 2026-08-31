# -*- coding: utf-8 -*-
"""S130 · Cuanto sustrato tienen los dos flags del A/B de los fondos.

POR QUE: al correr la lectura del A/B sobre el chunk 1 ya rescatado, los tres
brazos dieron las CUATRO firmas identicas hasta el tercer decimal. Eso no es un
empate: es la firma de que los flags no producen efecto.

La comprobacion cruda lo confirmo — `pool` es identico al control en TODOS los
campos (mismos records, mismo vrp_mw, mismo pc.vrp_mw, mismo umbral) y `bgmag`
difiere en 3 records de 4.612, solo en `diag_eff_threshold_k`, en ninguno en el
VRP. Los flags SI estan bien puestos y `pipeline.profile` los lee bien (se
verifico; no es el A89 de S129), y los tres procesadores SI los consumen.

Lo que falta es el SUSTRATO. Los dos flags operan sobre los pixeles que cruzan el
umbral K1 de Coppola (NTI > -0,8):

  · `enable_test1_k1_retire_from_hot_mask` pasa `nti_path_hot` como mascara de
    fondo no apto. Si esa mascara esta vacia, no cambia nada.
  · `enable_test1_k1_bg_exclude` excluye esos mismos pixeles del pool del fondo.
    Si no hay ninguno, el fondo es el mismo.

Este script mide cuantas pasadas tienen al menos un pixel K1, por sensor y por
volcan, sobre la data operacional completa. Persiste el resultado (S91).
"""
import io
import json
import os
import sys
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resultado_sustrato.json")

VOLS = ["Chaiten", "Copahue", "Isluga", "Lascar", "Lastarria", "Llaima",
        "NevadosDeChillan", "PlanchonPeteroa", "PuyehueCordonCaulle",
        "Tupungatito", "Villarrica"]


def bucket(s):
    if s.startswith("MODIS"):
        return "MODIS"
    if s.endswith("_750"):
        return "VIIRS750"
    if s.startswith("VIIRS"):
        return "VIIRS375"
    return "otro"


def main():
    tot_s, con_s = defaultdict(int), defaultdict(int)
    tot_v, con_v = defaultdict(int), defaultdict(int)

    for v in VOLS:
        p = os.path.join(ROOT, "data", "mirova_equivalent", v + ".json")
        if not os.path.exists(p):
            continue
        for r in json.load(open(p, encoding="utf-8"))["records"]:
            n = r.get("n_nti_path")
            if n is None:
                n = r.get("diag_n_nti_path")
            if n is None:
                continue          # granule sin I04+I05: el path no se pudo evaluar
            b = bucket(r.get("sensor", ""))
            tot_s[b] += 1
            tot_v[v] += 1
            if n > 0:
                con_s[b] += 1
                con_v[v] += 1

    res = {
        "definicion": (
            "pasadas con al menos un pixel que cruza el umbral K1 de Coppola "
            "(NTI > -0,8 noche), leido de `n_nti_path` (o `diag_n_nti_path`). Es el "
            "SUSTRATO sobre el que operan enable_test1_k1_retire_from_hot_mask y "
            "enable_test1_k1_bg_exclude: sin pixeles K1 los dos flags son no-ops. "
            "Denominador: pasadas donde el path pudo evaluarse (granule con I04+I05)."
        ),
        "por_sensor": {b: {"records": tot_s[b], "con_k1": con_s[b],
                           "pct": round(100 * con_s[b] / tot_s[b], 2)}
                       for b in ("MODIS", "VIIRS750", "VIIRS375") if tot_s[b]},
        "por_volcan": {v: {"records": tot_v[v], "con_k1": con_v[v],
                           "pct": round(100 * con_v[v] / tot_v[v], 2)}
                       for v in VOLS if tot_v[v]},
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)

    print("SUSTRATO DEL UMBRAL K1 (NTI > -0,8) — sobre que actuan los flags del A/B\n")
    print(f"{'sensor':10s} {'records':>9s} {'con K1':>8s} {'%':>8s}")
    for b, d in res["por_sensor"].items():
        print(f"{b:10s} {d['records']:9d} {d['con_k1']:8d} {d['pct']:7.2f}%")
    print()
    print(f"{'volcan':24s} {'records':>9s} {'con K1':>8s} {'%':>8s}")
    for v, d in sorted(res["por_volcan"].items(), key=lambda kv: -kv[1]["pct"]):
        print(f"{v:24s} {d['records']:9d} {d['con_k1']:8d} {d['pct']:7.2f}%")
    print(f"\n-> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
