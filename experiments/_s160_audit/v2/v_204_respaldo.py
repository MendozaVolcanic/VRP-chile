"""204: el respaldo de clase del tablero (index.html:3034-3036) corre sólo si falta distance_class y hay pixeles.
Cuenta records Tier A por (sin distance_class, tiene anomaly_pixels, tiene final_hotspot, pc.vrp_mw>0).
Pregunta 1: si el respaldo corriera, habria filas (True, True, ...) o (True, False, True, ...)."""
import json, collections, sys
sys.stdout.reconfigure(encoding="utf-8")
c = collections.Counter()
for v in ['Lascar','Lastarria','Isluga','Tupungatito','PlanchonPeteroa','NevadosDeChillan','Llaima','Villarrica','Copahue','PuyehueCordonCaulle','Chaiten']:
    for r in json.load(open(rf"D:\vrp-trabajo\temporales\s160_audit\main\data\mirova_equivalent\{v}.json", encoding="utf-8"))["records"]:
        dc = r.get("distance_class"); ap = bool(r.get("anomaly_pixels")); fh = r.get("final_hotspot_lat") is not None
        c[(dc is None, ap, fh, (r.get("primary_cluster") or {}).get("vrp_mw", 0) > 0 if r.get("primary_cluster") else None)] += 1
out = "\n".join(f"{k} {v}" for k, v in sorted(c.items(), key=str))
print(out)
open(__file__.replace("v_204_respaldo.py", "v_204_respaldo_salida.txt"), "w", encoding="utf-8").write(out + "\n")
