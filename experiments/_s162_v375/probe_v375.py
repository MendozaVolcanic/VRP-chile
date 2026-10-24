# -*- coding: utf-8 -*-
"""S162 V375-B y V375-C, runner: el port del código de MIROVA en VIIRS 375 con TODOS los brazos de ROI (brazos.py) y
la producción (K) sobre el MISMO gránulo, para las pasadas de objetivos_v375_bc.json. Sólo lectura: no escribe en
data/, no commitea, no hace push.

Reutiliza sin cambios la bajada, la lectura, la grilla de 134 x 134 de MIROVA y el re-corrido de K del probe de S159
(experiments/_s159/portes/probe_portes.py, «PP»; sus controles valieron 391 de 391, 10 de 10 y 149 de 149). Lo único
nuevo es que en vez de tres cajas corre los diez brazos de brazos.py y guarda la grilla (mir, tir) de cada pasada, para
que el evaluador recalcule los brazos sin red (control de que lo que se lee es lo que se calculó).

Pregunta 1 del instrumento: una pasada que no se baja, no se lee o cuyo volcán no está en el gránulo queda con estado
distinto de «ok» y el job sale 2 (S141); nunca 0 píxeles silencioso. Pregunta 2: antes de bajar nada se corren las
pruebas sin red de PP y de brazos.py (escena sintética: sin foco 0 píxeles en todos los brazos; foco débil en el
cráter de Tupungatito: M14 no lo ve, C14 y CIRC sí). Si fallan, no se corre.
Uso: python probe_v375.py --objetivos objetivos_v375_bc.json --out out --chunk 0 --nchunks 28 [--solo id,id]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "experiments/_s159/portes"))
sys.path.insert(0, str(AQUI))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import probe_portes as PP  # noqa: E402
import brazos as BR  # noqa: E402
import probar_brazos as PB  # noqa: E402

SEMILLAS = 20


def procesar(o, V, destino, outdir):
    g = o["grilla"]
    t0 = time.time()
    r = {"id": o["id"], "volcan": o["volcan"], "hora_utc": o["hora_utc"], "b": "VIIRS375", "granule": o["granule"]}
    par, err = PP.bajar_par(o["granule"], g["centro_lat"], g["centro_lon"], destino)
    if err:
        r["estado"] = err
        return r
    l1b, geo = par
    r["archivos"] = [l1b.name, geo.name]
    try:
        crop, dmin = PP.leer_viirs(l1b, geo, ("I04", "I05"), g["centro_lat"], g["centro_lon"])
        if crop is None:
            r["estado"] = "volcan_fuera_del_granulo"
            r["dist_min_km"] = dmin
            return r
        d = PP._haversine(crop["lat"], crop["lon"], g["centro_lat"], g["centro_lon"])
        if not np.isfinite(d).any() or np.nanmin(d) > 5:
            r["estado"] = "volcan_fuera_del_granulo"
            r["dist_min_km"] = None if not np.isfinite(d).any() else float(np.nanmin(d))
            return r
        i0 = np.unravel_index(np.nanargmin(np.where(np.isfinite(d), d, np.inf)), d.shape)
        geom = {k: float(crop[k][i0]) for k in ("sensor_zenith", "sensor_azimuth", "solar_zenith", "solar_azimuth")
                if k in crop}
        r["geometria_centro"] = geom
        r["saturados"] = crop.get("sat")
        dayflag = 0 if geom.get("solar_zenith", 180) > 90 else 1
        sg = PP.ORA.sunglint_deg(geom.get("sensor_zenith", 0), geom.get("solar_zenith", 0),
                                 geom.get("sensor_azimuth", 0), geom.get("solar_azimuth", 0))
        r["dayflag"], r["sunglint"] = dayflag, sg
        mir, tir = PP.grillar(crop, g, g["epsg"])
        if np.isnan(mir).sum() > mir.size // 2:
            r["port_estado"] = "grilla_incompleta"
        v = V[o["volcan"]]
        xc, yc = BR.crater_xy(g, v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"]))
        r["crater_xy"] = [xc, yc]
        r["port"] = BR.correr_brazos(mir, tir, g, g["X0"], g["Y0"], xc, yc, v["inner_radius_km"], o["volcan"],
                                     dayflag, sg, semillas=SEMILLAS)
        np.savez_compressed(outdir / f"grilla_{o['id']:04d}.npz", mir=mir.astype(np.float32),
                            tir=tir.astype(np.float32))
        try:
            r["K"] = PP.resumen_k("VIIRS375", o["volcan"], l1b, geo)
        except Exception as e:  # noqa: BLE001
            r["K"] = {"error": f"{type(e).__name__}: {e}", "traza": traceback.format_exc()[-1200:]}
        r["estado"] = "ok"
    except Exception as e:  # noqa: BLE001
        r["estado"] = f"error: {type(e).__name__}: {e}"
        r["traza"] = traceback.format_exc()[-1500:]
    finally:
        for q in (l1b, geo):
            try:
                q.unlink()
            except OSError:
                pass
    r["segundos"] = round(time.time() - t0, 1)
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--objetivos", default=str(AQUI / "objetivos_v375_bc.json"))
    ap.add_argument("--out", default="out")
    ap.add_argument("--chunk", type=int, default=0)
    ap.add_argument("--nchunks", type=int, default=1)
    ap.add_argument("--solo", default="")
    ap.add_argument("--sin-red", action="store_true")
    a = ap.parse_args()
    PP.prueba_sin_red()
    V = PB.volcanes()
    grillas = PB.prueba_cajas(V)
    PB.prueba_sintetica(V, grillas)
    print("PRUEBAS SIN RED DE BRAZOS OK", flush=True)
    if a.sin_red:
        return 0
    if not os.environ.get("EARTHDATA_TOKEN", "").strip():
        print("EARTHDATA_TOKEN vacio: no se corre (A71)")
        return 1
    from pipeline.fetch import auth
    auth()
    outdir = Path(a.out)
    outdir.mkdir(parents=True, exist_ok=True)
    destino = Path(os.environ.get("VRP_TMP_DIR", "/tmp/vrp_tmp")) / "granulos"
    objs = json.loads(Path(a.objetivos).read_text(encoding="utf-8"))["pasadas"]
    if a.solo:
        quiero = {int(x) for x in a.solo.split(",")}
        objs = [o for o in objs if o["id"] in quiero]
    mias = [o for n, o in enumerate(objs) if n % a.nchunks == a.chunk]
    print(f"VIIRS375 chunk {a.chunk}/{a.nchunks}: {len(mias)} pasadas", flush=True)
    resultados, faltan = [], 0
    for o in mias:
        print(f"== {o['id']} {o['volcan']} {o['hora_utc']} {o['clase']} {o['granule']}", flush=True)
        try:
            r = procesar(o, V, destino, outdir)
        except Exception as e:  # noqa: BLE001
            r = {"id": o["id"], "volcan": o["volcan"], "hora_utc": o["hora_utc"], "b": "VIIRS375",
                 "estado": f"error: {type(e).__name__}: {e}", "traza": traceback.format_exc()[-1500:]}
        if r.get("estado") != "ok":
            faltan += 1
        pf = (r.get("port") or {}).get("M14") or {}
        kr = ((r.get("K") or {}).get("record") or {})
        print(f"   estado={r.get('estado')} {r.get('segundos')} s | M14 {pf.get('npix')} px {pf.get('vrp_mw')} | "
              f"K pc {(kr.get('primary_cluster') or {}).get('vrp_mw')} dc {kr.get('distance_class')}", flush=True)
        resultados.append(r)
        (outdir / f"resultados_VIIRS375_{a.chunk:02d}.json").write_text(json.dumps(resultados, default=float),
                                                                         encoding="utf-8")
    print(f"pasadas sin procesar: {faltan} de {len(mias)}", flush=True)
    return 2 if faltan else 0


if __name__ == "__main__":
    sys.exit(main())
