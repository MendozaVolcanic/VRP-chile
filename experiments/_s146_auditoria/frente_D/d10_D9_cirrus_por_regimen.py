# -*- coding: utf-8 -*-
"""d10: cierre S113 de la divergencia D9 ('199 records cirrus FAR, 0 fuga al dashboard'; '214 visibles frios+path-D, 207 = 96,7 %
MIROVA-confirmados'). Ventana de S113: mayo-jun 2026, con la mascara de nube de 260 K todavia ACTIVA en VIIRS 375 (se retiro en #535,
2026-08-28). Remide la misma poblacion en (a) 2026-05-01..06-18, (b) regimen actual 09-01..09-19.
Definicion MIA (declarada, la de S113 no esta en ningun script del repo): frio = t_bg_k < 262; path-D dominante =
diag_n_dnti_ctx_path > diag_n_bt_path + diag_n_nti_path + diag_n_eti_path; con pc.vrp>0.
Instrumento: (1) control: (a) debe dar del orden de 199 far y 214 summit con ~97 % confirmados; si no, mi definicion difiere y el resto
es SOSPECHA. (2) n impresos."""
import io, sys, json
from collections import Counter
from dlib import *
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from _s126_lib import cargar_mirova
D = cargar()
def medir(w):
    mir, _ = cargar_mirova(w); res = {}
    for clase in ("far", "summit"):
        n = conf = 0; mx = 0.0; sens = Counter(); tot_pas = Counter(); noconf_mw = []
        for v in VOLS:
            ks = set(mir.get(v) or {})
            for r in D[v]:
                f = r["datetime_utc"][:10]
                if not (w[0] <= f <= w[1]): continue
                b = bucket(r["sensor"])
                if clase == "far": tot_pas[b] += 1
                if pcv(r) <= 0 or r.get("t_bg_k") is None or r["t_bg_k"] >= 262: continue
                d = r.get("diag_n_dnti_ctx_path") or 0
                if d <= (r.get("diag_n_bt_path") or 0) + (r.get("diag_n_nti_path") or 0) + (r.get("diag_n_eti_path") or 0): continue
                if r.get("distance_class") != clase: continue
                n += 1; sens[b] += 1; mx = max(mx, pcv(r)); c = (f, b) in ks; conf += c
                if not c and clase == "summit": noconf_mw.append(round(pcv(r), 2))
        res[clase] = {"n": n, "por_sensor": dict(sens), "mirova_confirmados": conf, "pct": round(100*conf/n, 1) if n else "SIN DATO", "max_pc_vrp": mx}
        if clase == "summit": res[clase]["no_confirmados_n"] = len(noconf_mw); res[clase]["no_confirmados_max_mw"] = max(noconf_mw) if noconf_mw else None
        else: res["pasadas_totales_por_sensor"] = dict(tot_pas)
    return res
out = {"S113(05-01..06-18)": medir(("2026-05-01", "2026-06-18")), "previo_invierno(07-01..08-28)": medir(("2026-07-01", "2026-08-28")), "actual(09-01..09-19)": medir(("2026-09-01", "2026-09-19"))}
json.dump(out, open("d10_D9_cirrus_por_regimen.json", "w"), indent=1); print(json.dumps(out, indent=1))
