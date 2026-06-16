"""S110 tarea-spec #1 (D11 design 2026-06-16) — ¿de qué ETAPA del ensamblado vienen
los píxeles near-crater (<=inner_radius) del cluster artefacto MODIS de NdC?

El probe run-1 mostró 0 seeds summit del FIRST-PASS en noches-artefacto, pero los records
tienen anomaly_pixels a 1-5 km. Sospecha (A55/S85): vienen del second_pass_adjacent +
apply_second_pass_intra_radio_gate (recaptura con umbrales summit relajados). Esto decide la
definición del gate del ancla (opción B): "señal-summit genuina" debe excluir la recaptura.

MÉTODO (A45 read-only): monkeypatch que captura first_pass (fp_hot) + el gate intra-radio
(first_pass_mask, final_active_mask, output). Atribuye los píxeles near-crater por etapa.
Espejo de los probes S110. Corre en Actions (pyhdf/MODIS Linux). Archivar tras usar.
"""
import sys, io, os, json
from pathlib import Path
from datetime import datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

from pipeline.fetch import search_granules, download_granules, auth
import pipeline.process_modis as pm

VLAT, VLON = -36.863, -71.377
RADIUS_KM, VENT_RADIUS_KM, INNER_KM = 25.0, 2.0, 5.0
TARGETS = [
    ("2026-04-10", "MODIS_TERRA", "MOD021KM.A2026100.0130.061.2026100131437.hdf", "ARTEFACTO"),
    ("2026-03-08", "MODIS_TERRA", "MOD021KM.A2026067.0250.061.2026067131051.hdf", "ARTEFACTO"),
    ("2026-02-08", "MODIS_AQUA",  "MYD021KM.A2026039.0645.061.2026039192119.hdf", "ARTEFACTO"),
    ("2026-02-26", "MODIS_AQUA",  "MYD021KM.A2026057.0650.061.2026057191350.hdf", "ARTEFACTO"),
    ("2026-03-06", "MODIS_TERRA", "MOD021KM.A2026065.0135.061.2026065131325.hdf", "ARTEFACTO"),
    ("2026-05-01", "MODIS_TERRA", "MOD021KM.A2026121.0205.061.2026121132049.hdf", "REAL"),
    ("2026-06-10", "MODIS_TERRA", "MOD021KM.A2026161.0155.061.2026161131743.hdf", "REAL"),
    ("2026-04-18", "MODIS_TERRA", "MOD021KM.A2026108.0145.061.2026108131726.hdf", "REAL"),
]
PRODUCT_KEY = {"MODIS_TERRA": "MODIS_TERRA_L1B", "MODIS_AQUA": "MODIS_AQUA_L1B"}
HERE = Path(__file__).parent
DEST = HERE / "granules"; DEST.mkdir(parents=True, exist_ok=True)
OUT = HERE / "out_asm"; OUT.mkdir(parents=True, exist_ok=True)

# --- Monkeypatches: capturan masks intermedias por etapa ---
_REAL_FP = pm.first_pass_tests_2_and_3
_REAL_GATE = pm.apply_second_pass_intra_radio_gate
_CAP = {}

def _wrap_fp(*a, **kw):
    hot, diag = _REAL_FP(*a, **kw)
    _CAP["fp_hot"] = np.array(hot, dtype=bool)
    _CAP["dist_km"] = np.array(kw["dist_km"])  # vent_dist_per_pixel
    return hot, diag

def _wrap_gate(*a, **kw):
    # apply_second_pass_intra_radio_gate(first_pass_mask, final_active_mask,
    #   vent_dist_per_pixel, inner_radius_km, enabled)
    fpm = kw.get("first_pass_mask", a[0] if a else None)
    fam = kw.get("final_active_mask", a[1] if len(a) > 1 else None)
    out = _REAL_GATE(*a, **kw)
    _CAP["gate_first_pass_mask"] = np.array(fpm, dtype=bool)
    _CAP["gate_final_active_in"] = np.array(fam, dtype=bool)
    _CAP["gate_output"] = np.array(out, dtype=bool)
    _CAP["gate_vent_dist"] = np.array(kw.get("vent_dist_per_pixel"))
    _CAP["gate_inner"] = kw.get("inner_radius_km")
    return out

pm.first_pass_tests_2_and_3 = _wrap_fp
pm.apply_second_pass_intra_radio_gate = _wrap_gate


def gname(g):
    try: return g["umm"]["DataGranule"]["Identifiers"][0]["Identifier"]
    except Exception: return str(g)[:60]


