# -*- coding: utf-8 -*-
"""§5 de la regla: media de d con IC bootstrap y prueba de signos en pares que cambian, por sensor, V1 y V2.
Y cruces de 1 MW con la tabla con OCR en V2."""
import json, sys, random, math, statistics
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
RAIZ = Path(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile")
sys.path.insert(0, str(RAIZ / "experiments" / "_s151_prereg_fk_11"))
import evaluar_fk as E
REP = Path(r"C:\Users\nmend\AppData\Local\Temp\claude\verif_fk_v2\rep")
def binom_p(k, n):
    # dos colas, p=0.5
    m = min(k, n - k)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(m + 1)) / 2 ** n)
for w, tmpn in (("V1", "tmp_v1"), ("V2", "tmp_v2")):
    cfg = dict(E.VENTANAS[w])
    T = json.load(open(REP / tmpn / "t_C0_K.json", encoding="utf-8"))["pasadas"]
    for s in E.SENS:
        D = E.diferencias_magnitud(T, s, cfg)
        if not D: print(w, s, "sin pares"); continue
        d = [x[1] for x in D]; r = [x[2] for x in D]
        ch = [x for x in D if abs(x[2]) > 1e-12]
        rnd = random.Random(0); ms = sorted(statistics.mean(rnd.choice(d) for _ in d) for _ in range(2000))
        pos = sum(1 for x in ch if x[1] > 0); neg = sum(1 for x in ch if x[1] < 0)
        baja = sum(1 for x in ch if x[2] < 0)
        print("%s %-8s pares %3d | cambian %3d (K bajo C0 en %3d; mediana log10(K/C0) en los que cambian %+.3f) | media d %+.3f [%+.3f, %+.3f] | d>0 %d d<0 %d p signos %.2g | razon mediana C0 %.3f K %.3f" % (
            w, s, len(D), len(ch), baja, statistics.median(x[2] for x in ch) if ch else float('nan'), statistics.mean(d), ms[50], ms[1949], pos, neg, binom_p(pos, pos + neg) if pos + neg else float('nan'),
            statistics.median(x[3] for x in D), statistics.median(x[4] for x in D)))
# cruces con OCR (V2)
T = json.load(open(REP / "tmp_v2_ocr" / "t_C0_K.json", encoding="utf-8"))["pasadas"]
cfg = dict(E.VENTANAS["V2"]); cfg["solo_tabla"] = False
ref = E.archivos_ref(cfg, REP / "tmp_v2_ocr")
prot = E.proteccion(set(T), ref, cfg["desde"], cfg["hasta"])
for k, v in sorted(T.items()):
    if len(v) != 2 or not E.decide_sensor(k, cfg): continue
    a, b = v["control"], v["brazo"]
    if prot[k]["A"] and a["pub"] and (a["disp"] or 0) >= 1 and (not b["pub"] or (b["disp"] or 0) < 1):
        print("V2 con OCR: protegida A que C0 muestra >=1 y K deja bajo 1 o calla:", k, a["disp"], b["disp"] if b["pub"] else "calla")
