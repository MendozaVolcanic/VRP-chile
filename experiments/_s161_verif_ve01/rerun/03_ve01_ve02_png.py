# -*- coding: utf-8 -*-
"""S161, VE-01 y VE-02 (sospechas del verificador S160) en las imágenes de MIROVA.

Por qué así: no hay GeoTIFF de MIROVA después del 2026-09-22 (el archivo los congela, memoria S151), pero el poller
de mirova-tif-archive guarda cada pocas horas el panel «Latest Images» (Latest10NTI): diez miniaturas del NTI de las
últimas pasadas, con hora, VRP y marco verde si hubo alerta. La miniatura es la misma escena que el TIF (134 x 134
celdas VIIRS 375 en EPSG:4326). Aquí se georreferencia la miniatura y se ubica el punto caliente.

Instrumento:
1. Georreferencia: se supone que el interior de la miniatura (150 x 150 px, dentro del marco de 2 px) cubre los
   bounds del TIF. Se COMPRUEBA correlacionando la miniatura (pasa-alto) con TIF nocturnos despejados del mismo volcán
   reescalados, buscando el desplazamiento de +-6 px que maximiza r. Nulo: la misma miniatura contra TIF de otro volcán
   (Isluga). Si el supuesto fuera falso, el r del mismo volcán no superaría al nulo o el mejor desplazamiento no sería
   ~0.
2. Punto caliente: pasa-alto (miniatura menos su mediana 5 x 5) en unidades de desviación robusta (MAD) de la
   miniatura; máximos locales con z >= 6. Se dan en lat/lon, distancia y rumbo al cráter y a nuestro píxel.
Las dos preguntas del instrumento: P1 (roto): el nulo de otro volcán debe dar r cercano a 0 y el mismo volcán claramente
más; P2 (muerto): se imprime n de máximos por miniatura; una miniatura sin máximos es SIN DATO, no «nada».

Las PNG se bajan una por una de raw.githubusercontent (sin pull ni clone del repo de 17 GB) a la carpeta temporal.
Uso: python -I 03_ve01_ve02_png.py > 03_ve01_ve02_png_salida.txt
"""
from __future__ import annotations

import glob
import subprocess
import sys
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image
from scipy.ndimage import gaussian_filter, maximum_filter, median_filter, zoom

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comun161 as C  # noqa: E402

C.utf8_stdout()
PNG_DIR = C.SCRATCH / "png_mirova"
RAW = "https://raw.githubusercontent.com/MendozaVolcanic/mirova-tif-archive/main/data/png/"
OUT = Path(__file__).resolve().parent

# Miniaturas: (fila, columna) del panel; la hora de cada una la leí en la imagen (rótulo sobre la miniatura).
CASOS = [
    dict(id="VE-01", vol="Tupungatito", png="Tupungatito/20260929_122836_VIIRS375_Latest10NTI.png", fila=0, col=3,
         rotulo="29-Sep-2026 04:54:00, VRP = 1.86 MW (rojo, marco verde)", nuestro=(-33.36927, -69.72791),
         nuestro_txt="record 2026-09-29 04:54 VIIRS_SNPP, 1 píxel, 1,112 MW, 302 K, far"),
    dict(id="VE-01 control misma noche", vol="Tupungatito", png="Tupungatito/20260929_122836_VIIRS375_Latest10NTI.png",
         fila=0, col=2, rotulo="29-Sep-2026 05:18:01, VRP = 0.04 MW", nuestro=None, nuestro_txt=""),
    dict(id="VE-02 (V750)", vol="PuyehueCordonCaulle", png="PuyehueCordonCaulle/20261021_083721_VIIRS750_Latest10NTI.png",
         fila=0, col=0, rotulo="21-Oct-2026 05:48:02, VRP = 0 MW; banner «Thermal anomaly: VERY LOW»",
         nuestro=None, nuestro_txt="record 2026-10-21 05:48 VIIRS_NOAA21_750, cúmulo 3 px, 1,418 MW a 10,1 km del cráter"),
    dict(id="VE-02 (V375)", vol="PuyehueCordonCaulle", png="PuyehueCordonCaulle/20261021_102055_VIIRS375_Latest10NTI.png",
         fila=0, col=1, rotulo="21-Oct-2026 05:48:02, VRP = NaN MW", nuestro=None, nuestro_txt=""),
]
FILA_Y0 = {0: 165}   # fila superior del panel (medido en los píxeles del marco)
COL_X0 = 15
PASO_X = 165
LADO = 150


def bajar(rel):
    dst = PNG_DIR / Path(rel).name
    if not dst.exists():
        PNG_DIR.mkdir(parents=True, exist_ok=True)
        subprocess.run(["curl", "-sSf", "-o", str(dst), RAW + rel], check=True)
    return dst


