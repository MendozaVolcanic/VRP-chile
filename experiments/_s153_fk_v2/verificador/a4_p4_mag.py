# -*- coding: utf-8 -*-
"""Punto 4: P4 (cumulo movido >0,5 km) por direccion, volcan y sensor; cruce de 1 MW entre C0 y K (regla §5);
punto 3/5: protegidas A que deciden, por volcan y sensor."""
import json, sys, collections, statistics, math
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
RAIZ = Path(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile")
sys.path.insert(0, str(RAIZ / "experiments" / "_s151_prereg_fk_11"))
import evaluar_fk as E
REP = Path(r"C:\Users\nmend\AppData\Local\Temp\claude\verif_fk_v2\rep")
inner = E.bp.inner_desde_html()
out = {}
for w in ("V1", "V2"):
    cfg = dict(E.VENTANAS[w]); tmp = REP / ("tmp_" + w.lower())
    T = json.load(open(tmp / "t_C0_K.json", encoding="utf-8"))["pasadas"]
    ref = E.archivos_ref(cfg, tmp)
    prot = E.proteccion(set(T), ref, cfg["desde"], cfg["hasta"])
    print("\n######## %s" % w)
    # protegidas A que deciden por volcan y sensor (C0 publica, decide_sensor, sin ocr_snpp en V1)
    c = collections.Counter()
    for k, v in T.items():
        if len(v) == 2 and prot[k]["A"] and v["control"]["pub"] and E.decide_sensor(k, cfg) and not (not cfg["solo_tabla"] and E.ocr_snpp(k, v["control"], prot)):
            c[(k.split("|")[1], k.split("|")[0])] += 1
    for s in E.SENS:
        tot = sum(n for (ss, _), n in c.items() if ss == s)
        print("  protegidas A que deciden %-8s %3d: %s" % (s, tot, ", ".join("%s %d" % (vv, n) for (ss, vv), n in sorted(c.items(), key=lambda x: -x[1]) if ss == s)))
    # P4
    mov = []
    for k, v in T.items():
        if len(v) != 2: continue
        a, b = v["control"], v["brazo"]
        if a["lab"] != "pos" or not (a["pub"] and b["pub"]) or None in (a["pc_lat"], a["pc_lon"], b["pc_lat"], b["pc_lon"]): continue
        d = E.ev._hav(a["pc_lat"], a["pc_lon"], b["pc_lat"], b["pc_lon"])
        if d > E.MOV_KM:
            vol, s, t = k.split("|")
            mov.append({"k": k, "vol": vol, "s": s, "mov_km": round(d, 2), "c0_dist": a["pc_dist"], "k_dist": b["pc_dist"],
                        "inner": inner[vol], "c0_disp": a["disp"], "k_disp": b["disp"], "ref": a["vrp_ref"], "prot": prot[k]["A"],
                        "decide": E.decide_sensor(k, cfg)})
    print("  P4: %d movidas" % len(mov))
    agg = collections.Counter()
    for m in mov:
        dirc = "hacia el crater" if (m["k_dist"] or 0) < (m["c0_dist"] or 0) else "hacia afuera"
        agg[(m["s"], m["vol"], dirc)] += 1
    for x in sorted(agg): print("     %-8s %-20s %-16s %d" % (*x, agg[x]))
    cerca = [m for m in mov if (m["k_dist"] or 0) < (m["c0_dist"] or 0)]
    print("  hacia el crater %d, hacia afuera %d" % (len(cerca), len(mov) - len(cerca)))
    sale = [m for m in mov if (m["c0_dist"] or 0) <= m["inner"] < (m["k_dist"] or 0)]
    entra = [m for m in mov if (m["k_dist"] or 0) <= m["inner"] < (m["c0_dist"] or 0)]
    print("  cruzan el inner_radius: de dentro a fuera %d, de fuera a dentro %d" % (len(sale), len(entra)))
    print("  movidas en protegidas A: %d (%s)" % (sum(m["prot"] for m in mov), [m["k"] for m in mov if m["prot"]][:20]))
    dd = [abs((m["k_dist"] or 0) - (m["c0_dist"] or 0)) for m in mov]
    if mov:
        print("  mov_km mediana %.2f max %.2f | |cambio de radio| mediana %.2f max %.2f" % (statistics.median(m["mov_km"] for m in mov), max(m["mov_km"] for m in mov), statistics.median(dd), max(dd)))
    for m in sorted(mov, key=lambda m: -m["mov_km"])[:12]:
        print("     ", m)
    # cruce de 1 MW
    cr = collections.Counter(); lista = []
    for k, v in T.items():
        if len(v) != 2 or not E.decide_sensor(k, cfg): continue
        a, b = v["control"], v["brazo"]
        if a["lab"] != "pos" or not (a["pub"] and b["pub"]): continue
        if a["disp"] is None or b["disp"] is None: continue
        s = k.split("|")[1]
        if a["disp"] >= 1 > b["disp"]:
            cr[(s, "abajo", prot[k]["A"])] += 1; lista.append((k, "abajo", a["disp"], b["disp"], a["vrp_ref"], prot[k]["A"]))
        elif b["disp"] >= 1 > a["disp"]:
            cr[(s, "arriba", prot[k]["A"])] += 1; lista.append((k, "arriba", a["disp"], b["disp"], a["vrp_ref"], prot[k]["A"]))
    print("  cruce de 1 MW (alertas publicadas por los dos, C0 -> K), (sensor, direccion, protegida A): %s" % dict(sorted(cr.items())))
    for x in lista:
        if x[5] and x[1] == "abajo": print("     PROTEGIDA BAJA DE 1 MW:", x)
    # protegidas que C0 muestra >=1 MW y K bajo 1 MW o no publica
    pb = collections.Counter()
    for k, v in T.items():
        if len(v) != 2 or not prot[k]["A"] or not E.decide_sensor(k, cfg): continue
        a, b = v["control"], v["brazo"]
        if a["pub"] and (a["disp"] or 0) >= 1:
            pb[(k.split("|")[1], "C0>=1")] += 1
            if not b["pub"] or (b["disp"] or 0) < 1: pb[(k.split("|")[1], "K<1 o calla")] += 1
    print("  protegidas A que C0 muestra >=1 MW y cuantas K deja bajo 1 o calla:", dict(sorted(pb.items())))
    out[w] = {"mov": mov, "cruces": lista}
json.dump(out, open(REP.parent / "a4_p4_mag.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
