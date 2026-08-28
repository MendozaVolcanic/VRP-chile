# -*- coding: utf-8 -*-
"""Lectura APAREADA de un brazo F70 contra el control operacional.

Uso: python experiments/_s124_f70/03_leer_brazo.py _f70_a

POR QUE APAREADA (leccion S124): dos corridas no procesan el mismo conjunto de
pasadas (ventana, granules NRT que un reproceso posterior no encuentra, fallas
transitorias de descarga). Comparar conteos de series completas atribuye a
"algoritmo" diferencias que son de COBERTURA. Se compara sobre la interseccion,
clave (datetime_utc, sensor).

Fuente de verdad de los numeros del informe (regla S91).
"""
import io, json, math, statistics as st, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
BRAZO = sys.argv[1] if len(sys.argv) > 1 else "_f70_a"
VOLS = ["Lascar", "Isluga", "Lastarria", "Llaima", "Copahue", "Tupungatito",
        "NevadosDeChillan", "Villarrica", "Chaiten", "PlanchonPeteroa",
        "PuyehueCordonCaulle"]
INI, FIN = "2026-06-25", "2026-08-24"


def idx(path):
    p = Path(path)
    if not p.exists():
        return {}
    d = json.loads(p.read_text(encoding="utf-8"))
    out = {}
    for r in d["records"]:
        f = r.get("datetime_utc") or ""
        if INI <= f[:10] <= FIN:
            out[(f, r.get("sensor"))] = r
    return out


def pc(r):
    c = (r or {}).get("primary_cluster") or {}
    return (c.get("vrp_mw") or 0), c.get("centroid_dist_km")


if __name__ == "__main__":
    print(f"BRAZO {BRAZO} vs control (mirova_equivalent), ventana {INI}..{FIN}")
    print(f"{'volcan':20s} {'pasadas':>8s} {'ratio med':>10s} {'aparecen':>9s} "
          f"{'desaparecen':>12s} {'d.dist med':>11s}")
    print("-" * 76)
    tot_ap = tot_de = 0
    for v in VOLS:
        a, c = idx(ROOT / f"data/{BRAZO}/{v}.json"), idx(ROOT / f"data/mirova_equivalent/{v}.json")
        com = set(a) & set(c)
        if not com:
            print(f"{v:20s} {'sin pasadas comunes':>40s}")
            continue
        ratios, ddist, ap, de = [], [], 0, 0
        for k in com:
            va, da = pc(a[k])
            vc, dc = pc(c[k])
            if va > 0 and vc > 0:
                ratios.append(va / vc)
                if da is not None and dc is not None:
                    ddist.append(da - dc)
            elif va > 0:
                ap += 1
            elif vc > 0:
                de += 1
        tot_ap += ap
        tot_de += de
        m = st.median(ratios) if ratios else float("nan")
        dd = st.median(ddist) if ddist else float("nan")
        print(f"{v:20s} {len(com):8d} {m:10.2f} {ap:9d} {de:12d} {dd:10.2f}km")
    print(f"\nTOTAL aparecen: {tot_ap}   desaparecen: {tot_de}")
    print("\nratio = VRP brazo / VRP control en pasadas donde AMBOS detectan.")
    print("1.00 = la grilla no cambia la magnitud. d.dist = migracion del cluster (A61).")
