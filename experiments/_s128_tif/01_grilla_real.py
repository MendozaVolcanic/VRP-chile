# -*- coding: utf-8 -*-
"""S128 Fase 2 · sonda P1 — LA GRILLA REAL DE MIROVA, desde evidencia EXTERNA.

Por que importa (el fenomeno antes que el codigo): MIROVA no publica sus escenas
sobre la lat/lon del volcan; las publica sobre una GRILLA fija. Si esa grilla se
ancla a una ESQUINA y nosotros centramos la nuestra en el crater, las dos mallas
quedan corridas media celda o mas, y entonces "el pixel del crater" de ellos y el
nuestro no son el mismo trozo de terreno. Eso es la divergencia D17, que hasta hoy
solo se pudo argumentar desde nuestro propio codigo.

Los GeoTIFF de `../mirova-tif-archive` son la UNICA evidencia externa que existe
sobre esa grilla: son las escenas que MIROVA publico, con su georreferencia adentro.

Mide tres cosas, todas verificables:
  1. si los tres sensores comparten un borde (cual) o un centro;
  2. cuanto se corre el centro del TIF respecto del crater y del `mirova_center`
     que hoy tiene volcanoes.yaml;
  3. si los bounds son estables entre pasadas del mismo volcan+sensor (una grilla
     fija tiene que serlo; si varian, no hay grilla).

Read-only. Escribe solo su JSON.
"""
import collections
import csv
import io
import json
import os
import statistics as st
import sys

import rasterio
import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
ARCH = os.path.join(os.path.dirname(ROOT), "mirova-tif-archive")

# Alias: el archivo de TIF usa otros nombres que volcanoes.yaml.
ALIAS_TIF = {"ChillanNevadosde": "NevadosDeChillan"}

vol_cfg = {}
with open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8") as fh:
    y = yaml.safe_load(fh)
for v in (y["volcanoes"] if isinstance(y, dict) and "volcanoes" in y else y):
    vol_cfg[v["name"]] = v

rows = list(csv.DictReader(open(os.path.join(ARCH, "index.csv"), encoding="utf-8")))
por = collections.defaultdict(list)
for r in rows:
    por[(ALIAS_TIF.get(r["volcano"], r["volcano"]), r["sensor"])].append(r)

R = {"_meta": {"archivo": ARCH, "filas_index": len(rows),
               "tif_unicos": len({r["tif_path"] for r in rows}),
               "md5_unicos": len({r["md5"] for r in rows})}}
detalle = {}

for (vol, sen), rs in sorted(por.items()):
    bounds, shapes, crs = [], set(), set()
    leidos = 0
    for r in rs:
        p = os.path.join(ARCH, r["tif_path"].replace("/", os.sep))
        if not os.path.exists(p):
            continue
        try:
            with rasterio.open(p) as ds:
                b = ds.bounds
                bounds.append((b.left, b.bottom, b.right, b.top))
                shapes.add((ds.height, ds.width))
                crs.add(str(ds.crs))
                leidos += 1
        except Exception:                                     # noqa: BLE001
            continue
    if not bounds:
        continue
    L, B, Rt, T = zip(*bounds)

    def disp(xs):
        """Dispersion en METROS aproximados (1 grado lat ~ 111,32 km)."""
        return round((max(xs) - min(xs)) * 111320.0, 1)

    detalle[vol + "|" + sen] = {
        "n_tif_leidos": leidos,
        "shape": sorted(shapes), "crs": sorted(crs),
        "oeste": {"mediana": round(st.median(L), 6), "dispersion_m": disp(L)},
        "este": {"mediana": round(st.median(Rt), 6), "dispersion_m": disp(Rt)},
        "sur": {"mediana": round(st.median(B), 6), "dispersion_m": disp(B)},
        "norte": {"mediana": round(st.median(T), 6), "dispersion_m": disp(T)},
        "centro": [round(st.median(L) / 2 + st.median(Rt) / 2, 6),
                   round(st.median(B) / 2 + st.median(T) / 2, 6)],
        "ancho_grados": round(st.median(Rt) - st.median(L), 6),
        "alto_grados": round(st.median(T) - st.median(B), 6),
    }

