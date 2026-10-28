# -*- coding: utf-8 -*-
"""VF4: ¿el control de identidad §8.2 (misma máscara, cero tolerancia) puede dar rojo SOLO por cuantización float32?
Las grillas del censo se guardaron en float32 (grilla_NNN.npz: 'mir','tir'); el runner computa V desde el HDF en float64.
Aquí se perturba cada grilla guardada con ruido relativo uniforme de ±6e-8 (medio ulp de float32; también ±1e-6 como
sensibilidad) y se compara la máscara de detectar_mirova contra la de la grilla tal cual. Solo lectura. Python -I."""
import glob, json, random, sys, time
from pathlib import Path
import numpy as np, yaml
RAIZ = Path(sys.argv[1])
sys.path.insert(0, str(RAIZ))
from pipeline import mirova_v750_codigo as MV
from pipeline.geo_utils import get_detection_anchor
CENSO = Path(r"D:\vrp-trabajo\temporales\s162_modd\censo")
N = int(sys.argv[2]) if len(sys.argv) > 2 else 400
vols = {v["name"]: v for v in yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
filas = []
for p in sorted(CENSO.glob("run_*/*/ab_parte*.jsonl")):
    for l in open(p, encoding="utf-8"):
        r = json.loads(l)
        if r.get("tipo") == "record" and (p.parent / ("grilla_%03d.npz" % r["id"])).exists():
            filas.append((p.parent, r))
print("filas con grilla:", len(filas))
random.seed(166)
alert = [x for x in filas if x[1].get("lab") in ("protegida", "bajo1")]
resto = [x for x in filas if x[1].get("lab") not in ("protegida", "bajo1")]
muestra = alert + random.sample(resto, max(0, N - len(alert)))
rng = np.random.default_rng(166)
res = {6e-8: [0, 0, 0], 1e-6: [0, 0, 0], 1e-5: [0, 0, 0]}   # flips, n, celdas_alertadas_totales
t0 = time.time(); errores = 0
for d, r in muestra:
    f = d / ("grilla_%03d.npz" % r["id"])
    if not f.exists():
        errores += 1; continue
    z = np.load(f)
    v = vols[r["vol"]]
    fam = MV.FAMILIAS["MODIS"]
    g = MV.grilla_del_volcan(r["vol"], paso_m=fam["paso_m"], clave_roi=fam["clave_roi"])
    vl, vo = get_detection_anchor(v)
    box = MV.caja_roi(g.get("roi", "def"), n=g["n"], celda_crater=MV.celda_de(g, vl, vo), inner_km=r["inner"],
                      lado_sensible=fam["lado_sensible"], lado_anillo=fam["lado_anillo"], paso_m=g["paso"])
    m13, m15 = z["mir"].astype(float), z["tir"].astype(float)
    base = MV.detectar_mirova(m13, m15, box, r["dayflag"], r["sunglint"], lam_mir=fam["lam_mir"], lam_tir=fam["lam_tir"])
    for eps in res:
        a = m13 * (1 + rng.uniform(-eps, eps, m13.shape)); b = m15 * (1 + rng.uniform(-eps, eps, m15.shape))
        m = MV.detectar_mirova(a, b, box, r["dayflag"], r["sunglint"], lam_mir=fam["lam_mir"], lam_tir=fam["lam_tir"])
        res[eps][0] += int((m != base).any()); res[eps][1] += 1; res[eps][2] += int(base.sum())
print("sin grilla/archivo:", errores, "| t=%.0fs" % (time.time() - t0))
for eps, (fl, n, na) in res.items():
    print("ruido relativo +-%g: pasadas con máscara distinta %d de %d (celdas alertadas base: %d)" % (eps, fl, n, na))
