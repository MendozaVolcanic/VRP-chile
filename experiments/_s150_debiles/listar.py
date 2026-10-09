# -*- coding: utf-8 -*-
"""S150. Lista las alertas que B publica y F no (filas.json de perdidas_max.py) con sus diagnosticos.
  python listar.py filas.json
"""
import io, json, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
F = json.load(open(sys.argv[1], encoding="utf-8"))
SAT = {"VIIRS_SNPP": "SNPP", "VIIRS_NOAA20": "N20", "VIIRS_NOAA21": "N21"}


def sat(s):
    s = s or ""
    for k, v in SAT.items():
        if s.startswith(k):
            return v
    return s


def f(x, n=3):
    return "-" if x is None else ("%.*f" % (n, x))


MALAS = {"Lastarria|VIIRS375|2026-05-02 05:06", "Isluga|VIIRS375|2026-05-29 04:54", "Lascar|VIIRS375|2026-06-25 04:54",
         "Lascar|VIIRS375|2026-08-17 05:00", "Lascar|VIIRS375|2026-08-22 05:06"}
if len(sys.argv) > 2 and sys.argv[2] == "--md":
    print("| # | volcán | sensor | pasada UTC | sat. | MIROVA MW | origen | cenit ° | t_bg K | σ BT anillo K | umbral F dNTI (μ+5σ) | umbral F dETI (μ+5σ) | B: px 1.er pase / 2.o pase | B: VRP cúmulo MW, dist km | B: BT píxel − t_bg K | F: px, cúmulo dist km |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(sorted((x for x in F if x["perdida"]), key=lambda x: (x["b"], x["dt"])), 1):
        b, ff = r["B"], r["F"] or {}
        m = r["mirova"][0] if r["mirova"] else {}
        exc = (b["ap_bt_max"] - b["t_bg_k"]) if b.get("ap_bt_max") and b.get("t_bg_k") else None
        orig = ("solo OCR" if r["solo_ocr"] else "tabla") + (" (imagen de otra pasada)" if r["clave"] in MALAS else "")
        print("| %d | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s / %s | %s, %s | %s | %s, %s |" % (
            i, r["vol"], r["b"], r["dt"], sat(b["sensor"]), f(m.get("vrp_mw"), 2), orig, f(b["sensor_zenith_deg"], 1),
            f(b["t_bg_k"], 1), f(b["diag_sigma_bg_k"], 2), f(b.get("stat_dnti_s"), 4), f(b.get("stat_deti_s"), 4),
            b["diag_n_first_pass_pixels"], b["diag_n_second_pass_recapture"], f(b["pc_vrp"]), f(b["pc_dist"], 1), f(exc, 1),
            ff.get("n_anomalous_pixels"), f(ff.get("pc_dist"), 1)))
    sys.exit(0)
print("mes|volcan|sensor|pasada UTC|sat|MIROVA MW|fuente|dist MIROVA|ult.act OCR|cenit|t_bg|sigma_bg K|mu+5sd dNTI|mu+5sd dETI|B: n1p n2p npx pc_vrp pc_dist bt-tbg|F: npx n1p n2p pc_dist pc_vrp")
for r in sorted((x for x in F if x["perdida"]), key=lambda x: (x["b"], x["dt"])):
    b, ff = r["B"], r["F"] or {}
    m = r["mirova"][0] if r["mirova"] else {}
    exc = (b["ap_bt_max"] - b["t_bg_k"]) if b.get("ap_bt_max") and b.get("t_bg_k") else None
    print("|".join([r["mes"], r["vol"], r["b"], r["dt"], sat(b["sensor"]), f(m.get("vrp_mw"), 2),
                    ("OCR" if r["solo_ocr"] else "tabla"), f(m.get("dist_km"), 2), (m.get("ultima_actualizacion") or "")[11:16],
                    f(b["sensor_zenith_deg"], 1), f(b["t_bg_k"], 1), f(b["diag_sigma_bg_k"], 2),
                    f(b.get("stat_dnti_s"), 4), f(b.get("stat_deti_s"), 4),
                    "%s %s %s %s %s %s" % (b["diag_n_first_pass_pixels"], b["diag_n_second_pass_recapture"], b["n_anomalous_pixels"], f(b["pc_vrp"]), f(b["pc_dist"], 1), f(exc, 1)),
                    "%s %s %s %s %s" % (ff.get("n_anomalous_pixels"), ff.get("diag_n_first_pass_pixels"), ff.get("diag_n_second_pass_recapture"), f(ff.get("pc_dist"), 1), f(ff.get("pc_vrp")))]))
