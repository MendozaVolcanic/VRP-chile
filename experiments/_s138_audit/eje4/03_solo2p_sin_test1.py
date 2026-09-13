# -*- coding: utf-8 -*-
"""S138 eje 4 (b2 refinado): de las noches ALERTA MIROVA cubiertas UNICAMENTE por records
"solo segundo paso sin activos" (fp = 0, sp > 0), cuantas tampoco tienen el Test 1 disparado
en ninguno de esos records. Sin Test 1 no hay camino de rescate: si se condiciona el segundo
paso (D2) sin quitar la compuerta (D22), esas noches se pierden con certeza; las que tienen
Test 1 disparado quedarian publicadas por `test1_roi` con la magnitud de keep_peak (que puede
ser 0, ver script 01). Es la cota INFERIOR del costo; el script 02 (b2) es la cota superior.

P1/P2 del instrumento: si `triggered_test1` no estuviera persistido se cuenta como SIN DATO,
no como False. Denominador: noches ALERTA (nocturnas) por volcan y sensor, ventana del CSV.
"""
import collections
import io
import json
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
from pipeline.mirova_csv_loader import load_mirova_alertas  # noqa: E402
from auto_audit_weekly import es_pasada_diurna_descartada, _coords_por_volcan  # noqa: E402

SNAP = ROOT / "data" / "mirova_reference" / "mirova_v1_snapshot"
VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa",
        "NevadosDeChillan", "Llaima", "Villarrica", "Copahue",
        "PuyehueCordonCaulle", "Chaiten"]
INNER = {"Lascar": 5, "Lastarria": 3, "Tupungatito": 7, "PlanchonPeteroa": 3,
         "NevadosDeChillan": 5, "Chaiten": 5, "Villarrica": 5, "Llaima": 5,
         "Copahue": 4, "Isluga": 5, "PuyehueCordonCaulle": 20}
BUCKETS = ["VIIRS375", "VIIRS750", "MODIS"]


def bucket(s):
    s = s or ""
    if s.startswith("MODIS"):
        return "MODIS"
    if s.endswith("_750"):
        return "VIIRS750"
    return "VIIRS375" if s.startswith("VIIRS") else None


def visible(r, vol):
    pc = r.get("primary_cluster") or {}
    v = pc.get("vrp_mw") or 0.0
    if not (0 < v <= 50000):
        return False
    if r.get("distance_class") and r["distance_class"] != "summit":
        return False
    cd = pc.get("centroid_dist_km")
    return cd is not None and cd <= INNER[vol]


def ic_prop(k, n, nb=5000, semilla=42):
    if n == 0:
        return (float("nan"), float("nan"))
    rng = random.Random(semilla)
    xs = [1] * k + [0] * (n - k)
    ms = sorted(sum(rng.choices(xs, k=n)) / n for _ in range(nb))
    return ms[int(0.025 * nb)], ms[int(0.975 * nb)]


def main():
    al = load_mirova_alertas(cons_path=str(SNAP / "registro_vrp_consolidado.csv"),
                             ocr_path=str(SNAP / "registro_vrp_ocr.csv"))
    coords = _coords_por_volcan()
    fe = sorted(a["fecha_utc"][:10] for a in al)
    INI, FIN = fe[0], fe[-1]
    mir = set()
    for a in al:
        if a["volcano"] not in VOLS or a["sensor_bucket"] not in BUCKETS:
            continue
        ll = coords.get(a["volcano"])
        try:
            dto = datetime.fromisoformat(a["fecha_utc"]).replace(tzinfo=timezone.utc)
        except ValueError:
            dto = None
        if ll and dto and es_pasada_diurna_descartada(a["sensor_bucket"], ll[0], ll[1], dto):
            continue
        mir.add((a["volcano"], a["sensor_bucket"], a["fecha_utc"][:10]))
    tot = collections.Counter()
    print(f"ventana MIROVA {INI}..{FIN}")
    print(f"{'volcan':20s}{'sensor':9s}{'alertas':>8s}{'solo2p':>7s}{'sin_test1':>10s}{'con_test1':>10s}"
          f"{'sin_dato':>9s}")
    for vol in VOLS:
        d = json.load(open(ROOT / "data" / "mirova_equivalent" / f"{vol}.json", encoding="utf-8"))
        noches = collections.defaultdict(lambda: {"otro": 0, "solo2p": [], })
        for r in d["records"]:
            b = bucket(r.get("sensor"))
            f = (r.get("datetime_utc") or "")[:10]
            if not b or not (INI <= f <= FIN) or not visible(r, vol):
                continue
            fp, sp = r.get("diag_n_first_pass_pixels"), r.get("diag_n_second_pass_recapture")
            k = (b, f)
            if fp == 0 and (sp or 0) > 0 and r.get("final_hotspot_source") == "ctx_cluster":
                noches[k]["solo2p"].append(r.get("triggered_test1"))
            else:
                noches[k]["otro"] += 1
        for b in BUCKETS:
            n_mir = sum(1 for (v, bb, f) in mir if v == vol and bb == b)
            s2 = s2_sin = s2_con = s2_nd = 0
            for (v, bb, f) in mir:
                if v != vol or bb != b:
                    continue
                n = noches.get((b, f))
                if not n or n["otro"] > 0 or not n["solo2p"]:
                    continue
                s2 += 1
                if any(t is None for t in n["solo2p"]):
                    s2_nd += 1
                elif any(t for t in n["solo2p"]):
                    s2_con += 1
                else:
                    s2_sin += 1
            tot[(b, "n")] += n_mir
            tot[(b, "s2")] += s2
            tot[(b, "sin")] += s2_sin
            tot[(b, "con")] += s2_con
            print(f"{vol:20s}{b:9s}{n_mir:8d}{s2:7d}{s2_sin:10d}{s2_con:10d}{s2_nd:9d}")
    print("\nTotales (cota inferior = sin_test1; cota superior = solo2p):")
    for b in BUCKETS:
        n, s2, si = tot[(b, "n")], tot[(b, "s2")], tot[(b, "sin")]
        lo, hi = ic_prop(si, n)
        print(f"  {b}: alertas={n} solo2p={s2} sin_test1={si} ({si / n:.1%}, IC95 [{lo:.3f},{hi:.3f}])"
              if n else f"  {b}: SIN DATO")


if __name__ == "__main__":
    main()
