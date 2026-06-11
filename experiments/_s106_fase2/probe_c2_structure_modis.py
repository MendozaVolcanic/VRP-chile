"""S106 Fase 2 prep — estructura de los 132 inflados MODIS vs señal real.

C1 (cap t_bg 273K) quedó refutado (probe_c1: los inflados son warm-scene
279-288K, first-pass contextual, no cirrus). Candidato restante: la magnitud
viene de SUMAR muchos píxeles marginales (blob first-pass). ¿Un criterio de
energía-por-píxel o tamaño separa los inflados (artefacto, 0% MIROVA) de la
señal MODIS real (Láscar ~78 dets calibradas 0.92×, NdC F47 332 MW real)?

Compara, para records MODIS con pc.vrp>0:
  - inflados (pc.vrp>5, 11 vols, S105: 0% confirmados MIROVA)
  - Láscar todos (control real calibrado)
en: pc.n_pixels, vrp/píxel del cluster, pc.centroid_dist_km, fp pixels.

Uso: python probe_c2_structure_modis.py
"""
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VOLS = ["Lascar", "Lastarria", "Isluga", "Llaima", "Villarrica", "Tupungatito",
        "Chaiten", "Copahue", "NevadosDeChillan", "PlanchonPeteroa",
        "PuyehueCordonCaulle"]


def modis_recs(vol):
    f = ROOT / "data" / "mirova_equivalent" / f"{vol}.json"
    obj = json.load(open(f, encoding="utf-8"))
    recs = obj.get("records", obj) if isinstance(obj, dict) else obj
    return [r for r in recs if (r.get("sensor") or "").startswith("MODIS")]


def med(xs):
    return statistics.median(xs) if xs else None


def stats(label, recs):
    pcs = [r["primary_cluster"] for r in recs]
    npx = [p.get("n_pixels") or 0 for p in pcs]
    vrp = [p.get("vrp_mw") or 0 for p in pcs]
    vpp = [v / n for v, n in zip(vrp, npx) if n]
    dist = [p.get("centroid_dist_km") for p in pcs
            if p.get("centroid_dist_km") is not None]
    fp = [r.get("diag_n_first_pass_pixels") or 0 for r in recs]
    print(f"{label:<28} n={len(recs):>4}  npx med={med(npx)}  "
          f"vrp/px med={med(vpp):.3f} MW  dist med={med(dist):.2f} km  "
          f"fp med={med(fp)}")
    return vpp


def main():
    inflados, lascar_all = [], []
    for vol in VOLS:
        for r in modis_recs(vol):
            pc = r.get("primary_cluster") or {}
            if not pc or not (pc.get("vrp_mw") or 0) > 0:
                continue
            if vol == "Lascar":
                lascar_all.append(r)
            if (pc.get("vrp_mw") or 0) > 5:
                inflados.append(r)

    vpp_inf = stats("INFLADOS pc>5 (11 vols)", inflados)
    vpp_las = stats("Lascar real (control)", lascar_all)

    # solapamiento del discriminante vrp/px
    if vpp_inf and vpp_las:
        thr_candidates = [0.3, 0.5, 0.8, 1.0]
        print("\nDiscriminante energia-por-pixel (vrp_mw / n_pixels del cluster):")
        for thr in thr_candidates:
            fp_rate = sum(1 for v in vpp_inf if v >= thr) / len(vpp_inf)
            keep_real = sum(1 for v in vpp_las if v >= thr) / len(vpp_las)
            print(f"  thr={thr:.1f} MW/px: inflados que ESCAPAN={fp_rate:.0%}  "
                  f"Lascar real conservado={keep_real:.0%}")

    # tamaño del blob como discriminante alternativo
    npx_inf = [(r["primary_cluster"].get("n_pixels") or 0) for r in inflados]
    npx_las = [(r["primary_cluster"].get("n_pixels") or 0) for r in lascar_all]
    print(f"\nn_pixels cluster: inflados med={med(npx_inf)} "
          f"(p90={sorted(npx_inf)[int(0.9*len(npx_inf))] if npx_inf else '—'}) | "
          f"Lascar med={med(npx_las)} "
          f"(p90={sorted(npx_las)[int(0.9*len(npx_las))] if npx_las else '—'})")


if __name__ == "__main__":
    main()
