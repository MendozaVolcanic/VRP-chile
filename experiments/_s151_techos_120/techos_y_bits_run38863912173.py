# -*- coding: utf-8 -*-
"""Tarea 1.20: techos de LUT y bit de saturacion por plataforma, desde los JSON por tramo del run
38863912173 (copiados de C:/Users/nmend/AppData/Local/Temp/claude/verif_118/tramos/ a ../tramos/).
Campos del probe: techos_lut_k (max de la LUT del granulo), n_bit_granulo_entero (pixeles con bit 4 en
el granulo entero), conteo[banda][zona][borrado|bit|techo] (borrados por produccion en la caja de 25 km).
"""
import sys, io, json, glob, collections, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tramos")
lut = collections.defaultdict(set); ngr = collections.Counter(); bit = collections.Counter(); grbit = collections.Counter()
borr = collections.Counter(); ventana = [None, None]
for f in sorted(glob.glob(os.path.join(base, "*", "sat_*.json"))):
    d = json.load(open(f, encoding="utf-8"))
    for p in d["pasadas"]:
        if p.get("estado") != "ok":
            continue
        pl = p["plataforma"]; ngr[pl] += 1
        dt = p["datetime_utc"]; ventana = [min(ventana[0] or dt, dt), max(ventana[1] or dt, dt)]
        for b, v in (p.get("techos_lut_k") or {}).items():
            lut[(pl, b)].add(round(v, 2))
        for b, v in (p.get("n_bit_granulo_entero") or {}).items():
            bit[(pl, b, "noche" if p["noche"] else "dia")] += v
            if v: grbit[(pl, b, "noche" if p["noche"] else "dia")] += 1
        for b, c in p["conteo"].items():
            for z in ("interior", "escena"):
                for k in ("borrado", "bit", "techo"):
                    borr[(d["familia"], b, z, k)] += c[z][k]
out = {"ventana": ventana, "granulos_ok_por_plataforma": dict(ngr),
       "techos_lut_k": {f"{a}|{b}": sorted(v) for (a, b), v in sorted(lut.items())},
       "pixeles_bit_granulo_entero": {"|".join(k): v for k, v in sorted(bit.items()) if v},
       "granulos_con_bit": {"|".join(k): v for k, v in sorted(grbit.items())},
       "borrados_caja25km_M15_y_I04": {"|".join(k): v for k, v in sorted(borr.items()) if k[1] in ("M15", "I04")}}
print(json.dumps(out, indent=1, ensure_ascii=False))
json.dump(out, open(__file__.replace(".py", ".json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
