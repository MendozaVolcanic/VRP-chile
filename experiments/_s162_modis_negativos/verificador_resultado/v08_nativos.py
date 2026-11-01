# -*- coding: utf-8 -*-
"""Verificador, R2 (recorte nativo 403 de 403): abro CADA nativo_<id>.npz del run, compruebo capas, formas no vacias,
coherencia con el record (forma, rebanadas, granulo) y que la posicion del volcan (centro de la grilla) cae dentro del
recorte en lat/lon del MxD03 para las evaluables. Pregunta 1: un .npz vacio, truncado o de otro granulo saldria
listado. Pregunta 2: imprimo cuantos abri; si no abriera ninguno se veria 0."""
import json, sys, collections
from pathlib import Path
import numpy as np
D, RUN = Path(sys.argv[1]), Path(sys.argv[2])
obj = {o["id"]: o for o in json.loads((D / "objetivos_neg_resto_modis.json").read_text(encoding="utf-8"))}
res = {}
for f in sorted(RUN.rglob("resultados_MODIS_*.json")):
    for r in json.loads(f.read_text(encoding="utf-8")): res[r["id"]] = r
CAPAS = ["lat_mxd03", "lon_mxd03", "lat_5km", "lon_5km", "b21", "b22", "b31", "linea", "frame", "sensor_zenith", "sensor_azimuth", "rebanadas", "forma_granulo"]
abiertos, malos, fuera, formas = 0, [], [], collections.Counter()
for i, r in sorted(res.items()):
    n = r.get("nativo") or {}
    fs = list(RUN.rglob(f"nativo_{i:04d}.npz"))
    if not n.get("guardado") or not fs:
        malos.append((i, "sin archivo o no guardado", n)); continue
    try:
        z = np.load(fs[0])
    except Exception as e:
        malos.append((i, "no abre", str(e))); continue
    abiertos += 1
    faltan = [c for c in CAPAS if c not in z.files]
    if faltan: malos.append((i, "faltan capas", faltan)); continue
    lat = z["lat_mxd03"]; forma = list(lat.shape)
    if forma != n["forma"] or lat.size == 0: malos.append((i, "forma", forma, n["forma"])); continue
    if list(z["rebanadas"]) != n["rebanadas"] or list(z["forma_granulo"]) != n["forma_granulo"]: malos.append((i, "rebanadas", list(z["rebanadas"]), n["rebanadas"])); continue
    if n["l1b"] != r.get("granule"): malos.append((i, "granulo distinto", n["l1b"], r.get("granule"))); continue
    for c in ("b21", "b22", "b31", "lat_mxd03"):
        if z[c].shape != lat.shape: malos.append((i, "capa con otra forma", c)); break
    if np.isfinite(lat).sum() == 0: malos.append((i, "lat toda NaN")); continue
    formas[(forma[0] >= 136, forma[1])] += 0
    g = obj[i]["grilla"]
    ok = np.isfinite(lat) & np.isfinite(z["lon_mxd03"])
    if r.get("estado") == "ok":
        d = np.hypot((lat - g["centro_lat"]) * 111.32, (z["lon_mxd03"] - g["centro_lon"]) * 111.32 * np.cos(np.radians(g["centro_lat"])))
        dmin = float(np.nanmin(np.where(ok, d, np.nan)))
        if dmin > 1.5: fuera.append((i, obj[i]["volcan"], round(dmin, 2)))
print("npz abiertos:", abiertos, "de", len(res), "| defectos:", len(malos), malos[:15])
print("evaluables (estado ok) cuyo recorte NO contiene el centro de la grilla a <1,5 km:", len(fuera), fuera[:10])
ev = [i for i, r in res.items() if r.get("estado") == "ok" and (r["port"]["fisica"] or {}).get("motivo_vacio") != "escena_invalida" and r.get("port_estado") != "grilla_incompleta"]
print("evaluables:", len(ev), "con nativo guardado y sano:", sum(1 for i in ev if i not in {m[0] for m in malos}))
tam = sum(f.stat().st_size for f in RUN.rglob("nativo_*.npz")) / 1e6
print(f"tamano total nativos: {tam:.1f} MB; grillas: {sum(f.stat().st_size for f in RUN.rglob('grilla_*.npz'))/1e6:.1f} MB (prereg: <=289 MB cota, ~126 MB optimista)")
# forma del recorte: filas (136 = 51 km + margen) y columnas variables (por el bow tie / ancho de pixel)
fs = collections.Counter(tuple(r["nativo"]["forma"]) for r in res.values() if r.get("nativo"))
print("formas mas comunes:", fs.most_common(6), "| filas distintas de 136:", sorted({k[0] for k in fs if k[0] != 136}))
