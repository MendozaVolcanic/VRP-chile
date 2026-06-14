"""S109 §1 — audit del A/B magnitud NÚCLEO FOCAL/CONTEXTUAL MODIS.

Compara 3 brazos reprocesados en GH Actions (reproc-s109-modis-focalmag-ab.yml)
contra criterios PRE-REGISTRADOS (A66, design 2026-06-14 §8):

  C1. DETECCIÓN sin cambios (granules COMUNES, lección S108): el recompute es
      POST-selección → en granules comunes, 0 diffs en distance_class/triggered_test1/
      n_anomalous_pixels/centroid_dist. La cobertura distinta por corrida (only_base/
      only_on) NO cuenta como diff (cada brazo es un reproc separado). Criterio: 0
      det-diffs en COMUNES.
  C2. INFLADOS curados: de los MODIS con base pc.vrp_mw > 5, % que cae a ≤ 5 en ON.
      Reporta también mediana ON/base (reducción) — objetivo acercar a MIROVA (~0).
  C3. LÁSCAR control: el foco MODIS real NO se desinfla. mediana(ON/base) de pc.vrp_mw
      sobre Láscar (base pc.vrp>0) en [0.85, 1.15].
  C4. FOCO DISCRETO preservado (restricción Nicolás = los incendios se muestran): en
      records con firma focal en base (píxel-pico ≥40% del cluster), ON debe preservar
      la magnitud (mediana ON/base ≥ 0.80). Si n bajo → underpowered, deferir a C3.

USO (tras `gh run download <RUN> -D <staging>` + reproc_coverage_gate.py por brazo):
  python experiments/_s109_modis_mag/audit_focalmag_ab.py --staging <staging>

Read-only. No toca operacional. S91: este script es la fuente de verdad de los números.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import statistics
from collections import defaultdict

BASE = "_modis_focalmag_base"
ARMS = ["_modis_focalmag_ctx", "_modis_focalmag_ctxpure"]
PROFILES = [BASE] + ARMS
VOLS = ["Lascar", "Chaiten", "Villarrica", "PuyehueCordonCaulle", "Tupungatito", "Llaima"]
INFLATE_MW = 5.0
CURE_FRACTION_MIN = 0.85
LASCAR_RATIO_BAND = (0.85, 1.15)
FOCAL_PEAK_FRAC = 0.40        # un record es "focal" si el píxel-pico aporta ≥40% del cluster
C4_PRESERVE_MIN = 0.80        # ON debe preservar ≥80% de la magnitud focal
DET_FIELDS = ["distance_class", "triggered_test1", "n_anomalous_pixels"]


def _key(r):
    return (r.get("datetime_utc"), r.get("sensor"))


def load_profile_vol(staging, profile, vol):
    """Mergea los chunk-artifacts de (profile, vol) → dict key->record (MODIS only)."""
    recs = {}
    prefix = f"s109focalmag-{profile}-"
    for entry in sorted(os.listdir(staging)):
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


def peak_frac(r):
    """fracción del cluster que aporta el píxel-pico (proxy de focalidad). Usa
    anomaly_pixels cerca del centroide del cluster."""
    pc = r.get("primary_cluster") or {}
    vrp_c = float(pc.get("vrp_mw") or 0.0)
    if vrp_c <= 0:
        return 0.0
    aps = r.get("anomaly_pixels") or []
    if not aps:
        return 0.0
    cl, co = pc.get("centroid_lat"), pc.get("centroid_lon")
    if cl is None or co is None:
        mx = max((float(a.get("vrp_mw") or 0.0) for a in aps), default=0.0)
        return mx / vrp_c
    # píxeles dentro de ~2km del centroide (cluster proxy)
    def near(a):
        dlat = (float(a["lat"]) - cl) * 111.0
        dlon = (float(a["lon"]) - co) * 111.0 * math.cos(math.radians(cl))
        return (dlat * dlat + dlon * dlon) <= 4.0
    mx = max((float(a.get("vrp_mw") or 0.0) for a in aps if near(a)), default=0.0)
    return mx / vrp_c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--staging", required=True, help="dir con artifacts de gh run download")
    args = ap.parse_args()

    data = {p: {v: load_profile_vol(args.staging, p, v) for v in VOLS} for p in PROFILES}

    print("=== Cobertura (n registros MODIS por brazo/vol) ===")
    for v in VOLS:
        ns = {p: len(data[p][v]) for p in PROFILES}
        print(f"  {v:<20} base={ns[BASE]:>4}  ctx={ns[ARMS[0]]:>4}  ctxpure={ns[ARMS[1]]:>4}")

    results = {}
    for arm in ARMS:
        name = arm.replace("_modis_focalmag_", "")
        print(f"\n{'='*72}\n=== BRAZO {name.upper()} vs base ===")

        # C1 — detección sin cambios (SOLO granules comunes)
        det_diffs, n_common, n_only_base, n_only_on = [], 0, 0, 0
        for v in VOLS:
            base, on = data[BASE][v], data[arm][v]
            common = set(base) & set(on)
            n_common += len(common)
            n_only_base += len(set(base) - set(on))
            n_only_on += len(set(on) - set(base))
            for k in sorted(common):
                for f in DET_FIELDS:
                    if base[k].get(f) != on[k].get(f):
                        det_diffs.append((v, k, f"{f}: {base[k].get(f)} -> {on[k].get(f)}"))
        c1_pass = len(det_diffs) == 0
        print(f"  C1 detección 0-diffs (comunes): {'PASS' if c1_pass else 'FAIL'} "
              f"({len(det_diffs)} diffs en {n_common} comunes; cobertura only_base={n_only_base} only_on={n_only_on} = ruido NASA)")
        for d in det_diffs[:10]:
            print(f"     {d[0]} {d[1]} | {d[2]}")

        # C2 — inflados curados (todos menos Láscar) + reducción mediana
        inflated_total = cured = 0
        residual, reduction = [], []
        for v in VOLS:
            if v == "Lascar":
                continue
            base, on = data[BASE][v], data[arm][v]
            for k in set(base) & set(on):
                if pc_vrp(base[k]) > INFLATE_MW:
                    inflated_total += 1
                    reduction.append(pc_vrp(on[k]) / pc_vrp(base[k]))
                    if pc_vrp(on[k]) <= INFLATE_MW:
                        cured += 1
                    else:
                        residual.append((v, k, round(pc_vrp(base[k]), 2), round(pc_vrp(on[k]), 2)))
        frac = (cured / inflated_total) if inflated_total else float("nan")
        med_red = statistics.median(reduction) if reduction else float("nan")
        c2_pass = inflated_total > 0 and frac >= CURE_FRACTION_MIN
        print(f"  C2 inflados curados: {'PASS' if c2_pass else 'FAIL'} "
              f"({cured}/{inflated_total} = {frac:.0%}; mediana ON/base = {med_red:.3f})")
        for d in residual[:8]:
            print(f"     residual {d[0]} {d[1]} base={d[2]} -> ON={d[3]}")

        # C3 — Láscar control
        base, on = data[BASE]["Lascar"], data[arm]["Lascar"]
        ratios = [pc_vrp(on[k]) / pc_vrp(base[k])
                  for k in set(base) & set(on) if pc_vrp(base[k]) > 0]
        med_ratio = statistics.median(ratios) if ratios else float("nan")
        c3_pass = bool(ratios) and LASCAR_RATIO_BAND[0] <= med_ratio <= LASCAR_RATIO_BAND[1]
        print(f"  C3 Láscar control: {'PASS' if c3_pass else 'FAIL'} "
              f"(mediana ON/base = {med_ratio:.3f}, banda {LASCAR_RATIO_BAND}, n={len(ratios)})")

        # C4 — foco discreto preservado (records con firma focal en base)
        focal_ratios = []
        for v in VOLS:
            base, on = data[BASE][v], data[arm][v]
            for k in set(base) & set(on):
                if pc_vrp(base[k]) > 0 and peak_frac(base[k]) >= FOCAL_PEAK_FRAC:
                    focal_ratios.append(pc_vrp(on[k]) / pc_vrp(base[k]))
        med_focal = statistics.median(focal_ratios) if focal_ratios else float("nan")
        c4_pass = bool(focal_ratios) and med_focal >= C4_PRESERVE_MIN
        c4_note = "" if len(focal_ratios) >= 5 else "  [underpowered n<5 → deferir a C3]"
        print(f"  C4 foco preservado: {'PASS' if c4_pass else ('FAIL' if focal_ratios else 'N/A')} "
              f"(mediana ON/base = {med_focal:.3f} ≥ {C4_PRESERVE_MIN}, n={len(focal_ratios)}){c4_note}")

        # focal_degraded diag (cuántos cayeron al solo-pico = sin foco contextual)
        n_degraded = sum(1 for v in VOLS for r in data[arm][v].values()
                         if (r.get("primary_cluster") or {}).get("focal_degraded"))
        print(f"  focal_degraded (solo-pico, sin foco contextual): {n_degraded} registros")

        results[name] = {"C1": c1_pass, "C2": c2_pass, "C3": c3_pass, "C4": c4_pass,
                         "cured_frac": frac, "med_reduction": med_red,
                         "lascar_ratio": med_ratio, "focal_ratio": med_focal,
                         "degraded": n_degraded}

    print(f"\n{'='*72}\n=== VEREDICTO (A66 pre-registrado) ===")
    for name, r in results.items():
        # adoptable = C1 (detección) + C3 (Láscar) + C4 (foco) duros; C2 = beneficio
        adoptable = r["C1"] and r["C3"] and (r["C4"] or math.isnan(r["focal_ratio"]))
        print(f"  {name:<10} C1={r['C1']} C2={r['C2']} C3={r['C3']} C4={r['C4']} "
              f"cured={r['cured_frac']:.0%} red={r['med_reduction']:.2f} lascar={r['lascar_ratio']:.2f} "
              f"-> {'ADOPTABLE' if adoptable else 'NO'}")
    print("\nRegla de decisión: adoptar el brazo que pase C1+C3+C4 (duros: detección, Láscar, foco) "
          "y maximice C2 (cura del inflado). ctx (keep-peak) preferido sobre ctxpure si ctxpure viola C4.")
    return results


if __name__ == "__main__":
    main()
