# -*- coding: utf-8 -*-
"""S159, censo del oráculo en VIIRS 750: K (producción) y el oráculo de MIROVA sobre el MISMO gránulo, en TODAS las
pasadas de objetivos.json. Sólo lectura: no escribe en data/, no commitea, no hace push.

Reúsa experiments/_s159/n/probe_n.py sin cambiar su lógica (bajada con reintentos y búsqueda por ventana, grilla de
GEO con interpolador lineal, oráculo con caja por defecto y con el recuadro sensible de 21 x 21, brazo K pasado por
store.append_record en carpeta temporal). Diferencias declaradas con el probe de N: sólo el brazo K (sin K2, C, F,
FC), sólo la variante lineal de la grilla de GEO (sin vecino, cúbico ni R2), sin .npz; y por pasada se agrega la
cobertura del gránulo en la grilla (celdas sin dato en el 67 x 67, en el recuadro de 21 x 21 y en la cumbre de 7 x 7)
para separar las pasadas partidas.

Pregunta 1 (si el oráculo estuviera roto, ¿se vería?): el control positivo son las alertas de MIROVA (N: 145 de 181
detectadas con razón 0,999); y el control 2 compara, pasada por pasada, con los números de N en las 508 que N midió.
Pregunta 2 (instrumento muerto): una pasada que no baja o falla queda con estado distinto de "ok" y el job sale 2;
K tiene que reproducir la publicación y el pc.vrp_mw de producción en todas las pasadas ok.
Uso: python probe_censo.py --objetivos objetivos.json --out out --chunk 0 --nchunks 32
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
RAIZ = AQUI.parents[2]
sys.path.insert(0, str(RAIZ / "experiments/_s159/n"))
import probe_n as PN  # noqa: E402  (agrega a sys.path la raíz, scripts/, el oráculo y probe_granulos)

ORA, PG = PN.ORA, PN.PG
C = PN.N // 2


def cobertura(m13g):
    nan = ~np.isfinite(m13g)
    return {"nan_67": int(nan.sum()),
            "nan_21": int(nan[C - 10:C + 11, C - 10:C + 11].sum()),
            "nan_7": int(nan[C - 3:C + 4, C - 3:C + 4].sum()),
            "nan_centro": bool(nan[C, C])}


def procesar_granulo(objs, destino):
    o0 = objs[0]
    PG.LATLON[0], PG.LATLON[1] = o0["grilla"]["centro_lat"], o0["grilla"]["centro_lon"]
    par, err = PN.bajar_con_reintentos(o0["granule"], destino)
    if err:
        return [{"id": o["id"], "volcan": o["volcan"], "hora_utc": o["hora_utc"], "estado": err} for o in objs]
    l1b, geo = par
    rad, _attrs = PG.leer_l1b(l1b)
    lat, lon, ang = PG.leer_geo(geo)
    res = []
    for o in objs:
        t0 = time.time()
        r = {"id": o["id"], "volcan": o["volcan"], "hora_utc": o["hora_utc"], "archivos": [l1b.name, geo.name]}
        try:
            g = o["grilla"]
            dlat = np.radians(lat - g["centro_lat"])
            dlon = np.radians(lon - g["centro_lon"])
            a = (np.sin(dlat / 2) ** 2 + np.cos(np.radians(lat)) * np.cos(np.radians(g["centro_lat"]))
                 * np.sin(dlon / 2) ** 2)
            dist = 6371.0 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
            r["dist_min_km"] = None if not np.isfinite(dist).any() else float(np.nanmin(dist))
            if r["dist_min_km"] is None or r["dist_min_km"] > 5:
                r["estado"] = "volcan_fuera_del_granulo"
                res.append(r)
                continue
            i0 = np.unravel_index(np.nanargmin(np.where(np.isfinite(dist), dist, np.inf)), dist.shape)
            geom = {k: float(v[i0]) for k, v in ang.items()}
            r["geometria_centro"] = geom
            dayflag = 0 if geom.get("solar_zenith", 180) > 90 else 1
            sg = ORA.sunglint_deg(geom.get("sensor_zenith", 0), geom.get("solar_zenith", 0),
                                  geom.get("sensor_azimuth", 0), geom.get("solar_azimuth", 0))
            r["dayflag"], r["sunglint"] = dayflag, sg
            gg = PN.grillar(lat, lon, rad["M13"], rad["M15"], g, g["ul_x"], g["ul_y"], ("linear",))
            if gg is None:
                r["oraculo_estado"] = "grilla_incompleta"
                r["oraculo"] = {}
            else:
                a13, a15 = gg["linear"]
                r["cobertura"] = cobertura(a13)
                r["oraculo"] = {"geo_linear": PN.oraculo(a13, a15, dayflag, sg),
                                "geo_linear_anillo_sensible": PN.oraculo(a13, a15, dayflag, sg, sensible=True)}
            if dayflag == 0:
                try:
                    r["brazos"] = {"K": PN.resumen_brazo("K", None, o["volcan"], l1b, geo)}
                except Exception as e:  # noqa: BLE001
                    r["brazos"] = {"K": {"error": f"{type(e).__name__}: {e}", "traza": traceback.format_exc()[-1200:]}}
            r["estado"] = "ok"
        except Exception as e:  # noqa: BLE001
            r["estado"] = f"error: {type(e).__name__}: {e}"
            r["traza"] = traceback.format_exc()[-1500:]
        r["segundos"] = round(time.time() - t0, 1)
        res.append(r)
    for q in (l1b, geo):
        try:
            q.unlink()
        except OSError:
            pass
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--objetivos", default=str(AQUI / "objetivos.json"))
    ap.add_argument("--out", default="out")
    ap.add_argument("--chunk", type=int, default=0)
    ap.add_argument("--nchunks", type=int, default=1)
    ap.add_argument("--solo", default="")
    ap.add_argument("--sin-red", action="store_true")
    a = ap.parse_args()
    PN.prueba_sin_red()
    PG.prueba_sintetica()
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
    objs = json.loads(Path(a.objetivos).read_text(encoding="utf-8"))
    if a.solo:
        quiero = {int(x) for x in a.solo.split(",")}
        objs = [o for o in objs if o["id"] in quiero]
    grupos = {}
    for o in objs:
        grupos.setdefault(o["granule"], []).append(o)
    claves = sorted(grupos)
    mias = [k for n, k in enumerate(claves) if n % a.nchunks == a.chunk]
    n_obj = sum(len(grupos[k]) for k in mias)
    print(f"chunk {a.chunk}/{a.nchunks}: {len(mias)} granulos, {n_obj} pasadas", flush=True)
    resultados, faltan = [], 0
    for k in mias:
        print(f"== {k} ({len(grupos[k])} pasadas)", flush=True)
        try:
            rs = procesar_granulo(grupos[k], destino)
        except Exception as e:  # noqa: BLE001
            rs = [{"id": o["id"], "volcan": o["volcan"], "hora_utc": o["hora_utc"],
                   "estado": f"error: {type(e).__name__}: {e}", "traza": traceback.format_exc()[-1500:]}
                  for o in grupos[k]]
        for r in rs:
            if r.get("estado") not in ("ok", "volcan_fuera_del_granulo"):  # fuera = la pasada no mira el volcan
                faltan += 1
            kk = ((r.get("brazos") or {}).get("K") or {})
            kpc = ((kk.get("record") or {}).get("primary_cluster") or {}).get("vrp_mw")
            od = (r.get("oraculo") or {}).get("geo_linear", {})
            osn = (r.get("oraculo") or {}).get("geo_linear_anillo_sensible", {})
            print(f"   {r['id']} {r['volcan']} {r['hora_utc']} estado={r.get('estado')} O={od.get('npix')}px "
                  f"{od.get('vrp_mw')} Os={osn.get('npix')}px {osn.get('vrp_mw')} | K pc {kpc} "
                  f"| cob {r.get('cobertura')}", flush=True)
            resultados.append(r)
        (outdir / f"resultados_{a.chunk:02d}.json").write_text(json.dumps(resultados, default=float), encoding="utf-8")
    print(f"pasadas sin procesar: {faltan} de {n_obj}", flush=True)
    return 2 if faltan else 0


if __name__ == "__main__":
    sys.exit(main())