def main():
    auth()
    print(f"NdC assembly attribution (tarea-spec #1) — {len(TARGETS)} noches\n", flush=True)
    results = []
    for date, sensor, granule, label in TARGETS:
        print(f"=== {label} {date} {sensor} ===\n    {granule}", flush=True)
        dt = datetime.strptime(date, "%Y-%m-%d")
        try:
            grs = search_granules(PRODUCT_KEY[sensor], VLAT, VLON, RADIUS_KM, dt)
        except Exception as e:
            print(f"    SEARCH FAIL: {e}", flush=True); continue
        stamp = ".".join(granule.split(".")[1:3])
        grs_t = [g for g in grs if gname(g) == granule or stamp in gname(g)] or grs
        try:
            paths = download_granules(grs_t, DEST)
        except Exception as e:
            print(f"    DOWNLOAD FAIL: {e}", flush=True); continue
        match = [p for p in paths if Path(p).name == granule] or \
                [p for p in paths if stamp in Path(p).name and "021KM" in Path(p).name]
        if not match:
            print(f"    NO MATCH", flush=True); continue
        _CAP.clear()
        try:
            pm.calculate_vrp(Path(match[0]), Path(match[0]), VLAT, VLON, RADIUS_KM,
                             vent_lat=VLAT, vent_lon=VLON, vent_radius_km=VENT_RADIUS_KM,
                             inner_radius_km=INNER_KM, exclude_zones=None,
                             active_water_bodies=None, lbg_global_compatible=True)
        except Exception as e:
            print(f"    calculate_vrp FAIL: {e}", flush=True); continue

        rec = {"date": date, "label": label, "sensor": sensor, "granule": granule}
        # --- atribución near-crater (vent_dist <= inner) por etapa ---
        if "fp_hot" in _CAP:
            d = _CAP["dist_km"]; near = d <= INNER_KM
            fp_near = int(np.sum(_CAP["fp_hot"] & near))
            rec["first_pass_summit_pixels"] = fp_near
            print(f"    FIRST-PASS seeds en summit (<={INNER_KM}km): {fp_near}", flush=True)
        else:
            print("    first-pass NO corrió (gate previo)", flush=True)
            rec["first_pass_ran"] = False
        if "gate_output" in _CAP:
            vd = _CAP["gate_vent_dist"]; near = vd <= _CAP["gate_inner"]
            fpm, fam, out = _CAP["gate_first_pass_mask"], _CAP["gate_final_active_in"], _CAP["gate_output"]
            n_fp = int(np.sum(fpm & near))
            n_2pass_added = int(np.sum(fam & ~fpm & near))   # añadidos por second_pass_adjacent
            n_gate_removed = int(np.sum(fam & ~out & near))  # quitados por el gate intra-radio
            n_final = int(np.sum(out & near))
            rec.update(gate_first_pass_summit=n_fp, secondpass_added_summit=n_2pass_added,
                       gate_removed_summit=n_gate_removed, gate_output_summit=n_final)
            print(f"    [gate S85] summit: first_pass={n_fp} | 2pass-recapture-añadidos={n_2pass_added}"
                  f" | gate-quitó={n_gate_removed} | salida-final={n_final}", flush=True)
            print(f"    -> los píxeles near-crater son: "
                  f"{'FIRST-PASS genuino' if n_fp>=n_2pass_added and n_fp>0 else ('SECOND-PASS recapture (suspecto A55/S85)' if n_2pass_added>0 else 'ninguno')}", flush=True)
        else:
            print("    intra-radio gate S85 NO se llamó", flush=True)
            rec["gate_ran"] = False
        results.append(rec); print("", flush=True)

    (OUT / "ndc_assembly_attribution.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    # --- síntesis ---
    print("=" * 60 + "\nSÍNTESIS — origen de los píxeles near-crater (<=5km)", flush=True)
    for lab in ("ARTEFACTO", "REAL"):
        rs = [r for r in results if r.get("label") == lab and "gate_output_summit" in r]
        if not rs: continue
        fp = sum(r["gate_first_pass_summit"] for r in rs)
        ad = sum(r["secondpass_added_summit"] for r in rs)
        fn = sum(r["gate_output_summit"] for r in rs)
        print(f"  {lab} (n={len(rs)}): first_pass_summit={fp} | 2pass_recapture_summit={ad} | final_summit={fn}", flush=True)
    print("\nVeredicto: si ARTEFACTO tiene first_pass_summit≈0 y 2pass_recapture_summit>0 ->", flush=True)
    print("el artefacto near-crater es RECAPTURA second-pass (gate del ancla B debe usar SOLO first-pass).", flush=True)


if __name__ == "__main__":
    main()
