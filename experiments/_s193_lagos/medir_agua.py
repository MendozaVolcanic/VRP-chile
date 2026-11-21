"""S193: cuantas detecciones de la via «codigo MIROVA» caen sobre agua.

POR QUE: Nicolas pregunta si los falsos positivos sobre lagos (Laguna del Maule) son una falla del codigo de
MIROVA o algo corregible. Antes de proponer nada hay que contar, con una mascara de agua publica e independiente
(JRC Global Surface Water v1.4, ocurrencia 1984-2021, 30 m; Pekel et al. 2016), cuantas detecciones caen sobre
agua, en que sensor, de dia o de noche, con que VRP y a que distancia del crater.

Fuentes (solo records con via_codigo_mirova=True, el metodo de produccion):
  data/historia_34/<V>.json   historia retro de la via de los 34 (2025-02-15 a 2026-11-02)
  data/sombra_34/<V>.json     sombra diaria de los 34 (desde 2026-11-03)
  data/mirova_equivalent/<V>.json  los 11 Tier A (NRT); para los 34 este archivo es pre-via y se descarta solo
Se deduplica por (sensor, datetime_utc).

Pixel: celda de la grilla de MIROVA (paso 375 m en VIIRS 375, 750 m en VIIRS 750, 1000 m en MODIS). Su fraccion
de agua es la fraccion de celdas JRC con ocurrencia >= 50 % dentro de un cuadrado de lado = paso centrado en el
lat/lon del pixel (aproximacion: la huella real fuera de nadir es mas grande; esto es la celda remuestreada).
Orilla: fraccion de agua > 0 en un cuadrado de 3 x paso (los vecinos del 3 x 3, que entran al contraste dNTI).

Uso: python -I medir_agua.py <raiz_repo> <dir_salida>
"""
import csv
import json
import math
import os
import sys
from collections import defaultdict

import numpy as np
import rasterio
from rasterio.windows import from_bounds
import yaml

REPO = sys.argv[1]
OUT = sys.argv[2]
CACHE = os.path.join(OUT, "cache_jrc")
os.makedirs(CACHE, exist_ok=True)

UMBRAL_OCURRENCIA = 50   # % del tiempo con agua 1984-2021: agua "permanente o casi"
PASO_M = {"MODIS": 1000.0, "V750": 750.0, "V375": 375.0}


def familia(sensor):
    if sensor.startswith("MODIS"):
        return "MODIS"
    if sensor.endswith("_750"):
        return "V750"
    return "V375"


def tile_url(lat, lon):
    # Teselas de 10 grados nombradas por su esquina noroeste.
    lon0 = int(math.floor(lon / 10.0) * 10)   # -70.5 -> -80
    lat0 = int(math.ceil(lat / 10.0) * 10)    # -36 -> -30
    lon_s = f"{abs(lon0)}{'W' if lon0 < 0 else 'E'}"
    lat_s = f"{abs(lat0)}{'S' if lat0 <= 0 else 'N'}" if lat0 != 0 else "0N"
    return ("/vsicurl/https://storage.googleapis.com/global-surface-water/downloads2021/occurrence/"
            f"occurrence_{lon_s}_{lat_s}v1_4_2021.tif")


class Mascara:
    """Ventana JRC alrededor de un volcan (cacheada en disco)."""

    def __init__(self, nombre, lat, lon, dlat=0.36, dlon=None):
        if dlon is None:
            dlon = 0.36 / math.cos(math.radians(lat))
        self.b = (lon - dlon, lat - dlat, lon + dlon, lat + dlat)
        f = os.path.join(CACHE, f"{nombre}.npz")
        if os.path.exists(f):
            z = np.load(f)
            self.a, self.t = z["a"], tuple(z["t"])
            return
        # La ventana puede cruzar el borde de una tesela: se arma por partes.
        res = 0.00025
        W, S, E, N = self.b
        nx = int(round((E - W) / res)); ny = int(round((N - S) / res))
        a = np.full((ny, nx), 255, dtype=np.uint8)
        urls = {tile_url(la, lo) for la in (S + 1e-6, N - 1e-6) for lo in (W + 1e-6, E - 1e-6)}
        for u in urls:
            with rasterio.open(u) as ds:
                tb = ds.bounds
                iw, is_, ie, in_ = max(W, tb.left), max(S, tb.bottom), min(E, tb.right), min(N, tb.top)
                if iw >= ie or is_ >= in_:
                    continue
                win = from_bounds(iw, is_, ie, in_, ds.transform)
                sub = ds.read(1, window=win, boundless=True, fill_value=255)
                c0 = int(round((iw - W) / res)); r0 = int(round((N - in_) / res))
                h, w = sub.shape
                h = min(h, ny - r0); w = min(w, nx - c0)
                a[r0:r0 + h, c0:c0 + w] = sub[:h, :w]
        self.a = a
        self.t = (W, N, res)
        np.savez_compressed(f, a=a, t=np.array(self.t))

    def fraccion(self, lat, lon, lado_m):
        W, N, res = self.t
        hl = lado_m / 2.0 / 111320.0
        hn = lado_m / 2.0 / (111320.0 * math.cos(math.radians(lat)))
        r0 = int((N - (lat + hl)) / res); r1 = int(math.ceil((N - (lat - hl)) / res))
        c0 = int((lon - hn - W) / res); c1 = int(math.ceil((lon + hn - W) / res))
        if r0 < 0 or c0 < 0 or r1 > self.a.shape[0] or c1 > self.a.shape[1]:
            return None, None
        sub = self.a[r0:r1, c0:c1]
        n = sub.size
        agua = ((sub >= UMBRAL_OCURRENCIA) & (sub <= 100)).sum() / n
        sindato = (sub == 255).sum() / n
        return float(agua), float(sindato)


