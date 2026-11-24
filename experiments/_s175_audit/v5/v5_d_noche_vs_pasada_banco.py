# -*- coding: utf-8 -*-
"""V5-D: 304 por otro camino. El auditor uso el port Python del audit (port_dash). Aqui uso el PREDICADO DEL TABLERO con node
(recs del banco, campo pub; regla A97) y las etiquetas del banco (lab == 'pos', D-9 SN).
Pregunta 1: si 'noche cuenta otra pasada' fuera falso, esta tabla daria noches_hit_solo_otra_pasada = 0 en todas las ventanas/estratos.
Pregunta 2: control positivo: ventana ancha del banco (2026-06-11..2026-11-07) y 'pub' forzado a 1 en todo => noche y pasada coinciden por construccion
(todas las noches con pos tienen acierto en su propia pasada); si el instrumento estuviera muerto daria lo mismo en ambos y no veria el control.
Universo: recs lab=='pos' (pasada nuestra pareada a una alerta de MIROVA, +-120 s) por (volcan, bucket, noche). Denominador: noches con >=1 pasada pos.
Nota: aqui la noche tiene denominador distinto (pasadas con record pareado a alerta); el auditor usaba noches de alerta con record. Se informan ambos conteos.
"""
import collections, os, pickle, sys
sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"C:\Users\nmend\vrp-temporales\s175_audit\f5\root"
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "scripts"))
B = pickle.load(open(r"C:\Users\nmend\vrp-temporales\s175_audit\f5\f5_base.pkl", "rb"))
def tabla(recs, desde, hasta, forzar=False):
    noches = collections.defaultdict(lambda: {"pos": 0, "pos_pub": 0})
    for r in recs:
        if r["lab"] != "pos" or not (desde <= r["noche"] <= hasta):
            continue
        k = (r["b"], r["vol"], r["noche"])
        noches[k]["pos"] += 1
        noches[k]["pos_pub"] += 1 if forzar else r["pub"]
    res = collections.defaultdict(collections.Counter)
    for (b, vol, n), v in noches.items():
        res[b]["noches_con_pos"] += 1
        res[b]["noches_hit_alguna_pasada"] += v["pos_pub"] > 0
        res[b]["noches_hit_solo_si_fuera_toda_pasada"] += 0
        res[b]["pasadas_pos"] += v["pos"]
        res[b]["pasadas_pos_pub"] += v["pos_pub"]
        res[b]["noches_con_pos_donde_alguna_pasada_pos_no_publica_y_otra_si"] += (0 < v["pos_pub"] < v["pos"])
        res[b]["noches_con_pos_todas_no_publican"] += v["pos_pub"] == 0
    return res
for nombre, d, h, f in (("ventana_audit 2026-09-03..2026-11-02", "2026-09-03", "2026-11-02", False),
                        ("ventana_banco 2026-06-11..2026-11-07", "2026-06-11", "2026-11-07", False),
                        ("CONTROL pub forzado=1 (ventana_audit)", "2026-09-03", "2026-11-02", True)):
    print("##", nombre)
    for b, c in sorted(tabla(B["recs"], d, h, f).items()):
        n, hit, p, pp = c["noches_con_pos"], c["noches_hit_alguna_pasada"], c["pasadas_pos"], c["pasadas_pos_pub"]
        print(f"  {b}: noches {n} hit_noche {hit} ({100*hit/n:.1f}%) | pasadas {p} hit_pasada {pp} ({100*pp/p:.1f}%) | brecha noche-pasada {100*hit/n-100*pp/p:+.1f} pts | "
              f"noches con una pasada que no publica y otra que si: {c['noches_con_pos_donde_alguna_pasada_pos_no_publica_y_otra_si']}")
