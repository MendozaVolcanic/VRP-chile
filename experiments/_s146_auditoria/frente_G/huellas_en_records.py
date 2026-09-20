"""Frente G (S146): huella de cada mecanismo en los records del regimen actual (>= 2026-09-01), por sensor.
Predicado del dashboard ejecutado con node via scripts/banco_paridad.correr_node (no portado). Solo lectura."""
import json, os, sys, io, collections
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.abspath(os.path.join(here, "..", "..", ".."))
sys.path.insert(0, root); sys.path.insert(0, os.path.join(root, "scripts"))
import yaml, banco_paridad as bp
DESDE = "2026-09-01"
cfg = yaml.safe_load(open(os.path.join(root, "volcanoes.yaml"), encoding="utf-8"))["volcanoes"]
tierA = {v["name"]: v for v in cfg if v.get("inner_radius_km")}
def bucket(s):
    s = str(s or "")
    return "MODIS" if s.startswith("MODIS") else ("VIIRS750" if s.endswith("_750") else "VIIRS375")
C = collections.defaultdict(collections.Counter)
casos, meta = [], []
for name, v in tierA.items():
    d = json.load(open(os.path.join(root, "data", "mirova_equivalent", name + ".json"), encoding="utf-8"))
    for r in d["records"]:
        if (r.get("datetime_utc") or "") < DESDE: continue
        b = bucket(r.get("sensor")); c = C[b]; pc = r.get("primary_cluster") or {}
        c["n"] += 1
        c["discarded_reason=" + str(r.get("discarded_reason"))] += 1
        c["final_hotspot_source=" + str(r.get("final_hotspot_source"))] += 1
        c["distance_class=" + str(r.get("distance_class"))] += 1
        c["geo_class=" + str(pc.get("geo_class"))] += 1
        c["product_version=" + str(r.get("product_version"))] += 1
        for k in ("single_pixel_mode", "d9_capped", "focal_magnitude", "corona_degraded"):
            if k in pc: c[f"pc.{k}={pc[k] if not isinstance(pc[k], dict) else 'dict'}"] += 1
        for k in ("diag_a46_relabel", "vrp_exceeds_sanity_cap", "diag_rejected_sanity_cap_mw", "diag_pc_rejected_sanity_cap_mw",
                  "diag_vrp_floor_mw", "discarded_n_pixels", "discarded_max_cluster_pixels", "f5_core_vrp_mw",
                  "vrp_mw_sum_active", "vrptir_aveni_mw", "nti_peak_lat", "diag_L_bg_vecinos_w_m2_sr_um", "diag_L_bg_local_w_m2_sr_um"):
            if r.get(k) is not None: c["tiene:" + k] += 1
        for k in ("n_excluded_water", "n_cloud_masked", "vrp_vent_mw", "vrp_tir_mw", "n_nti_rel_path", "diag_n_bt_path", "diag_n_nti_path",
                  "diag_n_eti_path", "diag_n_dnti_ctx_path", "diag_n_first_pass_pixels", "diag_n_second_pass_recapture", "n_vent_pixels"):
            if (r.get(k) or 0) > 0: c[k + ">0"] += 1
        if r.get("triggered_test1"): c["triggered_test1"] += 1
        if (r.get("n_anomalous_pixels") or 0) > 100: c["n_anomalous_pixels>100 (tope top-100)"] += 1
        if pc and pc.get("single_pixel_mode") and (pc.get("n_pixels") or 0) > 1: c["single_pixel_mode cambia (n_pixels>1)"] += 1
        if pc and (pc.get("vrp_mw") or 0) > 0 and r.get("f5_core_vrp_mw") is not None and abs(r["f5_core_vrp_mw"] - pc["vrp_mw"]) > 0.0015:
            c["f5_core != pc.vrp_mw"] += 1
            c["f5_core < pc" if r["f5_core_vrp_mw"] < pc["vrp_mw"] else "f5_core > pc"] += 1
        # legacy diag decide fuente: test1 disparo, hay pixeles contextuales en la mascara, pero dnti_ctx legacy = 0
        if r.get("triggered_test1") and ((r.get("diag_n_first_pass_pixels") or 0) + (r.get("diag_n_second_pass_recapture") or 0)) > 0 \
           and (r.get("diag_n_dnti_ctx_path") or 0) == 0 and (r.get("diag_n_nti_path") or 0) == 0:
            c["only_test1_source con mascara contextual NO vacia"] += 1
        casos.append([{k: r.get(k) for k in bp.CAMPOS_JS}, float(v["inner_radius_km"])]); meta.append((name, b, r))
pred = bp.correr_node(casos)
PUB = collections.defaultdict(collections.Counter)
for (name, b, r), (summit, valid, art, disp, pub) in zip(meta, pred):
    c = PUB[b]; pc = r.get("primary_cluster") or {}
    c["n"] += 1; c["publicada"] += pub; c["artefacto_termico(display)"] += art
    if pub and r.get("discarded_reason"): c["publicada CON discarded_reason=" + r["discarded_reason"]] += 1
    if pub and (r.get("vrp_mw") or 0) == 0: c["publicada con vrp_mw==0"] += 1
    if not pub and valid and not summit: c["no publicada: valida pero no summit"] += 1
    if not pub and valid and summit and not art and disp <= 0: c["no publicada: summit+valida, disp<=0 (cerca pc>inner)"] += 1
    if pub and pc.get("single_pixel_mode") and (pc.get("n_pixels") or 0) > 1: c["publicada y single_pixel cambia"] += 1
    if pub and pc.get("d9_capped"): c["publicada y d9_capped"] += 1
    if pub and name == "Villarrica" and (pc.get("n_pixels") or 0) > 12: c["Villarrica publicada con pc.n_pixels>12"] += 1
    if name == "Villarrica" and (pc.get("n_pixels") or 0) > 12: c["Villarrica pc.n_pixels>12"] += 1
    if pub and r.get("final_hotspot_source") == "cluster_rescue": c["publicada por cluster_rescue"] += 1
    if pub and r.get("diag_a46_relabel"): c["publicada con a46_relabel (no deberia)"] += 1
out = {"desde": DESDE, "huellas": {b: dict(c) for b, c in C.items()}, "publicacion": {b: dict(c) for b, c in PUB.items()}}
json.dump(out, open(os.path.join(here, "huellas_en_records.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
for sec in ("huellas", "publicacion"):
    for b in ("VIIRS375", "VIIRS750", "MODIS"):
        print("==", sec, b)
        for k, n in sorted(out[sec].get(b, {}).items()): print("  ", k, n)
