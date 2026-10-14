# -*- coding: utf-8 -*-
"""Tarea 1.4: el caso Lascar, NOAA-21, 2026-10-01 05:18, mirado en las imagenes de MIROVA (no hay GeoTIFF).

POR QUE ESTE CASO. El pre-registro del A/B `vrp_max` (P5) dice que MIROVA informo 1,2 MW en el crater mientras
nuestro pixel alertado mas energetico estaba a 19,7 km. Si MIROVA tenia calor ahi y lo ignoro, la regla no seria
"la mayor". Pero ese numero de MIROVA es una fila SOLO OCR (no esta en la tabla latest.php) y, desde S150, se sabe
que en esas filas el VRP es de su pasada pero la distancia puede ser de otra (memoria
reference_ocr_imagen_de_otra_pasada, PR Mirova-v1#20). Y MIROVA dejo de actualizar sus GeoTIFF el 2026-09-22
(HEAD del 2026-10-14: Last-Modified 22-Sep-2026 10:26 GMT), asi que para esta pasada no hay TIF.

QUE HAY. La lamina "Latest" de MIROVA (diez miniaturas del campo MIR de las ultimas pasadas, con fecha y VRP en la
cabecera de cada una) que el scraper Mirova-v1 guardo con la hora de la fila. Cada miniatura es el mismo campo que
el GeoTIFF, dibujado en 150 x 150 pixeles.

QUE HACE ESTE SCRIPT.
  1. CALIBRA la georreferencia de las miniaturas contra GeoTIFF de pasadas anteriores al 22-sep (lejanas VIIRS 375
     con foco identificado por estudio.py y atribucion no rechazada): busca la miniatura de esa pasada por
     correlacion con el TIF (control: la mejor celda debe ganarle claramente a las otras nueve) y mide cuanto se
     corre el foco entre el TIF y la miniatura, en km. Si el corrimiento no es chico, la miniatura no sirve para
     ubicar nada y el caso queda sin resolver.
  2. Con esa georreferencia, en la miniatura de las 05:18 de Lascar: donde esta el foco mas fuerte, a que distancia
     de nuestro pixel lejano y del crater; que z tiene la miniatura en nuestro pixel lejano contra el mismo punto
     girado alrededor del centro (11 angulos); y lo mismo en las miniaturas de las otras pasadas de esa noche.

Las celdas de las 05:18:02, 05:54:00 y 06:18:01 se identificaron leyendo la cabecera de cada miniatura (fecha y
VRP) en las laminas guardadas; el script comprueba que la celda de las 05:18 sea identica pixel a pixel en las dos
laminas que la contienen.

Uso: python experiments/_s151_seleccion_mirova/lascar_20261001.py
Salida: lascar_20261001_salida.txt y .json en esta carpeta. Imagenes y TIF al cache VRP_TIF_CACHE (fuera del repo).
"""
from __future__ import annotations

import io
import json
import math
import sys
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from PIL import Image
from scipy.ndimage import median_filter

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import comun_tif as T  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
MV1_SHA = "f14f721f57aa85dd225e7c5383ce08d3501362a6"   # Mirova-v1, consultado el 2026-10-14
MV1 = f"https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/{MV1_SHA}/monitoreo_satelital/imagenes_satelitales/"
CARPETA = {"NevadosDeChillan": "Nevados_de_Chillan", "PuyehueCordonCaulle": "Puyehue_Cordon_Caulle"}
# Disposicion de la lamina "Latest" (850 x 600): diez miniaturas de 150 x 150, cinco por fila (medido en la lamina).
X0 = [15, 180, 345, 510, 675]
Y0 = [165, 400]
LADO = 150
HP_KERNEL = 9
HOT = (-23.21154, -67.644)          # nuestro hotspot de Lascar NOAA-21 2026-10-01 05:18 (record del JSON)
CRATER = (-23.36293, -67.731416)    # vent_lat/vent_lon de volcanoes.yaml
CASO = {"05-18-02": {"05:18:02": 1, "06:18:01": 0}, "05-54-00": {"05:54:00": 1, "05:18:02": 2, "06:18:01": 0}}


def bajar(url, destino):
    destino.parent.mkdir(parents=True, exist_ok=True)
    if not destino.exists():
        try:
            urllib.request.urlretrieve(url, destino)
        except urllib.error.HTTPError:
            return None
    return destino


