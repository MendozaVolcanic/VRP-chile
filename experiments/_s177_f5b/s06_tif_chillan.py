# -*- coding: utf-8 -*-
"""s06: ¿hay en disco algún TIF de Chillán con anomalía fuerte para validar el selector de mancha saturada? Sólo lee.
Pre-registro: si el máximo de NTI de los TIF locales de Chillán fuera bajo (< 0,6), no hay control positivo con mancha saturada."""
import glob, os, sys, rasterio, numpy as np
sys.stdout.reconfigure(encoding="utf-8")
T = r"C:\Users\nmend\vrp-temporales\s175_audit\f5b"
for f in sorted(glob.glob(os.path.join(T, "tif_ref", "Chillan*")) + glob.glob(os.path.join(T, "tif_val", "Chillan*"))):
    with rasterio.open(f) as d:
        a = d.read(1).astype(float)
        print(os.path.basename(f), a.shape, "min %.3f max %.3f" % (np.nanmin(a), np.nanmax(a)))
pngs = sorted(os.listdir(os.path.join(T, "png")))
ch = [p for p in pngs if p.startswith("Chillan")]
print("láminas de Chillán en disco:", len(ch), "| primera", ch[0], "| última", ch[-1], "| TIF de validación de Chillán:", len(glob.glob(os.path.join(T, "tif_val", "Chillan*"))))