def cargar(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh).get("records", [])
    except FileNotFoundError:
        return []


def main():
    with open(os.path.join(REPO, "volcanoes.yaml"), encoding="utf-8") as fh:
        vy = yaml.safe_load(fh)
    volcs = vy["volcanoes"] if isinstance(vy, dict) else vy
    filas_pix, filas_rec = [], []
    cobertura = []
    for v in volcs:
        nombre, lat, lon = v["name"], float(v["lat"]), float(v["lon"])
        recs = {}
        fuentes = defaultdict(int)
        for sub in ("historia_34", "sombra_34", "mirova_equivalent"):
            for r in cargar(os.path.join(REPO, "data", sub, f"{nombre}.json")):
                if not r.get("via_codigo_mirova"):
                    continue
                k = (r.get("sensor"), r.get("datetime_utc"))
                if k in recs:
                    continue
                recs[k] = (sub, r)
                fuentes[sub] += 1
        if not recs:
            continue
        det = [(s, r) for s, r in recs.values() if r.get("anomaly_pixels")]
        fechas = sorted(r["datetime_utc"] for _, r in recs.values())
        cobertura.append({"volcan": nombre, "records": len(recs), "detecciones": len(det),
                          "desde": fechas[0], "hasta": fechas[-1],
                          "fuentes": dict(fuentes)})
        if not det:
            continue
        m = Mascara(nombre, lat, lon)
        for sub, r in det:
            fam = familia(r["sensor"])
            paso = PASO_M[fam]
            sz = r.get("solar_zenith_deg")
            noche = sz is not None and sz > 90.0
            pix = r["anomaly_pixels"]
            mejor = None
            n_agua = 0
            n_orilla = 0
            for p in pix:
                fa, fs = m.fraccion(p["lat"], p["lon"], paso)
                fo, _ = m.fraccion(p["lat"], p["lon"], 3 * paso)
                if fa is None:
                    continue
                en_agua = fa >= 0.5
                orilla = (not en_agua) and fo is not None and fo > 0.0
                n_agua += en_agua
                n_orilla += orilla
                filas_pix.append({"volcan": nombre, "sensor": r["sensor"], "familia": fam,
                                  "datetime_utc": r["datetime_utc"], "noche": int(noche),
                                  "lat": p["lat"], "lon": p["lon"], "dist_km": p.get("dist_km"),
                                  "bt_k": p.get("bt_k"), "frac_agua": round(fa, 3),
                                  "frac_agua_3x": round(fo, 3) if fo is not None else "",
                                  "frac_sindato": round(fs, 3)})
                bt = p.get("bt_k") or -1
                if mejor is None or bt > mejor[0]:
                    mejor = (bt, fa, fo, p)
            if mejor is None:
                continue
            bt, fa, fo, p = mejor
            if fa >= 0.5:
                clase = "agua"
            elif fo is not None and fo > 0.0:
                clase = "orilla"
            else:
                clase = "tierra"
            pc = r.get("primary_cluster") or {}
            vrp = pc.get("vrp_mw") if pc.get("vrp_mw") is not None else r.get("vrp_mw")
            filas_rec.append({"volcan": nombre, "fuente": sub, "sensor": r["sensor"], "familia": fam,
                              "datetime_utc": r["datetime_utc"], "mes": r["datetime_utc"][5:7],
                              "noche": int(noche), "solar_zenith_deg": sz,
                              "n_pix": len(pix), "n_pix_agua": n_agua, "n_pix_orilla": n_orilla,
                              "clase_pico": clase, "frac_agua_pico": round(fa, 3),
                              "bt_pico_k": bt, "t_bg_k": r.get("t_bg_k"),
                              "vrp_mw": vrp, "vrp_record_mw": r.get("vrp_mw"),
                              "dist_km": r.get("final_hotspot_dist_km"),
                              "distance_class": r.get("distance_class")})
    for nom, filas in (("pixeles.csv", filas_pix), ("records.csv", filas_rec)):
        if not filas:
            continue
        with open(os.path.join(OUT, nom), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(filas[0].keys()))
            w.writeheader(); w.writerows(filas)
    with open(os.path.join(OUT, "cobertura.json"), "w", encoding="utf-8") as fh:
        json.dump(cobertura, fh, ensure_ascii=False, indent=1)
    print("volcanes con records:", len(cobertura), "records con deteccion:", len(filas_rec),
          "pixeles:", len(filas_pix))


if __name__ == "__main__":
    main()