R["por_volcan_sensor"] = detalle

# --- La pregunta del prompt: los 3 sensores, ¿comparten borde o centro? -------
comparacion = {}
for vol in sorted({k.split("|")[0] for k in detalle}):
    ss = {k.split("|")[1]: v for k, v in detalle.items() if k.startswith(vol + "|")}
    if len(ss) < 2:
        continue
    cfg = vol_cfg.get(vol, {})
    mc = cfg.get("mirova_center")
    vent = (cfg.get("vent_lat", cfg.get("lat")), cfg.get("vent_lon", cfg.get("lon")))

    def spread(campo, idx=None):
        vals = [s[campo]["mediana"] if idx is None else s["centro"][idx]
                for s in ss.values()]
        return round((max(vals) - min(vals)) * 111320.0, 1)

    comparacion[vol] = {
        "sensores": sorted(ss),
        "desacuerdo_entre_sensores_m": {
            "borde_oeste": spread("oeste"), "borde_este": spread("este"),
            "borde_sur": spread("sur"), "borde_norte": spread("norte"),
            "centro_lon": spread(None, 0), "centro_lat": spread(None, 1),
        },
        "centro_del_tif_por_sensor": {k: v["centro"] for k, v in ss.items()},
        "volcanoes_yaml": {
            "lat_lon": [cfg.get("lat"), cfg.get("lon")],
            "vent": list(vent),
            "mirova_center": mc,
        },
    }
    # Offset del centro del TIF respecto de los dos anclas que usa el pipeline.
    for k, v in ss.items():
        clon, clat = v["centro"]
        off = {}
        if cfg.get("lat") is not None:
            off["vs_volcano_latlon_m"] = [
                round((clon - cfg["lon"]) * 111320.0 * 0.77, 1),
                round((clat - cfg["lat"]) * 111320.0, 1)]
        if mc:
            mlat, mlon = (mc if isinstance(mc, (list, tuple))
                          else (mc.get("lat"), mc.get("lon")))
            off["vs_mirova_center_m"] = [round((clon - mlon) * 111320.0 * 0.77, 1),
                                         round((clat - mlat) * 111320.0, 1)]
        comparacion[vol].setdefault("offset_centro_tif", {})[k] = off

R["comparacion_por_volcan"] = comparacion

out = os.path.join(AQUI, "01_grilla_real.json")
json.dump(R, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("escrito:", out)
print(json.dumps(R["_meta"], ensure_ascii=False))
print("\n== Desacuerdo entre los 3 sensores, en metros (0 = comparten ese borde) ==")
print(f"{'volcan':22s}{'oeste':>9s}{'este':>9s}{'sur':>9s}{'norte':>9s}"
      f"{'c_lon':>9s}{'c_lat':>9s}")
for v, d in sorted(comparacion.items()):
    z = d["desacuerdo_entre_sensores_m"]
    print(f"{v:22s}{z['borde_oeste']:>9.1f}{z['borde_este']:>9.1f}"
          f"{z['borde_sur']:>9.1f}{z['borde_norte']:>9.1f}"
          f"{z['centro_lon']:>9.1f}{z['centro_lat']:>9.1f}")
print("\n== Estabilidad de los bounds entre pasadas (dispersion en m) ==")
for k, d in sorted(detalle.items()):
    print(f"{k:34s} n={d['n_tif_leidos']:>4d} shape={str(d['shape'][0]):>10s} "
          f"disp O/E/S/N = {d['oeste']['dispersion_m']:>7.1f}"
          f"{d['este']['dispersion_m']:>9.1f}{d['sur']['dispersion_m']:>9.1f}"
          f"{d['norte']['dispersion_m']:>9.1f}")
