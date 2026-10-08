"""C01: tabla de records de Nevados de Chillan desde 2026-09-20 (S150, frente C).

Instrumento:
1. Si lo que mido estuviera roto (por ejemplo el tope D9 recortando), esta tabla lo veria:
   imprime vrp_mw escena, pc.vrp_mw, la marca d9_capped y los contadores de los caminos duros.
2. Si el instrumento estuviera muerto (archivo vacio o campos ausentes), las columnas saldrian
   None y el conteo de records seria 0; se imprime el denominador.
Ventana: datetime_utc >= 2026-09-20 en data/mirova_equivalent/NevadosDeChillan.json (local,
mismo commit que el remoto 85be8ec21 del 2026-10-02 12:34 UTC).
"""
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
VOL = sys.argv[1] if len(sys.argv) > 1 else "NevadosDeChillan"
DESDE = sys.argv[2] if len(sys.argv) > 2 else "2026-09-20"
d = json.load(open(f"data/mirova_equivalent/{VOL}.json", encoding="utf-8"))
recs = [r for r in d["records"] if r["datetime_utc"] >= DESDE]
print(f"{VOL}: {len(recs)} records desde {DESDE} (total {len(d['records'])})")
cols = ("dt sensor vrp pc_vrp pc_n n_anom n_clu cap fdeg spm cdist fclass fdist fsrc "
        "t_bg sig nbt nnti ndnti n1p n1ps n2p t1 t_max").split()
print("\t".join(cols))
# nota: la ventana horaria del 2026-10-01 08:35 es el ejemplo del plan
for r in recs:
    pc = r.get("primary_cluster") or {}
    row = [r["datetime_utc"], r["sensor"], r.get("vrp_mw"), pc.get("vrp_mw"), pc.get("n_pixels"),
           r.get("n_anomalous_pixels"), r.get("n_hotspots_clustered"), pc.get("d9_capped", ""),
           pc.get("focal_degraded", ""), pc.get("single_pixel_mode", pc.get("single_pixel", "")),
           pc.get("centroid_dist_km"), r.get("distance_class"), r.get("final_hotspot_dist_km"),
           r.get("final_hotspot_source"), r.get("t_bg_k"), r.get("diag_sigma_bg_k"),
           r.get("diag_n_bt_path"), r.get("diag_n_nti_path"), r.get("diag_n_dnti_ctx_path"),
           r.get("diag_n_first_pass_pixels"), r.get("diag_n_first_pass_summit"),
           r.get("diag_n_second_pass_recapture"), r.get("triggered_test1"), r.get("t_max_k")]
    if (r.get("vrp_mw") or 0) > 0 or pc:
        print("\t".join("-" if (x is None or x == "") else str(x) for x in row))