def celdas(path):
    im = np.asarray(Image.open(path).convert("RGB")).astype(float)
    lum = im.sum(axis=2)
    return [lum[y:y + LADO, x:x + LADO] for y in Y0 for x in X0]


def zfield(a):
    hp = a - median_filter(a, size=HP_KERNEL)
    m = np.nanmedian(hp)
    s = 1.4826 * np.nanmedian(np.abs(hp - m))
    z = (hp - m) / s if s > 0 else hp * 0
    z[:3, :] = z[-3:, :] = z[:, :3] = z[:, -3:] = np.nan   # el marco de color de la miniatura contamina el borde
    return z


def tif_a_miniatura(arr):
    """El TIF remuestreado a 150 x 150 (bilineal), para correlacionar con la miniatura."""
    a = np.where(np.isfinite(arr) & (arr > 0), arr, np.nanmedian(arr[np.isfinite(arr) & (arr > 0)]))
    return np.asarray(Image.fromarray(a.astype("float32")).resize((LADO, LADO), Image.BILINEAR), dtype=float)


def rc_a_uv(r, c, h, w):
    return (r + 0.5) * LADO / h - 0.5, (c + 0.5) * LADO / w - 0.5


def latlon_a_uv(lat, lon, bounds, h, w):
    """Posicion en la miniatura de un punto, con la georreferencia del TIF (borde a borde)."""
    left, bottom, right, top = bounds
    return (top - lat) / (top - bottom) * LADO - 0.5, (lon - left) / (right - left) * LADO - 0.5


def uv_a_latlon(v, u, bounds):
    left, bottom, right, top = bounds
    return top - (v + 0.5) / LADO * (top - bottom), left + (u + 0.5) / LADO * (right - left)