def miniatura(path, fila, col):
    im = np.array(Image.open(path).convert("RGB")).astype(float)
    y0, x0 = FILA_Y0[fila], COL_X0 + PASO_X * col
    return im[y0:y0 + LADO, x0:x0 + LADO].mean(axis=2), im[y0 - 2:y0 + LADO + 1, x0 - 2:x0 + LADO + 1]


def tifs_noche(vol, n=40):
    pats = [C.REPO / f"experiments/_s144_conteo_tif/_dl_tif/*/data/tif/{vol}/2026*VIIRS375.tif",
            C.REPO / f"experiments/_s147_tif/tif/{vol}/2026*VIIRS375.tif"]
    fs = sorted({f for p in pats for f in glob.glob(str(p))})
    out = []
    for f in fs:
        h = int(Path(f).name[9:11])
        if not (3 <= h <= 8):          # pasadas nocturnas VIIRS en Chile
            continue
        with rasterio.open(f) as d:
            if d.crs is None or d.crs.to_epsg() != 4326:
                continue
            A = d.read(1).astype(float)
            b = d.bounds
        A[~np.isfinite(A) | (A <= 0)] = np.nan
        if np.isnan(A).mean() > 0.05:
            continue
        out.append((f, np.where(np.isnan(A), np.nanmedian(A), A), b))
    return out[-n:]


def hp(a, s=6):
    return a - gaussian_filter(a, s)


def correl(I, A):
    Z = zoom(A, (I.shape[0] / A.shape[0], I.shape[1] / A.shape[1]), order=1)
    a, b = hp(Z), hp(I)
    best = (-2, 0, 0)
    r00 = None
    for dy in range(-6, 7):
        for dx in range(-6, 7):
            aa = np.roll(np.roll(a, dy, 0), dx, 1)[8:-8, 8:-8]
            r = float(np.corrcoef(aa.ravel(), b[8:-8, 8:-8].ravel())[0, 1])
            if dy == 0 and dx == 0:
                r00 = r
            if r > best[0]:
                best = (r, dy, dx)
    return best, r00


