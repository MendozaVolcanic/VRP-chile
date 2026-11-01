# -*- coding: utf-8 -*-
"""S155 frente 5: el tope D9 de 5 MW, esta activo o latente en Chillan en erupcion?

POR QUE. El tope recorta a 5 MW el cumulo cuando el disparo es solo contextual (n_bt_path = n_nti_path = 0) y el
fondo del anillo esta bajo 270 K (process_viirs_mod.py:1009-1016, process_viirs.py:1440-1447). En erupcion el NTI
absoluto rara vez pasa -0,8 a 375-1000 m, asi que la primera condicion se cumple casi siempre; queda la del fondo.
Pregunta 1: si el tope recortara, lo veria? Si: d9_capped en el cumulo y vrp_mw exactamente 5,0. Pregunta 2: el
control positivo son los records C0 de MODIS Terra del 2026-09-28, que el JSON trae con vrp_mw = 5,0.
Ventana: records de Chillan 2026-09-28 a 2026-10-19 (todos, haya o no alerta de MIROVA)."""
import io, json, os, sys, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
WT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
recs = json.load(open(os.path.join(WT, "data/mirova_equivalent/NevadosDeChillan.json"), encoding="utf-8"))["records"]
W = [r for r in recs if "2026-09-28" <= r["datetime_utc"] <= "2026-10-19 23:59"]
det = [r for r in W if r.get("primary_cluster")]
cond = [r for r in det if (r.get("n_bt_path") or 0) == 0 and (r.get("n_nti_path") or 0) == 0
        and r.get("t_bg_k") is not None and r["t_bg_k"] < 270.0]
cap = [r for r in det if (r.get("primary_cluster") or {}).get("d9_capped")]
print("records en ventana=%d con cumulo=%d; con las condiciones del tope (solo contextual y t_bg<270)=%d; topados=%d" % (
    len(W), len(det), len(cond), len(cap)))
print("con cumulo y n_nti_path>0: %d ; n_bt_path>0: %d" % (sum(1 for r in det if (r.get('n_nti_path') or 0) > 0),
                                                         sum(1 for r in det if (r.get('n_bt_path') or 0) > 0)))
for r in cap:
    pc = r["primary_cluster"]
    print("  TOPADO %s %s t_bg=%.1f pc=%.3f vrp_mw=%s regimen=%s" % (r["datetime_utc"], r["sensor"], r["t_bg_k"],
          pc["vrp_mw"], r["vrp_mw"], (r.get("regimen") or {}).get("codigo_sha", "C0 (sin regimen)")[:9]))
print("records con cumulo nocturno por t_bg (<270 / >=270):", sum(1 for r in det if r['t_bg_k'] < 270), sum(1 for r in det if r['t_bg_k'] >= 270))
print("records con condiciones del tope cuyo cumulo NO llega a 5 MW (latentes): %d; max pc en ellos %.2f" % (
    sum(1 for r in cond if r["primary_cluster"]["vrp_mw"] < 5), max([r["primary_cluster"]["vrp_mw"] for r in cond] or [0])))
ref = [x for x in csv.DictReader(open("D:/vrp-trabajo/temporales/frente_5/registro_vrp_consolidado_remoto_20261019.csv",
       encoding="utf-8", errors="replace")) if "hill" in x["Volcan"].lower() and x["Fecha_Satelite_UTC"][:13] == "2026-09-28 01"]
print("MIROVA Chillan 2026-09-28 01h:", [(x["Fecha_Satelite_UTC"], x["Sensor"], x["VRP_MW"], x["Tipo_Registro"]) for x in ref])
