"""209: cuantos cumulos tienen el modo de un pixel aplicado con 2 o 3 pixeles (unico caso en que maximo != suma),
por sensor, antes y desde 2026-09-18; si en V375 traen f5_core_vrp_mw (el tablero publica el nucleo F5).
Pregunta 1: si el modo no existiera, spm_total seria 0. Denominador: spm_total por sensor y ventana."""
import json, collections, sys
sys.stdout.reconfigure(encoding="utf-8")
c = collections.Counter()
V = ['Lascar','Lastarria','Isluga','Tupungatito','PlanchonPeteroa','NevadosDeChillan','Llaima','Villarrica','Copahue','PuyehueCordonCaulle','Chaiten']
for v in V:
    for r in json.load(open(rf"D:\vrp-trabajo\temporales\s160_audit\main\data\mirova_equivalent\{v}.json", encoding="utf-8"))["records"]:
        pc = r.get("primary_cluster") or {}
        s = r.get("sensor", ""); b = "MODIS" if s.startswith("MODIS") else "V750" if s.endswith("_750") else "V375"
        w = "desde0918" if r.get("datetime_utc", "") >= "2026-09-18" else "antes"
        if pc.get("single_pixel_mode") and (pc.get("n_pixels") or 0) >= 2:
            c[(w, b, "spm_n2a3")] += 1
            if r.get("f5_core_vrp_mw") is not None: c[(w, b, "spm_n2a3_con_f5")] += 1
            if r.get("distance_class") == "summit" and (pc.get("vrp_mw") or 0) > 0: c[(w, b, "spm_n2a3_summit_vrp>0")] += 1
        if pc.get("single_pixel_mode"): c[(w, b, "spm_total")] += 1
out = "\n".join(f"{k} {c[k]}" for k in sorted(c))
print(out)
open(__file__.replace("v_209_spm.py", "v_209_spm_salida.txt"), "w", encoding="utf-8").write(out + "\n")