def main():
    print("S161 03: VE-01 y VE-02 en los paneles Latest10NTI de MIROVA (mirova-tif-archive/data/png)")
    nulo_tifs = tifs_noche("Isluga", n=10)
    for caso in CASOS:
        path = bajar(caso["png"])
        I, crop = miniatura(path, caso["fila"], caso["col"])
        vol = caso["vol"]
        vent = C.GEO[vol]["vent"]
        print(f"\n=== {caso['id']}: {vol}, panel {caso['png']}, miniatura fila {caso['fila']} col {caso['col']}")
        print(f"    rótulo leído en la imagen: {caso['rotulo']}")
        # 1. georreferencia
        mismos = tifs_noche(vol)
        res = sorted(((correl(I, A), Path(f).name, b) for f, A, b in mismos), key=lambda x: -x[0][0][0])
        nul = [correl(I, A)[0][0] for _, A, _ in nulo_tifs]
        (r, dy, dx), r00 = res[0][0]
        b = res[0][2]
        print(f"    georreferencia: {len(mismos)} TIF nocturnos despejados del mismo volcán; mejor {res[0][1]} r = {r:.3f} "
              f"con desplazamiento (dy, dx) = ({dy}, {dx}) px de miniatura (r sin desplazar {r00:.3f}); mediana r de los "
              f"5 mejores {np.median([x[0][0][0] for x in res[:5]]):.3f}")
        print(f"    nulo (otro volcán, Isluga, {len(nul)} TIF): r máximo {max(nul):.3f}, mediana {np.median(nul):.3f}")
        georef_ok = r > max(nul) + 0.15 and abs(dy) <= 2 and abs(dx) <= 2
        print(f"    georreferencia {'VALIDA' if georef_ok else 'NO VALIDADA (escena nublada o desplazamiento grande)'}: "
              f"se usa la identidad (interior = bounds del TIF) {'corregida por el desplazamiento' if georef_ok else 'sin corregir'}")
        sy, sx = (dy, dx) if georef_ok else (0, 0)
        # 2. punto caliente
        h = I - median_filter(I, size=5, mode="nearest")
        mad = np.median(np.abs(h - np.median(h))) * 1.4826
        z = h / mad
        z[:3, :] = z[-3:, :] = 0
        z[:, :3] = z[:, -3:] = 0
        pk = (z == maximum_filter(z, size=7)) & (z >= 6)
        ys, xs = np.where(pk)
        orden = np.argsort(-z[ys, xs])
        print(f"    máximos locales z >= 6: {len(ys)}")
        for k in orden[:6]:
            yy, xx = ys[k], xs[k]
            # roll(a, dy) alinea el TIF con la miniatura: rasgo de miniatura en fila y = TIF en fila y - dy
            fy = (yy - sy + 0.5) / LADO
            fx = (xx - sx + 0.5) / LADO
            lat = b.top - fy * (b.top - b.bottom)
            lon = b.left + fx * (b.right - b.left)
            dv = C.dist_km(*vent, lat, lon)
            rv = C.octante(C.rumbo(*vent, lat, lon))
            dc = C.dist_km(*C.GEO[vol]["tif_centro"], lat, lon)
            linea = (f"      z {z[yy, xx]:5.1f} en px ({yy},{xx}) -> {lat:.5f} / {lon:.5f}: {dv:5.2f} km {rv} del cráter, "
                     f"{dc:5.2f} km del centro del TIF")
            if caso["nuestro"]:
                linea += f"; a {C.dist_km(*caso['nuestro'], lat, lon):.2f} km de nuestro píxel"
            print(linea)
        if caso["nuestro"]:
            n = caso["nuestro"]
            print(f"    nuestro: {caso['nuestro_txt']} en {n[0]} / {n[1]}: {C.dist_km(*vent, *n):.2f} km "
                  f"{C.octante(C.rumbo(*vent, *n))} del cráter, {C.dist_km(*C.GEO[vol]['tif_centro'], *n):.2f} km del centro del TIF")
        elif caso["nuestro_txt"]:
            print(f"    nuestro: {caso['nuestro_txt']}")
            import json
            hora = caso["rotulo"][:17]
            for r in json.load(open(C.DATA / f"{vol}.json", encoding="utf-8"))["records"]:
                if r["datetime_utc"] == "2026-10-21 05:48":
                    ap = r.get("anomaly_pixels") or []
                    bts = sorted(x["bt_k"] for x in ap)
                    print(f"      {r['sensor']}: t_bg {r.get('t_bg_k')} K, {len(ap)} píxeles anómalos con BT {bts[0] if bts else None} a "
                          f"{bts[-1] if bts else None} K, a {min((C.dist_km(*vent, x['lat'], x['lon']) for x in ap), default=float('nan')):.1f} a "
                          f"{max((C.dist_km(*vent, x['lat'], x['lon']) for x in ap), default=float('nan')):.1f} km del cráter; cúmulo {r.get('primary_cluster')}")
        Image.fromarray(np.clip(crop, 0, 255).astype("uint8")).resize((crop.shape[1] * 3, crop.shape[0] * 3), Image.NEAREST).save(
            OUT / f"03_miniatura_{caso['id'].split()[0].replace('-', '')}_{caso['png'].split('/')[1][:15]}_c{caso['col']}.png")


def ve01_extra():
    """Celda de la grilla de MIROVA donde cae la fuente de VE-01 y otras pasadas nuestras con un píxel a <= 1 km."""
    import json
    from pyproj import Transformer
    vol, pt = "Tupungatito", (-33.36927, -69.72791)
    g = C.GEO[vol]["grilla"]
    T = Transformer.from_crs("EPSG:4326", f"EPSG:{g['epsg']}", always_xy=True)
    for nombre, (la, lo) in (("fuente VE-01", pt), ("cráter", C.GEO[vol]["vent"])):
        x, y = T.transform(lo, la)
        f, c = int((g["ul_y"] - y) // C.CELDA_M), int((x - g["ul_x"]) // C.CELDA_M)
        zona = "caja de cumbre" if (30 <= f <= 36 and 30 <= c <= 36) else ("anillo" if (22 <= f <= 42 and 24 <= c <= 42) else "fuera del anillo")
        print(f"    {nombre}: celda de la grilla de MIROVA fila {f}, col {c} -> {zona}")
    print("    otras pasadas nuestras (todo el corpus) con un píxel anómalo a <= 1 km de la fuente:")
    for r in json.load(open(C.DATA / f"{vol}.json", encoding="utf-8"))["records"]:
        for x in r.get("anomaly_pixels") or []:
            if x.get("lat") is not None and C.dist_km(*pt, x["lat"], x["lon"]) <= 1.0:
                print(f"      {r['datetime_utc']} {r['sensor']}: píxel {x['lat']} / {x['lon']}, BT {x.get('bt_k')} K, "
                      f"{x.get('vrp_mw')} MW, clase {r.get('distance_class')}")
                break


if __name__ == "__main__":
    main()
    print()
    print("=== VE-01, posición en la grilla de MIROVA y recurrencia en nuestros records")
    ve01_extra()
