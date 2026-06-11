"""S106 Fase 2 prep — ¿C1 (cap D9 270→273K) cura los 131 records MODIS path-D-only
inflados sin dañar a Láscar (el único con señal MODIS real abundante)?

Cap actual (mirova_equivalent.yaml): path_d_only_cap_mw=5.0 cuando record es
path-D-only Y t_bg < 270K. Los 131 (S105 §5) son path-D-only con pc.vrp>5 que
HOY escapan al cap (t_bg >= 270K) o entraron antes del cap.

Mide sobre data/mirova_equivalent (en disco, A2):
  1. Por volcán: records MODIS con pc.vrp>5, cuántos son path-D-only, y la
     distribución de su t_bg_k (¿cuántos caen con cap a 273K? ¿cuántos escapan?).
  2. Láscar control: sus records MODIS path-D-only (reales o no) — cuántos
     serían capados a 273K y qué pc.vrp tienen (riesgo A68: altitud 5592 m
     contamina el proxy t_bg frío).

Uso: python probe_c1_cap_modis.py
"""
import json
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VOLS = ["Lascar", "Lastarria", "Isluga", "Llaima", "Villarrica", "Tupungatito",
        "Chaiten", "Copahue", "NevadosDeChillan", "PlanchonPeteroa",
        "PuyehueCordonCaulle"]


def modis_recs(vol):
    f = ROOT / "data" / "mirova_equivalent" / f"{vol}.json"
    if not f.exists():
        return []
    obj = json.load(open(f, encoding="utf-8"))
    recs = obj.get("records", obj) if isinstance(obj, dict) else obj
    return [r for r in recs if (r.get("sensor") or "").startswith("MODIS")]


def is_path_d_only(r):
    return ((r.get("n_dnti_ctx_path") or 0) > 0
            and (r.get("n_bt_path") or 0) == 0
            and (r.get("n_nti_path") or 0) == 0
            and not r.get("triggered_test1"))


def med(xs):
    return statistics.median(xs) if xs else None


def main():
    tot_inflated = tot_d_only = 0
    print(f"{'vol':<18}{'nMODIS':>7}{'pc>5':>6}{'D-only':>7}{'tbg<270':>8}"
          f"{'270-273':>8}{'>=273':>7}  tbg mediana pc>5-D-only")
    for vol in VOLS:
        recs = modis_recs(vol)
        infl = [r for r in recs
                if ((r.get("primary_cluster") or {}).get("vrp_mw") or 0) > 5]
        d_only = [r for r in infl if is_path_d_only(r)]
        tbg = [r.get("t_bg_k") for r in d_only if r.get("t_bg_k") is not None]
        lt270 = sum(1 for t in tbg if t < 270)
        b270_273 = sum(1 for t in tbg if 270 <= t < 273)
        ge273 = sum(1 for t in tbg if t >= 273)
        tot_inflated += len(infl)
        tot_d_only += len(d_only)
        m = med(tbg)
        print(f"{vol:<18}{len(recs):>7}{len(infl):>6}{len(d_only):>7}{lt270:>8}"
              f"{b270_273:>8}{ge273:>7}  {m:.1f}K" if m is not None else
              f"{vol:<18}{len(recs):>7}{len(infl):>6}{len(d_only):>7}{lt270:>8}"
              f"{b270_273:>8}{ge273:>7}  —")
    print(f"\nTotal inflados (pc.vrp>5): {tot_inflated} | path-D-only: {tot_d_only}")

    # Láscar control: TODOS sus path-D-only (cualquier vrp) — qué pasa a 273K
    print("\n--- Láscar control (riesgo A68 altitud) ---")
    recs = modis_recs("Lascar")
    d_only = [r for r in recs if is_path_d_only(r)]
    capped273 = [r for r in d_only
                 if r.get("t_bg_k") is not None and r["t_bg_k"] < 273]
    vrps = [((r.get("primary_cluster") or {}).get("vrp_mw") or 0)
            for r in capped273]
    print(f"path-D-only Láscar: {len(d_only)} | capados con 273K: {len(capped273)}")
    if vrps:
        print(f"pc.vrp de los capados: mediana={med(vrps):.2f} MW, "
              f"max={max(vrps):.2f} MW, >5MW: {sum(1 for v in vrps if v > 5)}")
    tbg_all = [r.get("t_bg_k") for r in recs if r.get("t_bg_k") is not None]
    print(f"t_bg_k Láscar MODIS (todos): mediana={med(tbg_all):.1f}K, "
          f"<273K: {sum(1 for t in tbg_all if t < 273)}/{len(tbg_all)}")


if __name__ == "__main__":
    main()
