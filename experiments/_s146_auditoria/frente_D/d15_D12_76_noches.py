# -*- coding: utf-8 -*-
"""d15: divergencia D12, nota S125 del catalogo: el A/B S121 'cura 76 noches de Lascar' / AUDIT_S121: '76 noches de FN recuperadas (reales)'.
Ventana del A/B: 2025-02-15..05-15. (a) existe ground truth MIROVA en esa ventana? (fecha minima del CSV, CONS u OCR, global y Lascar);
(b) tasa base: en cuantas noches de Lascar MODIS de esa ventana hay HOY un cumulo con magnitud dentro del inner (sin mirar la etiqueta).
Instrumento: (1) si el loader estuviera roto min_fecha seria None: se imprime n de alertas. (2) idem."""
import io, sys, os, json
from dlib import *
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, ROOT); os.environ["VRP_PROFILE"] = "mirova_equivalent"
from pipeline.mirova_csv_loader import load_mirova_alertas
SNAP = os.path.join(ROOT, "data", "mirova_reference", "mirova_v1_snapshot")
al = load_mirova_alertas(cons_path=os.path.join(SNAP, "registro_vrp_consolidado.csv"), ocr_path=os.path.join(SNAP, "registro_vrp_ocr.csv"))
fs = sorted((a.get("fecha_utc") or "")[:10] for a in al if a.get("fecha_utc"))
fl = sorted((a.get("fecha_utc") or "")[:10] for a in al if a.get("fecha_utc") and a["volcano"] == "Lascar")
out = {"n_alertas": len(al), "gt_fecha_min": fs[0], "gt_fecha_max": fs[-1], "gt_lascar_min": fl[0],
       "alertas_en_ventana_AB_2025-02-15_05-15": sum(1 for f in fs if "2025-02-15" <= f <= "2025-05-15")}
D = cargar(); noches = set(); con = set()
for r in D["Lascar"]:
    f = r["datetime_utc"][:10]
    if not ("2025-02-15" <= f <= "2025-05-15") or bucket(r["sensor"]) != "modis": continue
    noches.add(f); pc = r.get("pc") or {}
    if (pc.get("vrp_mw") or 0) > 0 and pc.get("centroid_dist_km") is not None and pc["centroid_dist_km"] <= 5: con.add(f)
out["lascar_modis_noches_en_ventana"] = len(noches); out["con_cumulo_dentro_del_inner"] = len(con)
json.dump(out, open("d15_D12_76_noches.json", "w"), indent=1); print(json.dumps(out, indent=1))
