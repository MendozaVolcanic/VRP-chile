# -*- coding: utf-8 -*-
"""S196: fondos del visor de radios del edificio (imagen satelital y relieve sombreado con curvas de nivel).

POR QUÉ el fondo va en archivos y no en teselas en vivo: el visor se publica como Artifact, y la política de seguridad
de los Artifact bloquea en silencio toda imagen de otro servidor. Además Nicolás abre el HTML desde su disco. Por eso
cada volcán lleva dos imágenes fijas, recortadas alrededor del cráter, que el visor pone debajo del mapa.

POR QUÉ relieve además de satélite: el límite de un edificio volcánico se lee en el quiebre de pendiente entre el cono
y el terreno que lo rodea; la imagen satelital lo esconde con nieve, nubes y sombras, el relieve sombreado con curvas
de nivel lo muestra directo.

Fuentes (las mismas familias que ya usa el repo):
  - Satélite: ESRI World Imagery (teselas públicas; el tablero frontend/index.html y experiments/_s124_ndc_focus/basemap.py
    la usan). Atribución: «Imagen: Esri, Maxar, Earthstar Geographics».
  - Relieve: Terrain Tiles de AWS Open Data (formato terrarium; SRTM y otros modelos, dominio público o abiertos),
    sombreado aquí (Sol al NO a 45°) con curvas cada 100 m y maestras cada 500 m.

Proyección: las dos fuentes son Web Mercator; el mosaico conserva esa proyección y el visor (Leaflet, EPSG:3857) lo
coloca con las coordenadas exactas de sus esquinas, así que no hay error de reproyección.

Uso: python experiments/_s196_visor_radios/fondos.py [--cache DIR] [--solo Volcan,...]
Salida: experiments/_s196_visor_radios/fondos/<Volcan>_sat.jpg, <Volcan>_relieve.jpg y fondos.json (esquinas).
"""
from __future__ import annotations

import argparse
import io
import json
import math
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
import yaml
from PIL import Image

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ))
from pipeline.geo_utils import get_detection_anchor  # noqa: E402

URL_SAT = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
URL_DEM = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
UA = {"User-Agent": "VRP-Chile/visor-radios"}
TILE = 256
# Tier A (11, grilla de 51 x 51 km): caja de ±30 km a zoom 12, así cabe un edificio de hasta ~28 km de radio.
# Los demás (radio de 5 km en el NRT): ±20 km a zoom 11; un edificio chileno rara vez pasa de 15 km de radio.
CAJA = {True: (30.0, 12, 1400), False: (20.0, 11, 900)}   # (semilado km, zoom, lado máximo de la imagen en px)


def deg2tile(lat, lon, z):
    n = 2.0 ** z
    return (lon + 180.0) / 360.0 * n, (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n


def tile2deg(x, y, z):
    n = 2.0 ** z
    return math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n)))), x / n * 360.0 - 180.0


def bajar(url, f: Path, reintentos=4):
    if f.exists() and f.stat().st_size > 0:
        return f.read_bytes()
    f.parent.mkdir(parents=True, exist_ok=True)
    for i in range(reintentos):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                raw = r.read()
            f.write_bytes(raw)
            time.sleep(0.05)
            return raw
        except Exception as e:  # noqa: BLE001  (red: reintento con espera creciente)
            if i == reintentos - 1:
                raise RuntimeError(f"no bajó {url}: {e}") from e
            time.sleep(2 * (i + 1))


def mosaico(lat0, lon0, semi_km, z, cache: Path, fuente: str):
    """Mosaico de teselas que cubre ±semi_km alrededor de (lat0, lon0). Devuelve (array, (sur, oeste, norte, este))."""
    dlat = semi_km / 110.574
    dlon = semi_km / (111.320 * math.cos(math.radians(lat0)))
    x0, y0 = deg2tile(lat0 + dlat, lon0 - dlon, z)
    x1, y1 = deg2tile(lat0 - dlat, lon0 + dlon, z)
    tx0, ty0, tx1, ty1 = int(x0), int(y0), int(x1), int(y1)
    filas = []
    for ty in range(ty0, ty1 + 1):
        fila = []
        for tx in range(tx0, tx1 + 1):
            if fuente == "sat":
                raw = bajar(URL_SAT.format(z=z, x=tx, y=ty), cache / "sat" / f"{z}_{tx}_{ty}.jpg")
                fila.append(np.asarray(Image.open(io.BytesIO(raw)).convert("RGB")))
            else:
                raw = bajar(URL_DEM.format(z=z, x=tx, y=ty), cache / "dem" / f"{z}_{tx}_{ty}.png")
                a = np.asarray(Image.open(io.BytesIO(raw)).convert("RGB")).astype(np.float64)
                fila.append(a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768)
        filas.append(np.concatenate(fila, axis=1))
    m = np.concatenate(filas, axis=0)
    # Recorte exacto a la caja pedida (en píxeles del mosaico).
    c0, r0 = int((x0 - tx0) * TILE), int((y0 - ty0) * TILE)
    c1, r1 = int(math.ceil((x1 - tx0) * TILE)), int(math.ceil((y1 - ty0) * TILE))
    m = m[r0:r1, c0:c1]
    norte, oeste = tile2deg(tx0 + c0 / TILE, ty0 + r0 / TILE, z)
    sur, este = tile2deg(tx0 + c1 / TILE, ty0 + r1 / TILE, z)
    return m, (sur, oeste, norte, este)