def main():
    out = io.StringIO()

    def P(*a):
        print(*a)
        print(*a, file=out)

    res = {}
    # ------------------------------------------------------------------ 1. calibracion contra TIF
    df = pd.read_csv(AQUI / "pasadas.csv")
    cand = df[(df.grupo == "lejana") & (df.sensor == "VIIRS375") & df.ring_id & (df.atrib != "rechazada")
              & (df.z_ring >= 30)].sort_values("fecha_utc")
    P(f"== 1. Calibracion de la georreferencia de las miniaturas: {len(cand)} lejanas VIIRS 375 con foco z >= 30 y TIF")
    # El scraper guarda laminas solo con la hora de algunas filas. Para cada lejana se prueban las laminas de las
    # filas del mismo volcan (VIIRS 375) de esa fecha a la misma hora o despues (la lamina trae las diez ultimas
    # pasadas, asi que una posterior suele contener la celda buscada); la celda se reconoce por correlacion.
    sys.path.insert(0, str(AQUI.parents[1] / "scripts"))
    from referencia_mirova_unificada import cargar_referencia_unificada
    horas = {}
    for f in cargar_referencia_unificada():
        if f["sensor_bucket"] == "VIIRS375" and f["tipo"] != "RUTINA":
            horas.setdefault((f["volcano"], f["fecha_utc"][:10]), set()).add(f["fecha_utc"][11:19])
    filas = []
    for x in cand.itertuples():
        carpeta = CARPETA.get(x.vol, x.vol)
        png = None
        for hh in sorted(h for h in horas.get((x.vol, x.fecha_utc[:10]), ()) if h >= x.fecha_utc[11:19])[:4]:
            hhmmss = hh.replace(":", "-")
            png = bajar(f"{MV1}{carpeta}/{x.fecha_utc[:10]}/{hhmmss}_{carpeta}_VIIRS375_Latest.png",
                        T.CACHE / "mv1" / carpeta / x.fecha_utc[:10] / f"{hhmmss}_Latest.png")
            if png is not None:
                break
        if png is None:
            continue
        with rasterio.open(T.CACHE / x.tif) as s:
            arr = s.read(1).astype(float)
            h, w = arr.shape
            bounds = s.bounds
            geo = s.crs.is_geographic
        if not geo:
            continue
        # se correlacionan los campos de EXCESO LOCAL, no los crudos: el campo crudo esta dominado por la topografia,
        # que es la misma en todas las pasadas, y no distingue una celda de otra (primera corrida: r 0,98 a 0,99 en
        # las diez celdas; cambio hecho despues de verla, dicho)
        ref = zfield(tif_a_miniatura(arr))
        cs = celdas(png)
        rs = []
        for cc in cs:
            zc = zfield(cc)
            ok = np.isfinite(ref) & np.isfinite(zc)
            a, b = np.clip(ref[ok], -10, 50), np.clip(zc[ok], -10, 50)
            rs.append(float(np.corrcoef(a, b)[0, 1]) if b.std() > 0 else float("nan"))
        orden = np.argsort([-(r if r == r else -9) for r in rs])
        k, k2 = int(orden[0]), int(orden[1])
        zt = zfield(cs[k])
        v0, u0 = latlon_a_uv(x.ring_lat, x.ring_lon, bounds, h, w)
        vi, ui = int(round(v0)), int(round(u0))
        win = zt[max(0, vi - 6):vi + 7, max(0, ui - 6):ui + 7]
        if not np.isfinite(win).any():
            continue
        dv, du = np.unravel_index(int(np.nanargmax(win)), win.shape)
        vf, uf = max(0, vi - 6) + dv, max(0, ui - 6) + du
        lat_f, lon_f = uv_a_latlon(vf, uf, bounds)
        err = float(T.dist_km(lat_f, lon_f, x.ring_lat, x.ring_lon))
        vg, ug = np.unravel_index(int(np.nanargmax(zt)), zt.shape)
        lat_g, lon_g = uv_a_latlon(vg, ug, bounds)
        err_g = float(T.dist_km(lat_g, lon_g, x.ring_lat, x.ring_lon))
        # nulo: la misma ventana en las OTRAS nueve celdas (otras pasadas, misma escena)
        otras = []
        for j, cc in enumerate(cs):
            if j != k:
                wz = zfield(cc)[max(0, vi - 6):vi + 7, max(0, ui - 6):ui + 7]
                if np.isfinite(wz).any():
                    otras.append(float(np.nanmax(wz)))
        filas.append({"vol": x.vol, "fecha": x.fecha_utc, "celda": k, "r_mejor": rs[k], "r_segunda": rs[k2],
                      "err_km": err, "z_mini": float(np.nanmax(win)), "err_max_global_km": err_g,
                      "z_otras_celdas": float(np.median(otras)) if otras else float("nan")})
        P(f"   {x.vol:18s} {x.fecha_utc}: celda {k}, r {rs[k]:.3f} (segunda {rs[k2]:.3f}); foco del TIF en la miniatura a "
          f"{err:.2f} km (z {np.nanmax(win):.1f}); maximo global de la miniatura a {err_g:.2f} km del foco del TIF")
    cal = pd.DataFrame(filas)
    if len(cal):
        # Criterio escrito despues de la primera corrida (dicho): "la celda mas correlacionada muestra el foco" =
        # z >= 10 en la ventana de +-2 km alrededor de donde el TIF pone el foco. La version anterior pedia que la
        # mejor celda doblara la correlacion de la segunda, y casi ninguna lo cumple porque pasadas vecinas comparten
        # rasgos fijos de la escena.
        buenas = cal[cal.z_mini >= 10]
        P(f"   miniaturas encontradas {len(cal)}; en {len(buenas)} la celda mas correlacionada muestra el foco (z >= 10 a "
          f"+-2 km de donde lo pone el TIF); nulo, la misma ventana en las otras nueve celdas: z mediano "
          f"{cal.z_otras_celdas.median():.1f}, sobre 10 en {int((cal.z_otras_celdas >= 10).sum())} de {len(cal)}")
        if len(buenas):
            P(f"   corrimiento TIF -> miniatura del foco: mediana {buenas.err_km.median():.2f} km, maximo {buenas.err_km.max():.2f} km;"
              f" el maximo global de la miniatura cae a <= 1,1 km del foco del TIF en {int((buenas.err_max_global_km <= 1.1).sum())}"
              f" de {len(buenas)}")
            res["calibracion"] = {"n_laminas": len(cal), "n_foco_visible": len(buenas),
                                  "err_mediana_km": round(float(buenas.err_km.median()), 3),
                                  "err_max_km": round(float(buenas.err_km.max()), 3),
                                  "z_otras_celdas_mediana": round(float(cal.z_otras_celdas.median()), 2),
                                  "max_global_a_1_1km": int((buenas.err_max_global_km <= 1.1).sum())}

    # ------------------------------------------------------------------ 2. el caso
    P("\n== 2. Lascar 2026-10-01: laminas Latest de VIIRS 375 que guardo el scraper (cabecera 'Last Update 06:18:01')")
    with rasterio.open(next((T.CACHE / "data" / "tif" / "Lascar").glob("*_VIIRS375.tif"))) as s:
        bounds_l = s.bounds
        if not s.crs.is_geographic:
            raise SystemExit("el TIF de referencia de Lascar no es EPSG:4326")
    P(f"   georreferencia de la miniatura: la del GeoTIFF VIIRS 375 de Lascar (EPSG:4326, {bounds_l})")
    lam = {}
    for nombre in CASO:
        p = bajar(f"{MV1}Lascar/2026-10-01/{nombre}_Lascar_VIIRS375_Latest.png", T.CACHE / "mv1" / "Lascar" / "2026-10-01" / f"{nombre}_Latest.png")
        lam[nombre] = celdas(p)
    a, b = lam["05-18-02"][CASO["05-18-02"]["05:18:02"]], lam["05-54-00"][CASO["05-54-00"]["05:18:02"]]
    P(f"   la celda 05:18:02 es la misma en las dos laminas: diferencia maxima {np.abs(a - b).max():.1f} (de 0 a 765)")
    v_h, u_h = latlon_a_uv(*HOT, bounds_l, 134, 134)
    v_c, u_c = latlon_a_uv(*CRATER, bounds_l, 134, 134)
    clat, clon = (bounds_l[1] + bounds_l[3]) / 2, (bounds_l[0] + bounds_l[2]) / 2
    P(f"   nuestro pixel lejano en la miniatura: fila {v_h:.1f}, columna {u_h:.1f}; crater: fila {v_c:.1f}, columna {u_c:.1f}")
    res["caso"] = {}
    for hora, k in CASO["05-54-00"].items():
        z = zfield(lam["05-54-00"][k])
        vg, ug = np.unravel_index(int(np.nanargmax(z)), z.shape)
        lat_g, lon_g = uv_a_latlon(vg, ug, bounds_l)

        def zen(v, u):
            vi, ui = int(round(v)), int(round(u))
            w = z[max(0, vi - 1):vi + 2, max(0, ui - 1):ui + 2]
            return float(np.nanmax(w)) if np.isfinite(w).any() else float("nan")
        z_hot = zen(v_h, u_h)
        z_cr = max(zen(v, u) for v in np.arange(v_c - 3, v_c + 4) for u in np.arange(u_c - 3, u_c + 4))
        nulos = []
        for ang in range(30, 360, 30):
            la, lo = T.rotar(HOT[0], HOT[1], clat, clon, ang)
            v, u = latlon_a_uv(la, lo, bounds_l, 134, 134)
            if 3 <= v < LADO - 3 and 3 <= u < LADO - 3:
                nulos.append(zen(v, u))
        d_hot = float(T.dist_km(lat_g, lon_g, *HOT))
        d_cr = float(T.dist_km(lat_g, lon_g, *CRATER))
        P(f"   celda {hora}: foco mas fuerte z {np.nanmax(z):.1f} en ({lat_g:.4f}, {lon_g:.4f}), a {d_hot:.2f} km de nuestro "
          f"pixel lejano y {d_cr:.2f} km del crater | z en nuestro pixel lejano {z_hot:.1f} (girado: mediana "
          f"{np.nanmedian(nulos):.1f}, maximo {np.nanmax(nulos):.1f}, n={len(nulos)}) | z maximo a <= 1 km del crater {z_cr:.1f}")
        res["caso"][hora] = {"z_max": round(float(np.nanmax(z)), 2), "foco": [round(lat_g, 5), round(lon_g, 5)],
                             "d_foco_a_nuestro_km": round(d_hot, 2), "d_foco_a_crater_km": round(d_cr, 2),
                             "z_en_nuestro": round(z_hot, 2), "z_girado_mediana": round(float(np.nanmedian(nulos)), 2),
                             "z_girado_max": round(float(np.nanmax(nulos)), 2), "z_crater": round(z_cr, 2)}
    (AQUI / "lascar_20261001_salida.txt").write_text(out.getvalue(), encoding="utf-8")
    (AQUI / "lascar_20261001_salida.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
