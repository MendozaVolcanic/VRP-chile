"""S106 — Co-validación cross-sensor para el destape MODIS.

Hipótesis: el blob warm-scene first-pass MODIS (132 inflados, 0% MIROVA) es
efímero/atmosférico → NO co-ocurre con detecciones VIIRS375 de la misma noche.
La señal volcánica real (Láscar) detecta en VIIRS375 casi todas las noches →
sus records MODIS sí co-ocurren.

Nota: S101 descartó "co-validación" para la población pre-nadir (sec³ activo,
otro mecanismo). La población post-S102/S105 es distinta (first-pass warm-blob)
→ re-test justificado con registro.

Para cada record MODIS con pc.vrp>0: ¿existe record VIIRS375 con detección
(pc.vrp>0) en la MISMA fecha (día UTC) del mismo volcán?

Uso: python probe_modis_covalidation.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VOLS = ["Lascar", "Lastarria", "Isluga", "Llaima", "Villarrica", "Tupungatito",
        "Chaiten", "Copahue", "NevadosDeChillan", "PlanchonPeteroa",
        "PuyehueCordonCaulle"]


def recs(vol):
    obj = json.load(open(ROOT / "data/mirova_equivalent" / f"{vol}.json",
                         encoding="utf-8"))
    return obj.get("records", obj)


def main():
    tot_inf = inf_cov = 0
    tot_las = las_cov = 0
    print(f"{'vol':<20}{'inflados':>9}{'co-val':>7}{'%':>5}")
    for vol in VOLS:
        rs = recs(vol)
        v375_det_days = {(r.get("datetime_utc") or "")[:10] for r in rs
                         if str(r.get("sensor", "")).startswith("VIIRS")
                         and not str(r.get("sensor", "")).endswith("750")
                         and ((r.get("primary_cluster") or {}).get("vrp_mw") or 0) > 0}
        modis = [r for r in rs if str(r.get("sensor", "")).startswith("MODIS")
                 and ((r.get("primary_cluster") or {}).get("vrp_mw") or 0) > 0]
        inf = [r for r in modis
               if ((r.get("primary_cluster") or {}).get("vrp_mw") or 0) > 5]
        cov = sum(1 for r in inf
                  if (r.get("datetime_utc") or "")[:10] in v375_det_days)
        tot_inf += len(inf)
        inf_cov += cov
        if inf:
            print(f"{vol:<20}{len(inf):>9}{cov:>7}{100*cov/len(inf):>4.0f}%")
        if vol == "Lascar":
            tot_las = len(modis)
            las_cov = sum(1 for r in modis
                          if (r.get("datetime_utc") or "")[:10] in v375_det_days)

    print(f"\nINFLADOS (11 vols): {inf_cov}/{tot_inf} co-validados por V375 misma "
          f"noche ({100*inf_cov/max(tot_inf,1):.0f}%)")
    print(f"LASCAR real (todos): {las_cov}/{tot_las} co-validados "
          f"({100*las_cov/max(tot_las,1):.0f}%)")
    print("\nGate candidato: MODIS pc.vrp>5 + first-pass-only SIN co-val V375 "
          "misma noche -> cap/marca. Si % inflados-coval alto, REFUTADO.")


if __name__ == "__main__":
    main()
