# -*- coding: utf-8 -*-
"""EJE 2 (S138): cuanto pesan en los records operacionales los mecanismos que el
codigo tiene y el paper SP426.5 no.

Denominador: todos los records de data/mirova_equivalent/<TierA>.json, por bucket
de sensor (MODIS / VIIRS375 = VIIRS_* sin sufijo / VIIRS750 = *_750), con la
ventana temporal min-max de datetime_utc de cada bucket (regla A90).

Las dos preguntas del instrumento: cada conteo se acompana de su denominador y de
un control positivo (un campo que seguro existe en todos los records, `sensor`),
para distinguir "no hay" de "no medi". Un campo ausente en TODOS los records
de un bucket se reporta como SIN DATO, no como 0.
"""
import io
import json
import os
import sys
from collections import Counter, defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DATA = os.path.join(ROOT, "data", "mirova_equivalent")
TIER_A = ["PuyehueCordonCaulle", "Villarrica", "Lascar", "Copahue", "NevadosDeChillan",
          "Llaima", "Chaiten", "PlanchonPeteroa", "Lastarria", "Isluga", "Tupungatito"]
OUT = os.path.join(os.path.dirname(__file__), "02_records_operacionales_resultado.json")


def bucket(sensor):
    s = str(sensor or "")
    if s.startswith("MODIS"):
        return "MODIS"
    if s.startswith("VIIRS"):
        return "VIIRS750" if s.endswith("_750") else "VIIRS375"
    return "OTRO"


stats = defaultdict(Counter)
presence = defaultdict(Counter)
window = defaultdict(lambda: ["9999", "0000"])
per_vol = defaultdict(Counter)

for vol in TIER_A:
    p = os.path.join(DATA, f"{vol}.json")
    if not os.path.exists(p):
        print("SIN ARCHIVO", p); continue
    recs = json.load(open(p, encoding="utf-8")).get("records", [])
    for r in recs:
        b = bucket(r.get("sensor"))
        st = stats[b]; pr = presence[b]
        st["n_records"] += 1
        per_vol[vol][b] += 1
        dt = r.get("datetime_utc") or ""
        if dt < window[b][0]: window[b][0] = dt
        if dt > window[b][1]: window[b][1] = dt
        for k in ("diag_n_first_pass_pixels", "diag_n_second_pass_recapture", "diag_n_nti_path",
                  "primary_cluster", "final_hotspot_source", "f5_core_vrp_mw", "vrp_mw",
                  "distance_class", "triggered_test1", "sensor"):
            if k in r: pr[k] += 1
        pc = r.get("primary_cluster") or {}
        fp = r.get("diag_n_first_pass_pixels")
        sp = r.get("diag_n_second_pass_recapture")
        n_anom = r.get("n_anomalous_pixels") or 0
        if pc: st["con_cluster"] += 1
        if n_anom > 0: st["con_pixeles_hot"] += 1
        if fp is not None and sp is not None:
            if fp == 0 and sp > 0: st["deteccion_SOLO_segundo_pase(fp=0,sp>0)"] += 1
            if fp > 0: st["primer_pase>0"] += 1
            if sp > 0: st["segundo_pase>0"] += 1
        if r.get("diag_n_nti_path", 0) and r.get("diag_n_nti_path", 0) > 0:
            st["test1_K1_dispara(n_nti_path>0)"] += 1
            if fp == 0: st["K1_dispara_y_primer_pase=0"] += 1
        if r.get("final_hotspot_source") == "test1": st["fuente=test1_integrado"] += 1
        if r.get("triggered_test1"): st["triggered_test1"] += 1
        if pc.get("single_pixel_mode"): st["pc.single_pixel_mode"] += 1
        if pc.get("focal_magnitude"): st["pc.focal_magnitude"] += 1
        if pc.get("d9_capped"): st["pc.d9_capped"] += 1
        if pc.get("corona_degraded") is not None: st["pc.corona_evaluada"] += 1
        if pc and pc.get("vrp_mw") is not None and r.get("vrp_mw") is not None:
            if abs(float(pc["vrp_mw"]) - float(r["vrp_mw"])) > 1e-6:
                st["pc.vrp_mw != vrp_mw(suma escena)"] += 1
        if "f5_core_vrp_mw" in r and pc.get("vrp_mw") is not None:
            if abs(float(r["f5_core_vrp_mw"]) - float(pc["vrp_mw"])) > 1e-6:
                st["f5_core != pc.vrp_mw"] += 1
        if r.get("distance_class") == "far" and pc.get("geo_class") == "summit":
            st["far_por_final_hotspot_pero_cluster_summit"] += 1
        if r.get("discarded_reason"): st["discarded_reason_presente"] += 1
        if r.get("diag_vrp_floor_mw"): st["piso_vrp_aplicado"] += 1
        if r.get("vrp_exceeds_sanity_cap") or r.get("diag_rejected_sanity_cap_mw"):
            st["sanity_cap_tocado"] += 1

out = {}
for b in sorted(stats):
    n = stats[b]["n_records"]
    out[b] = {"ventana_utc": window[b], "n_records": n,
              "conteos": {k: v for k, v in sorted(stats[b].items())},
              "porcentaje_sobre_n_records": {k: round(100.0 * v / n, 2) for k, v in sorted(stats[b].items())},
              "campos_presentes_(control: sensor=n)": dict(presence[b])}
out["por_volcan"] = {v: dict(c) for v, c in per_vol.items()}
json.dump(out, open(OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(json.dumps(out, indent=2, ensure_ascii=False))
