# -*- coding: utf-8 -*-
"""Que perfiles de pipeline/profiles/*.yaml resuelven la via de MODIS encendida en main 438a60a1e (A89: se lee de
pipeline.profile en un proceso por perfil, no del YAML). Control: mirova_equivalent tiene que dar True y
guardia_k_modis False. Denominador: los YAML de pipeline/profiles/ sin la carpeta _archive."""
import io, sys, os, glob, subprocess, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = r"D:\vrp-trabajo\temporales\s179-audit\a\base"
os.chdir(BASE)
res, enc, err = collections.Counter(), [], []
for f in sorted(glob.glob("pipeline/profiles/*.yaml")):
    p = os.path.basename(f)[:-5]
    r = subprocess.run([sys.executable, "-c", "import pipeline.profile as p; print(p.ENABLE_MODIS_CODIGO_MIROVA)"],
                       env=dict(os.environ, VRP_PROFILE=p, PYTHONIOENCODING="utf-8"), capture_output=True, text=True)
    out = (r.stdout.strip().splitlines() or ["ERROR"])[-1]
    res[out] += 1
    if out == "True": enc.append(p)
    if out == "ERROR": err.append(p)
print("perfiles:", sum(res.values()), dict(res))
print("control: mirova_equivalent encendido:", "mirova_equivalent" in enc, "| guardia_k_modis encendido:", "guardia_k_modis" in enc)
print("con la via de MODIS encendida (", len(enc), "):"); print(" ", ", ".join(enc))
print("de ellos, con «_k» o «k_» en el nombre:", [p for p in enc if "_k_" in p or p.endswith("_k") or "_k" in p])
if err: print("no cargan:", err)
