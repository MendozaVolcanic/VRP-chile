"""S107 §2 — audit del A/B fondo-local de magnitud MODIS (corona del cluster).

Compara los 3 brazos (base flag-OFF / footprint V-B / ring V-A) reprocesados en
GH Actions (workflow reproc-s107-modis-localmag-ab.yml), contra las predicciones
PRE-REGISTRADAS (A66, design 2026-06-13 §5):

  C1. DETECCIÓN sin cambios: base vs ON deben tener registros idénticos EXCEPTO
      pc.vrp_mw (+ el diag corona_degraded). El recompute es POST-selección →
      cualquier diff en triggered_test1 / distance_class / n_anomalous / cluster
      dist es un BUG. Criterio duro: 0 diffs.
  C2. INFLADOS curados: de los registros MODIS con base pc.vrp_mw > 5 MW, ≥85 %
      deben caer a ≤ 5 MW en el brazo ON (los ~120 warm-scene).
  C3. LÁSCAR control: la lava real NO debe desinflarse. mediana(ON/base) de
      pc.vrp_mw sobre Láscar (base pc.vrp>0) debe quedar en [0.85, 1.15].

USO (tras `gh run download <RUN> -D <staging>` + reproc_coverage_gate.py por brazo):
  python experiments/_s107_modis_localmag/audit_localmag_ab.py --staging <staging>

Read-only. No toca operacional. S91: este script es la fuente de verdad de los números.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
from collections import defaultdict

PROFILES = ["_modis_localmag_base", "_modis_localmag_footprint", "_modis_localmag_ring"]
VOLS = ["Lascar", "Chaiten", "Villarrica", "PuyehueCordonCaulle", "Tupungatito", "Llaima"]
INFLATE_MW = 5.0
CURE_FRACTION_MIN = 0.85
LASCAR_RATIO_BAND = (0.85, 1.15)
# campos de DETECCIÓN que deben ser idénticos base vs ON (todo menos magnitud/diag)
DET_FIELDS = ["distance_class", "triggered_test1", "n_anomalous_pixels"]


def _key(r):
    return (r.get("datetime_utc"), r.get("sensor"))


def load_profile_vol(staging, profile, vol):
    """Mergea los chunk-artifacts de (profile, vol) → dict key->record (MODIS only)."""
    recs = {}
    for entry in sorted(os.listdir(staging)):
        prefix = f"s107localmag-{profile}-"
        if not entry.startswith(prefix):
            continue
        rest = entry[len(prefix):]
        if not rest.startswith(f"{vol}-"):
            continue
        path = os.path.join(staging, entry, f"{vol}.json")
        if not os.path.exists(path):
            continue
        try:
            data = json.load(open(path, encoding="utf-8"))
        except Exception as e:
            print(f"  WARN no parsea {path}: {e}")
            continue
        for r in data.get("records", []):
            if not str(r.get("sensor", "")).startswith("MODIS"):
                continue
            recs[_key(r)] = r
    return recs


def pc_vrp(r):
    pc = r.get("primary_cluster") or {}
    return float(pc.get("vrp_mw") or 0.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--staging", required=True, help="dir con los artifacts de gh run download")
    args = ap.parse_args()

    data = {p: {v: load_profile_vol(args.staging, p, v) for v in VOLS} for p in PROFILES}

    # cobertura básica
    print("=== Cobertura (n registros MODIS por brazo/vol) ===")
    for v in VOLS:
        ns = {p: len(data[p][v]) for p in PROFILES}
        print(f"  {v:<20} base={ns[PROFILES[0]]:>4}  footprint={ns[PROFILES[1]]:>4}  ring={ns[PROFILES[2]]:>4}")

    results = {}
    for arm in ("_modis_localmag_footprint", "_modis_localmag_ring"):
        name = arm.replace("_modis_localmag_", "")
        print(f"\n{'='*70}\n=== BRAZO {name.upper()} vs base ===")

        # C1 — detección sin cambios
        det_diffs = []
        for v in VOLS:
            base, on = data["_modis_localmag_base"][v], data[arm][v]
            common = set(base) & set(on)
            only_base = set(base) - set(on)
            only_on = set(on) - set(base)
            for k in sorted(only_base):
                det_diffs.append((v, k, "solo en base"))
            for k in sorted(only_on):
                det_diffs.append((v, k, "solo en ON"))
            for k in sorted(common):
                for f in DET_FIELDS:
                    if base[k].get(f) != on[k].get(f):
                        det_diffs.append((v, k, f"{f}: {base[k].get(f)} -> {on[k].get(f)}"))
        c1_pass = len(det_diffs) == 0
        print(f"  C1 detección 0-diffs: {'PASS' if c1_pass else 'FAIL'} ({len(det_diffs)} diffs)")
        for d in det_diffs[:10]:
            print(f"     {d[0]} {d[1]} | {d[2]}")

        # C2 — inflados curados (todos los vols menos Láscar control)
        inflated_total = cured = 0
        residual = []
        for v in VOLS:
            if v == "Lascar":
                continue
            base, on = data["_modis_localmag_base"][v], data[arm][v]
            for k in set(base) & set(on):
                if pc_vrp(base[k]) > INFLATE_MW:
                    inflated_total += 1
                    if pc_vrp(on[k]) <= INFLATE_MW:
                        cured += 1
                    else:
                        residual.append((v, k, round(pc_vrp(base[k]), 2), round(pc_vrp(on[k]), 2)))
        frac = (cured / inflated_total) if inflated_total else float("nan")
        c2_pass = inflated_total > 0 and frac >= CURE_FRACTION_MIN
        print(f"  C2 inflados curados: {'PASS' if c2_pass else 'FAIL'} "
              f"({cured}/{inflated_total} = {frac:.0%}, umbral {CURE_FRACTION_MIN:.0%})")
        for d in residual[:8]:
            print(f"     residual {d[0]} {d[1]} base={d[2]} -> ON={d[3]}")

        # C3 — Láscar control
        base, on = data["_modis_localmag_base"]["Lascar"], data[arm]["Lascar"]
        ratios = [pc_vrp(on[k]) / pc_vrp(base[k])
                  for k in set(base) & set(on)
                  if pc_vrp(base[k]) > 0 and pc_vrp(on[k]) is not None]
        med_ratio = statistics.median(ratios) if ratios else float("nan")
        c3_pass = LASCAR_RATIO_BAND[0] <= med_ratio <= LASCAR_RATIO_BAND[1]
        print(f"  C3 Láscar control: {'PASS' if c3_pass else 'FAIL'} "
              f"(mediana ON/base = {med_ratio:.3f}, banda {LASCAR_RATIO_BAND}, n={len(ratios)})")

        # corona_degraded
        n_degraded = sum(1 for v in VOLS for r in data[arm][v].values()
                         if (r.get("primary_cluster") or {}).get("corona_degraded"))
        print(f"  corona_degraded (fallback regional): {n_degraded} registros")

        results[name] = {"C1": c1_pass, "C2": c2_pass, "C3": c3_pass,
                         "cured_frac": frac, "lascar_ratio": med_ratio, "degraded": n_degraded}

    # veredicto
    print(f"\n{'='*70}\n=== VEREDICTO (A66 pre-registrado) ===")
    for name, r in results.items():
        allpass = r["C1"] and r["C2"] and r["C3"]
        print(f"  {name:<10} C1={r['C1']} C2={r['C2']} C3={r['C3']} -> {'ADOPTABLE' if allpass else 'NO'}")
    print("\nDiscriminador V-A vs V-B (A66): a igualdad de C1-C3, gana mayor cured_frac, "
          "menor lascar desviación de 1.0, y menos corona_degraded.")
    return results


if __name__ == "__main__":
    main()
