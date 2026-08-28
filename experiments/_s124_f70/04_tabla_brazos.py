# -*- coding: utf-8 -*-
"""Los 4 brazos de F70, lado a lado, contra MIROVA (ratio mediano por volcan).

  control  grilla OFF - kernel per-volcan  = data/mirova_equivalent
  A        grilla ON  - kernel per-volcan  = data/_f70_a
  B        grilla ON  - kernel GLOBAL      = data/_f70_b
  C        grilla OFF - kernel GLOBAL      = data/_s124_kernelbg_ab (6 vols)

Ratio = VRP nuestro / VRP MIROVA en las noches en que MIROVA publico ALERTA.
Banda de la MEDIANA: [0.7, 1.4] (no la de una deteccion suelta, que es
[0.5, 2.0] — el error que S124 encontro en la auditoria).
"""
import collections, csv, io, json, statistics as st, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
INI, FIN = "2026-06-25", "2026-08-24"
BANDA = (0.7, 1.4)
VOLS = ["Lascar", "Isluga", "Lastarria", "Llaima", "Copahue", "Tupungatito",
        "NevadosDeChillan", "Villarrica", "Chaiten", "PlanchonPeteroa",
        "PuyehueCordonCaulle"]
# A14: el scraper normaliza algunos nombres. Faltaba PCC y eso lo ESCONDIO de
# la tabla del veredicto F70 — justo el unico volcan con dano real (0.75->0.64).
ALIAS = {"NevadosDeChillan": "Nevados de Chillan",
         "PuyehueCordonCaulle": "Puyehue-Cordon Caulle"}
BRAZOS = [("control", "mirova_equivalent"), ("A", "_f70_a"),
          ("B", "_f70_b"), ("C", "_s124_kernelbg_ab")]


def alertas():
    gt = collections.defaultdict(dict)
    with open(ROOT / "latest_consolidado.csv", encoding="utf-8", errors="replace") as fh:
        for r in csv.DictReader(fh):
            f = (r.get("Fecha_Satelite_UTC") or "")[:10]
            if not (INI <= f <= FIN) or "ALERTA" not in (r.get("Tipo_Registro") or ""):
                continue
            if (r.get("Sensor") or "").strip().upper() != "VIIRS375":
                continue
            try:
                v = float(r.get("VRP_MW") or 0)
            except ValueError:
                continue
            if v > 0:
                k = r.get("Volcan")
                gt[k][f] = max(gt[k].get(f, 0), v)
    return gt


def serie(subdir, vol):
    p = ROOT / f"data/{subdir}/{vol}.json"
    if not p.exists():
        return None
    d = json.loads(p.read_text(encoding="utf-8"))
    o = {}
    for r in d["records"]:
        f = (r.get("datetime_utc") or "")[:10]
        s = r.get("sensor") or ""
        if not (INI <= f <= FIN) or "VIIRS" not in s or "750" in s:
            continue
        pc = r.get("primary_cluster") or {}
        v = pc.get("vrp_mw") or 0
        if v > 0 and r.get("distance_class") == "summit":
            o[f] = max(o.get(f, 0), v)
    return o


if __name__ == "__main__":
    gt = alertas()
    print(f"Ratio mediano vs MIROVA (banda de la MEDIANA {BANDA}), {INI}..{FIN}\n")
    print(f"{'volcan':20s} {'n':>4s} " + " ".join(f"{n:>9s}" for n, _ in BRAZOS))
    print("-" * 66)
    for v in VOLS:
        m = gt.get(ALIAS.get(v, v), {})
        if not m:
            continue
        fila, n = [], 0
        for _, sub in BRAZOS:
            s = serie(sub, v)
            if s is None:
                fila.append("   --")
                continue
            rs = [s[f] / m[f] for f in m if f in s]
            n = max(n, len(rs))
            if not rs:
                fila.append("   --")
            else:
                r = st.median(rs)
                marca = "*" if BANDA[0] <= r <= BANDA[1] else " "
                fila.append(f"{r:8.2f}{marca}")
        print(f"{v:20s} {n:4d} " + " ".join(f"{x:>9s}" for x in fila))
    print("\n* = dentro de banda. JUEZ del criterio F70: Tupungatito (B debe")
    print("curarlo donde C no). GUARDA: Lastarria no debe romperse (A84).")
