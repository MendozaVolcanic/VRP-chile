# -*- coding: utf-8 -*-
"""M5 - la grilla de MIROVA leida de los 19 KMZ del repo (pendiente #6 de AUDIT_S128).

POR QUE: el pipeline remuestrea sobre una ventana de semiancho fijo `half_km=25.5`
(pipeline/regrid.py) centrada en la cumbre. Si la ventana que MIROVA publica tiene otro
semiancho -o uno distinto por sensor- entonces el anillo de fondo con que calculamos mu
y sigma no es el mismo trozo de terreno que el de ellos, y los umbrales no son
comparables aunque la formula sea identica.

Los 19 KMZ versionados en `kmz/` son el producto "Last_GE" de mirovaweb: un overlay con
su `<LatLonBox>`. Se mide su centro y su semiancho en km, por volcan y por sensor, contra
`mirova_center_lat/lon` de volcanoes.yaml y contra los 25,5 km del regrid.

Read-only.
"""
import glob
import math
import os
import re
import zipfile

import pandas as pd

import _lib as L

RE_BOX = re.compile(
    r"<north>([-\d.]+)</north>\s*<south>([-\d.]+)</south>\s*"
    r"<east>([-\d.]+)</east>\s*<west>([-\d.]+)</west>", re.S)
ALIAS_KMZ = {"ChillanNevadosde": "NevadosDeChillan"}


def leer_box(path):
    with zipfile.ZipFile(path) as z:
        kml = [n for n in z.namelist() if n.endswith(".kml")][0]
        t = z.read(kml).decode("utf-8", errors="replace")
    m = RE_BOX.search(t.replace("\n", ""))
    if not m:
        return None
    n, s, e, w = (float(x) for x in m.groups())
    return n, s, e, w


def main():
    cfg = L.load_volcanoes()
    filas = []
    for p in sorted(glob.glob(os.path.join(L.REPO, "kmz", "*.kmz"))):
        base = os.path.basename(p).replace("_Last_GE.kmz", "")
        vol, sen = base.split("_", 1)
        vol = ALIAS_KMZ.get(vol, vol)
        if vol not in cfg:
            continue
        b = leer_box(p)
        if b is None:
            continue
        n, s, e, w = b
        clat, clon = (n + s) / 2, (e + w) / 2
        semi_ns = (n - s) / 2 * 111.320
        semi_eo = (e - w) / 2 * 111.320 * math.cos(math.radians(clat))
        c = cfg[vol]
        filas.append(dict(
            archivo=os.path.basename(p), volcano=vol, sensor=sen,
            centro_lat=round(clat, 6), centro_lon=round(clon, 6),
            semiancho_NS_km=round(semi_ns, 2), semiancho_EO_km=round(semi_eo, 2),
            vs_half_km_25_5_NS=round(semi_ns - 25.5, 2),
            vs_half_km_25_5_EO=round(semi_eo - 25.5, 2),
            centro_vs_mirova_center_m=round(1000 * L.haversine_km(
                c["mirova_center_lat"], c["mirova_center_lon"], clat, clon), 0),
            centro_vs_vent_km=round(L.haversine_km(c["vent_lat"], c["vent_lon"], clat, clon), 2),
            centro_vs_gvp_km=round(L.haversine_km(c["lat"], c["lon"], clat, clon), 2)))
    d = pd.DataFrame(filas)
    d.to_csv(L.OUT + "/m5_kmz_grilla.csv", index=False)

    res = dict(
        n_kmz=int(len(d)),
        semiancho=dict(
            por_sensor={s: dict(n=int(len(g)),
                                NS_km_mediana=round(float(g.semiancho_NS_km.median()), 2),
                                EO_km_mediana=round(float(g.semiancho_EO_km.median()), 2),
                                NS_min=float(g.semiancho_NS_km.min()),
                                NS_max=float(g.semiancho_NS_km.max()),
                                EO_min=float(g.semiancho_EO_km.min()),
                                EO_max=float(g.semiancho_EO_km.max()))
                        for s, g in d.groupby("sensor")},
            nota="el regrid del pipeline usa half_km=25,5 en los dos ejes"),
        desvio_vs_25_5=dict(
            NS_mediana_km=round(float(d.vs_half_km_25_5_NS.median()), 2),
            EO_mediana_km=round(float(d.vs_half_km_25_5_EO.median()), 2),
            NS_rango=[float(d.vs_half_km_25_5_NS.min()), float(d.vs_half_km_25_5_NS.max())],
            EO_rango=[float(d.vs_half_km_25_5_EO.min()), float(d.vs_half_km_25_5_EO.max())]),
        centro_vs_mirova_center_m=dict(
            mediana=round(float(d.centro_vs_mirova_center_m.median()), 0),
            max=float(d.centro_vs_mirova_center_m.max()),
            n_mayor_200m=int((d.centro_vs_mirova_center_m > 200).sum())),
        por_volcan_sensor=d.set_index("archivo").to_dict("index"))
    L.dump("m5_kmz_grilla.json", res)
    print(d.to_string(index=False))
    print()
    print(pd.DataFrame(res["semiancho"]["por_sensor"]).T.to_string())


if __name__ == "__main__":
    main()
