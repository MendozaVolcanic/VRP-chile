# -*- coding: utf-8 -*-
"""¿El A/B aguanta el veredicto? — poder estadistico e IC por bootstrap.

Pregunta de Nicolas: "bastaron esos reprocesamientos para asegurar lo que dices?"

Un ratio mediano sin intervalo de confianza no distingue "no hay efecto" de
"no pudimos medirlo". Este script contesta tres cosas:
  1. IC 95% del ratio mediano por volcan y brazo (bootstrap, 5000 remuestreos).
  2. Los ICs de control y B, se SOLAPAN? Si si, la diferencia no es concluyente.
  3. B == C es exacto o solo coincide al redondear a 2 decimales?
"""
import collections, csv, io, json, random, statistics as st, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
INI, FIN = "2026-06-25", "2026-08-24"
VOLS = ["Lascar", "Isluga", "Lastarria", "Llaima", "Copahue", "Tupungatito",
        "NevadosDeChillan", "Villarrica", "Chaiten", "PlanchonPeteroa",
        "PuyehueCordonCaulle"]
ALIAS = {"NevadosDeChillan": "Nevados de Chillan",
         "PuyehueCordonCaulle": "Puyehue-Cordon Caulle"}
BRAZOS = [("control", "mirova_equivalent"), ("A", "_f70_a"),
          ("B", "_f70_b"), ("C", "_s124_kernelbg_ab")]
BANDA = (0.7, 1.4)


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
                gt[r.get("Volcan")][f] = max(gt[r.get("Volcan")].get(f, 0), v)
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


def ic_mediana(xs, n=5000, semilla=42):
    """IC 95% de la mediana por bootstrap."""
    if len(xs) < 2:
        return (float("nan"), float("nan"))
    rng = random.Random(semilla)
    meds = sorted(st.median(rng.choices(xs, k=len(xs))) for _ in range(n))
    return meds[int(0.025 * n)], meds[int(0.975 * n)]


if __name__ == "__main__":
    gt = alertas()
    print("1) IC 95% del ratio mediano (bootstrap 5000). Si el IC cruza la banda,")
    print("   el veredicto 'dentro/fuera' NO es concluyente para ese volcan.\n")
    print(f"{'volcan':20s} {'n':>3s} {'control (IC95)':>22s} {'B (IC95)':>22s} {'solapan?':>9s}")
    print("-" * 82)
    sin_poder = []
    for v in VOLS:
        m = gt.get(ALIAS.get(v, v), {})
        if not m:
            continue
        sc, sb = serie("mirova_equivalent", v), serie("_f70_b", v)
        if sc is None or sb is None:
            continue
        rc = [sc[f] / m[f] for f in m if f in sc]
        rb = [sb[f] / m[f] for f in m if f in sb]
        if len(rc) < 2 or len(rb) < 2:
            print(f"{v:20s} {len(rc):3d}   n insuficiente para IC")
            sin_poder.append(v)
            continue
        mc, mb = st.median(rc), st.median(rb)
        lc, hc = ic_mediana(rc)
        lb, hb = ic_mediana(rb)
        solapan = not (hc < lb or hb < lc)
        # el IC cruza el borde de banda?
        cruza = (lc < BANDA[0] < hc) or (lc < BANDA[1] < hc)
        marca = "SI" if solapan else "no"
        print(f"{v:20s} {len(rc):3d} {mc:7.2f} [{lc:.2f}-{hc:.2f}] "
              f"{mb:7.2f} [{lb:.2f}-{hb:.2f}] {marca:>9s}"
              + ("   <== IC cruza la banda" if cruza else ""))
    if sin_poder:
        print(f"\n   sin poder para IC (n<2): {', '.join(sin_poder)}")

    print("\n\n2) B == C es EXACTO o solo coincide al redondear?\n")
    print(f"{'volcan':20s} {'B':>10s} {'C':>10s} {'|B-C|':>10s}")
    print("-" * 54)
    for v in VOLS:
        m = gt.get(ALIAS.get(v, v), {})
        sb, sc2 = serie("_f70_b", v), serie("_s124_kernelbg_ab", v)
        if not m or sb is None or sc2 is None:
            continue
        rb = [sb[f] / m[f] for f in m if f in sb]
        rc = [sc2[f] / m[f] for f in m if f in sc2]
        if not rb or not rc:
            continue
        b, c = st.median(rb), st.median(rc)
        print(f"{v:20s} {b:10.6f} {c:10.6f} {abs(b-c):10.6f}")
    print("\n   |B-C| = 0.000000 -> identidad EXACTA: la grilla no cambia nada.")
    print("   |B-C| pequeno pero no cero -> coincidencia al redondear.")
