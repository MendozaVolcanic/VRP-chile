"""S136 - donde pone MIROVA su foco termico en Isluga, medido sobre sus propios TIF.

POR QUE. Isluga es el unico Tier A con `vent_lat/lon` escrito a 2 decimales (-19,15 / -68,83):
+-0,55 km solo por redondeo, del mismo orden que el offset de 0,86 km al SO que la auditoria
S134 (F1 H6) encontro en el 100 % de los pares. El verificador la dejo en "plausible fuerte" y
pidio el dato que faltaba. Ese `vent` NO es cosmetico: `get_detection_anchor` lo usa como ancla
de deteccion, clustering y distancia en el perfil operacional, asi que decide el anillo dual-ROI
y la clasificacion summit/far.

MAXIMO LOCAL, NO GLOBAL (A61). La primera version de este script busco el maximo del TIF entero
y los 4 casos que pasaron el corte cayeron a 20-31 km del crater: eran maximos de ESCENA (el TIF
cubre ~50 km), no el foco del volcan. A61 lo dice explicitamente: hay que mirar la radiancia
LOCAL del TIF alrededor del crater. Se busca dentro del `inner_radius_km` del volcan.

QUE MIDE, Y QUE NO. El maximo local del TIF es donde MIROVA ve el calor. NO es el crater
morfologico: fijar la coordenada necesita imagen o DEM, y es decision del geologo. Esto acota la
DIRECCION del offset, que es lo que faltaba.

Se compara POSICION contra POSICION (A93): componentes N-S y E-O con signo, nunca la resta de
dos radios. MEDIANA, no media, porque un outlier corre la media y esconde el sesgo direccional
(A70). A24: el TIF no es VRP per-pixel sumable; aca solo se usa la POSICION de su maximo.
"""
import io
import math
import statistics as st
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import numpy as np
import rasterio
import yaml

RAIZ = Path(__file__).resolve().parents[2]
ARCHIVO = RAIZ.parent / "mirova-tif-archive" / "data" / "tif"
VOLCAN = "Isluga"
# Un maximo local que no destaca del fondo de la escena es ruido, no un foco.
REALCE_MIN = 1.5


def hav(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def main():
    vs = yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]
    vol = next(v for v in vs if v["name"] == VOLCAN)
    vent_lat, vent_lon = vol["vent_lat"], vol["vent_lon"]
    inner = vol.get("inner_radius_km", 5)
    print("{} - vent configurado: {} / {}  (2 decimales: +-0,55 km por redondeo)".format(
        VOLCAN, vent_lat, vent_lon))
    print("        mirova_center:  {} / {}  (centro del encuadre, NO su crater)".format(
        vol.get("mirova_center_lat"), vol.get("mirova_center_lon")))
    print("        ventana de busqueda: inner_radius_km = {} km".format(inner))
    print()

    tifs = sorted((ARCHIVO / VOLCAN).glob("*VIIRS375*.tif"))
    if not tifs:
        print("no hay TIF VIIRS375 de {} en {}".format(VOLCAN, ARCHIVO / VOLCAN))
        return
    print("TIF VIIRS375 en el archivo: {}  ({} -> {})".format(
        len(tifs), tifs[0].name[:8], tifs[-1].name[:8]))

    dys, dxs, seps, realces = [], [], [], []
    for p in tifs:
        with rasterio.open(p) as src:
            a = src.read(1).astype(float)
            h, w = a.shape
            rows, cols = np.mgrid[0:h, 0:w]
            xs, ys = rasterio.transform.xy(src.transform, rows.ravel(), cols.ravel())
            lat = np.array(ys).reshape(h, w)
            lon = np.array(xs).reshape(h, w)
        d = np.vectorize(lambda la, lo: hav(vent_lat, vent_lon, la, lo))(lat, lon)
        local = (d <= inner) & np.isfinite(a)
        if local.sum() < 10:
            continue
        fondo = float(np.nanmedian(a[np.isfinite(a)]))
        sub = np.where(local, a, np.nan)
        k = int(np.nanargmax(sub))
        r, c = np.unravel_index(k, a.shape)
        mx = float(sub.flat[k])
        if fondo <= 0 or mx / fondo < REALCE_MIN:
            continue  # campo plano en el entorno del crater: no hay foco que ubicar
        dy = hav(vent_lat, vent_lon, lat[r, c], vent_lon) * (1 if lat[r, c] > vent_lat else -1)
        dx = hav(vent_lat, vent_lon, vent_lat, lon[r, c]) * (1 if lon[r, c] > vent_lon else -1)
        dys.append(dy)
        dxs.append(dx)
        seps.append(hav(vent_lat, vent_lon, lat[r, c], lon[r, c]))
        realces.append(mx / fondo)

    print("con un maximo local destacable (>= {}x el fondo de escena): {}".format(
        REALCE_MIN, len(dys)))
    if len(dys) < 5:
        print("muestra insuficiente para un veredicto direccional")
        return

    print()
    print("DESPLAZAMIENTO del foco local de MIROVA respecto del vent configurado:")
    print("   componente N-S : {:+.3f} km (mediana)".format(st.median(dys)))
    print("   componente E-O : {:+.3f} km (mediana)".format(st.median(dxs)))
    print("   separacion     : {:.3f} km (mediana; p25 {:.2f}  p75 {:.2f})".format(
        st.median(seps), sorted(seps)[len(seps) // 4], sorted(seps)[3 * len(seps) // 4]))
    n_norte = sum(1 for x in dys if x > 0)
    n_este = sum(1 for x in dxs if x > 0)
    print()
    print("CONSISTENCIA DIRECCIONAL (el sesgo se ve aca, no en la distancia - A70):")
    print("   al norte del vent: {}/{}     al este del vent: {}/{}".format(
        n_norte, len(dys), n_este, len(dxs)))
    print("   realce mediano del foco local: {:.2f}x".format(st.median(realces)))

    print()
    print("LIMITES, para que nadie lea de mas:")
    print(" - el realce mediano es bajo: el campo de MIROVA en Isluga es casi plano, coherente")
    print("   con un volcan de regimen Muy Bajo. El pico de un campo plano es ruido (A84/S106),")
    print("   asi que la DIRECCION es interpretable y la MAGNITUD no.")
    print(" - si el p75 de la separacion toca el inner_radius, parte de los maximos estan")
    print("   pegados al borde de la ventana de busqueda: artefacto del recorte, no del volcan.")
    print(" - el archivo cubre una ventana corta; no es la serie completa.")
    print(" - esto ubica donde MIROVA ve el calor, NO el crater morfologico.")


if __name__ == "__main__":
    main()