def relieve(dem, lat0, z, lado_max):
    """Sombreado (azimut 315°, altura 45°) con curvas de nivel cada 100 m (maestras cada 500 m), como imagen RGB."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    # Tamaño del píxel en metros: Web Mercator a esta latitud y zoom.
    px_m = 156543.03392 * math.cos(math.radians(lat0)) / 2 ** z
    from matplotlib.colors import LightSource, LinearSegmentedColormap
    # Las teselas traen picos falsos muy negativos (Villarrica: -3.743 m junto al lago); se recorta al percentil 0,5
    # para que no estiren la escala de color ni dibujen curvas espurias.
    dem = np.maximum(dem, np.nanpercentile(dem, 0.5))
    # Tinte hipsométrico apagado (verde grisáceo abajo, ocre, pardo, blanco en las cumbres) mezclado con el sombreado:
    # el color da la altura y la sombra da la forma; así se ve dónde el cono se separa del terreno que lo rodea.
    tinte = LinearSegmentedColormap.from_list("hipso", ["#8fa58a", "#c9c08f", "#b08a5e", "#8a6a55", "#f2efe9"])
    ls = LightSource(azdeg=315, altdeg=45)
    rgb = ls.shade(dem, cmap=tinte, blend_mode="soft", vert_exag=1.5, dx=px_m, dy=px_m,
                   vmin=float(np.nanmin(dem)), vmax=float(np.nanmax(dem)))
    h, w = dem.shape
    esc = min(1.0, lado_max / max(h, w))
    W, H = max(1, round(w * esc)), max(1, round(h * esc))
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(rgb, extent=(0, w, h, 0), interpolation="bilinear")
    lo, hi = math.floor(np.nanmin(dem) / 100) * 100, math.ceil(np.nanmax(dem) / 100) * 100
    niveles = np.arange(lo, hi + 100, 100)
    finas = [v for v in niveles if v % 500]
    maestras = [v for v in niveles if not v % 500]
    yy, xx = np.mgrid[0:h, 0:w]
    if finas:
        ax.contour(xx, yy, dem, levels=finas, colors="#6b3a14", linewidths=0.35, alpha=0.55)
    if maestras:
        cs = ax.contour(xx, yy, dem, levels=maestras, colors="#5a2a08", linewidths=0.9, alpha=0.85)
        ax.clabel(cs, fmt="%d", fontsize=6, inline=True)
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)
    ax.axis("off")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="D:/vrp-trabajo/temporales/s196_visor/teselas")
    ap.add_argument("--solo", default="")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    cache = Path(args.cache)
    salida = AQUI / "fondos"
    salida.mkdir(exist_ok=True)
    meta_f = AQUI / "fondos.json"
    meta = json.loads(meta_f.read_text(encoding="utf-8")) if meta_f.exists() else {}
    solo = {s for s in args.solo.split(",") if s}
    vols = [v for v in yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]
            if v.get("active")]
    for v in vols:
        nombre = v["name"]
        if solo and nombre not in solo:
            continue
        tier_a = v.get("radius_km") == 25
        semi, z, lado = CAJA[tier_a]
        lat0, lon0 = get_detection_anchor(v)
        sat, caja = mosaico(lat0, lon0, semi, z, cache, "sat")
        img = Image.fromarray(sat)
        esc = min(1.0, lado / max(img.size))
        img = img.resize((round(img.size[0] * esc), round(img.size[1] * esc)), Image.LANCZOS)
        img.save(salida / f"{nombre}_sat.jpg", quality=72, optimize=True, progressive=True)
        dem, caja_d = mosaico(lat0, lon0, semi, z, cache, "dem")
        assert all(abs(a - b) < 1e-9 for a, b in zip(caja, caja_d)), "las dos fuentes deben cubrir la misma caja"
        rel = relieve(dem, lat0, z, lado)
        rel = rel.resize(img.size, Image.LANCZOS)
        rel.save(salida / f"{nombre}_relieve.jpg", quality=72, optimize=True, progressive=True)
        meta[nombre] = {"sur": caja[0], "oeste": caja[1], "norte": caja[2], "este": caja[3], "zoom": z,
                        "semilado_km": semi, "px": list(img.size),
                        "cota_min_m": round(float(np.nanpercentile(dem, 0.5))), "cota_max_m": round(float(np.nanmax(dem)))}
        print(f"{nombre}\tz{z}\t{img.size}\tcotas {meta[nombre]['cota_min_m']} a {meta[nombre]['cota_max_m']} m",
              flush=True)
    meta_f.write_text(json.dumps(meta, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
