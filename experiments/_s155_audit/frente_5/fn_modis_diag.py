# -*- coding: utf-8 -*-
"""S155 frente 5: diagnosticos persistidos de las pasadas con alerta de MIROVA que no publicamos (FN) en la ventana
2026-09-28 a 2026-10-19, y de MODIS en general por cenit. Solo lee el record; no explica por que no disparo el detector
(eso exige el L1B). Pregunta del instrumento: un record sin pixeles no distingue "no habia" de "no se midio"; por eso
se imprimen t_max_k, su distancia y el sigma del fondo: si t_max cae lejos del crater o bajo el umbral efectivo, el
detector SI miro y no vio."""
import json, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
WT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
recs = json.load(open(os.path.join(WT, "data/mirova_equivalent/NevadosDeChillan.json"), encoding="utf-8"))["records"]
QUIEN = {("2026-09-28 04:42", "_750"), ("2026-09-29 07:20", "MODIS"), ("2026-10-12 05:54", "_750"),
         ("2026-10-12 07:20", "MODIS"), ("2026-10-15 01:05", "MODIS")}
campos = ["sensor", "sensor_zenith_deg", "t_bg_k", "t_max_k", "diag_t_max_dist_km", "diag_eff_threshold_k",
          "diag_sigma_bg_k", "diag_nti_max", "diag_nti_bg", "diag_sd_dnti", "diag_n_first_pass_pixels",
          "diag_n_first_pass_summit", "diag_n_second_pass_recapture", "n_anomalous_pixels", "granule"]
for r in recs:
    for t, s in QUIEN:
        if r["datetime_utc"][:16] == t and s in r["sensor"]:
            print(t, {c: r.get(c) for c in campos})
print("\nMODIS nocturnos 2026-10-01..19 (todos los records, haya o no alerta): fecha zen tmax dist_tmax n_anom pc_vrp")
for r in recs:
    if r["sensor"].startswith("MODIS") and "2026-10-01" <= r["datetime_utc"] <= "2026-10-19 23" and (r.get("solar_zenith_deg") or 0) > 90:
        pc = r.get("primary_cluster") or {}
        print(r["datetime_utc"], r["sensor"], r.get("sensor_zenith_deg"), r.get("t_max_k"), r.get("diag_t_max_dist_km"),
              r.get("n_anomalous_pixels"), pc.get("vrp_mw"), pc.get("centroid_dist_km"))
