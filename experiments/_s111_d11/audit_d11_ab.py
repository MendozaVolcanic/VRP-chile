"""S111 D11 — audit A/B del gate del ancla MODIS. CRITERIOS PRE-REGISTRADOS (A66).

Compara 3 brazos pareados por granule sobre los 11 Tier A:
  - base   = data/mirova_equivalent/        (operacional, master OFF)
  - nogate = data/_d11_modis_nogate/         (master ON, gate OFF — contrafactual)
  - gated  = data/_d11_modis_gated/          (master ON, gate ON — candidato)

Solo records MODIS. El ancla toca POSICIÓN (distance_class), no detección.

CRITERIOS DE VEREDICTO (pre-registrados antes de ver el reproc):
  C1 — NdC artefacto bloqueado: gated_flips(NdC) << nogate_flips(NdC). El gate
       debe bloquear la mayoría de los ~199 candidatos (artefacto topográfico A69).
  C2 — Láscar curado (D12): gated_flips(Lascar) > 0 (recupera FN reales al cráter).
  C3 — cat-b preservado: en los otros 9 Tier A, todo gated_flip tiene
       first_pass_summit>0 (señal genuina, no artefacto).
  C4 — detección invariante (DURO, por construcción M1): base vs gated, 0 diffs en
       triggered_test1 / n_anomalous_pixels / diag_n_first_pass_pixels por granule.
  MECANISMO (DURO): todo gated_flip tiene fps>0; todo nogate_flip que el gate
       bloquea (no es gated_flip) tiene fps==0. Si se viola → BUG, no adoptar.

Salida: stdout conciso + JSON. Pre-escrito S111 (A16); corre tras el reproc A/B.
"""
import json, io, sys
from pathlib import Path
from collections import defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "data" / "mirova_equivalent"
NOGATE = ROOT / "data" / "_d11_modis_nogate"
GATED = ROOT / "data" / "_d11_modis_gated"
VOLS = ["Lastarria", "PlanchonPeteroa", "Copahue", "Lascar", "Isluga",
        "NevadosDeChillan", "Llaima", "Villarrica", "Chaiten", "Tupungatito",
        "PuyehueCordonCaulle"]
OUT = Path(__file__).parent / "d11_ab_audit.json"


def load_modis_by_granule(d, vol):
    f = d / f"{vol}.json"
    if not f.exists():
        return None
    doc = json.loads(f.read_text(encoding="utf-8"))
    recs = doc["records"] if isinstance(doc, dict) else doc
    out = {}
    for r in recs:
        if str(r.get("sensor", "")).startswith("MODIS"):
            out[r.get("granule")] = r
    return out


def dc(r):
    return r.get("distance_class")


def main():
    results = {}
    print("S111 D11 — audit A/B (base vs nogate vs gated), pareado por granule\n", flush=True)
    for vol in VOLS:
        base = load_modis_by_granule(BASE, vol)
        nog = load_modis_by_granule(NOGATE, vol)
        gat = load_modis_by_granule(GATED, vol)
        if not gat:
            print(f"{vol:22s} — sin reproc gated (skip)", flush=True)
            continue
        # granules presentes en gated (y base para C4)
        commons = [g for g in gat if base and g in base]
        nogate_flips = gated_flips = 0
        c4_diffs = 0
        mech_bad_flip = 0           # gated_flip con fps==0 (BUG)
        mech_bad_block = 0          # bloqueado por gate pero fps>0 (BUG)
        gated_flip_fps_pos = 0
        for g in commons:
            b, gd = base[g], gat[g]
            ng = nog.get(g) if nog else None
            fps = gd.get("diag_n_first_pass_summit", 0) or 0
            b_far = dc(b) == "far"
            # flips far->summit
            if ng is not None and b_far and dc(ng) == "summit":
                nogate_flips += 1
            gflip = b_far and dc(gd) == "summit"
            if gflip:
                gated_flips += 1
                if fps > 0:
                    gated_flip_fps_pos += 1
                else:
                    mech_bad_flip += 1
            # bloqueo por gate: nogate flipea pero gated no
            if ng is not None and b_far and dc(ng) == "summit" and not gflip:
                if fps > 0:
                    mech_bad_block += 1
            # C4 deteccion invariante base vs gated
            for k in ("triggered_test1", "n_anomalous_pixels", "diag_n_first_pass_pixels"):
                if b.get(k) != gd.get(k):
                    c4_diffs += 1
                    break
        results[vol] = dict(n_common=len(commons), nogate_flips=nogate_flips,
                            gated_flips=gated_flips, c4_det_diffs=c4_diffs,
                            mech_bad_flip=mech_bad_flip, mech_bad_block=mech_bad_block)
        print(f"{vol:22s} n={len(commons):4d} | nogate_flip={nogate_flips:4d} "
              f"gated_flip={gated_flips:4d} | C4_diffs={c4_diffs:3d} | "
              f"MECH bad_flip={mech_bad_flip} bad_block={mech_bad_block}", flush=True)

    OUT.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n=== VEREDICTO (criterios pre-registrados) ===", flush=True)
    ndc = results.get("NevadosDeChillan", {})
    lasc = results.get("Lascar", {})
    c1 = ndc.get("gated_flips", 99999) < 0.5 * max(ndc.get("nogate_flips", 1), 1)
    c2 = lasc.get("gated_flips", 0) > 0
    c4 = all(v["c4_det_diffs"] == 0 for v in results.values())
    mech = all(v["mech_bad_flip"] == 0 and v["mech_bad_block"] == 0 for v in results.values())
    print(f"  C1 NdC artefacto bloqueado (gated {ndc.get('gated_flips')} << nogate "
          f"{ndc.get('nogate_flips')}): {'PASS' if c1 else 'FAIL'}", flush=True)
    print(f"  C2 Láscar curado (gated_flips {lasc.get('gated_flips')} > 0): "
          f"{'PASS' if c2 else 'FAIL'}", flush=True)
    print(f"  C4 detección invariante (0 diffs todos): {'PASS' if c4 else 'FAIL'}", flush=True)
    print(f"  MECANISMO gate consistente (0 bad_flip/bad_block): "
          f"{'PASS' if mech else 'FAIL'}", flush=True)
    print(f"\n  ADOPTAR si C1∧C2∧C4∧MECANISMO. C3 (cat-b) = revisar gated_flips por "
          f"vol vs actividad real.", flush=True)


if __name__ == "__main__":
    main()
