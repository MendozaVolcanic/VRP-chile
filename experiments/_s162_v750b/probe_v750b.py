# -*- coding: utf-8 -*-
"""S162 V750-B (y confirmación de V750-C): la ROI del código de MIROVA por volcán en VIIRS 750, y el código sobre la
geometría nativa del gránulo. Sólo lectura: no escribe en data/, no commitea, no hace push.

POR QUÉ. Pre-registro: experiments/_s162_v750b/PREREGISTRO_V750B.md. El código de MIROVA (port de R2, validado contra
Octave) corre sobre la grilla GEO lineal de cada pasada con cuatro matrices BOX (B0 caja del .m, B1 21 x 21 sensible,
B2 caja de 7 x 7 en el cráter de volcanoes.yaml, B3 círculo inner_radius_km sensible; B4 se arma en el analizador con
B0 y B1). En el subconjunto S_C corre además sobre la ventana NATIVA del gránulo (N0 caja del .m, N1 sensible), que es
el brazo «sin remuestreo» que V750-C no pudo correr porque las grillas de N no traen la ventana nativa.

Reúsa experiments/_s159/n/probe_n.py sin cambiar su lógica (bajada con reintentos, grilla GEO, brazo K por
store.append_record en carpeta temporal). Guarda por pasada la grilla GEO lineal (float32) y, en S_C, la ventana nativa.

Pregunta 1 (si el oráculo estuviera roto, ¿se vería?): B0 y B1 tienen que reproducir al censo S159 en las pasadas
comunes (control del analizador), y B0 tiene que perder protegidas de Cordón Caulle (control positivo). La función
cajas() se prueba sin red (prueba_sin_red_v750b): B2 y B3 tienen que diferir de B0 en Cordón Caulle y Tupungatito.
Pregunta 2 (instrumento muerto): una pasada que no baja o falla queda con estado distinto de "ok" y el job sale 2; K
tiene que reproducir la publicación y el pc.vrp_mw de producción.
Uso: python probe_v750b.py --objetivos objetivos_v750b.json --out out --chunk 0 --nchunks 32
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
sys.path.insert(0, str(RAIZ / "experiments/_s159/n"))
import probe_n as PN  # noqa: E402  (agrega a sys.path la raíz, scripts/, el oráculo y probe_granulos)

ORA, PG = PN.ORA, PN.PG
N = PN.N
C = N // 2
MEDIA_VENTANA = 33  # ventana nativa de 67 x 67 píxeles alrededor del píxel más cercano al centro


def cajas(celda_crater, inner_km):
    """Las cuatro BOX de la grilla. celda_crater = (fila, columna) del cráter de volcanoes.yaml en la grilla GEO."""
    b0 = PG.caja_mirova()
    b1 = b0.copy()
    b1[b1 == 1] = 2
    b2 = b0.copy()
    b2[b2 == 2] = 1
    f, c = celda_crater
    if 3 <= f <= N - 4 and 3 <= c <= N - 4:
        b2[f - 3:f + 4, c - 3:c + 4] = 2
    r, q = np.indices((N, N))
    dk = np.hypot(r - C, q - C) * PN.CELDA / 1000.0
    b3 = b0.copy()
    b3[b3 == 2] = 1
    b3[dk <= inner_km] = 2
    # B0e: la matriz de ejemplo del paquete OSF tal cual (VJ1 2023-05-19; experiments/_s158_audit_r2/rb/00_box_mat.txt):
    # BOX == 1 en filas 22..42 y columnas 24..42 (21 x 19, no simétrica), BOX == 2 en 30..36. Informativo (verificador
    # de V750-C, VV-01: B0 la simetriza a 21 x 21).
    b0e = np.zeros((N, N))
    b0e[22:43, 24:43] = 1
    b0e[30:37, 30:37] = 2
    return {"B0": b0, "B0e": b0e, "B1": b1, "B2": b2, "B3": b3}


def oraculo_caja(m13, m15, dayflag, sg, box, semillas=None):
    """Igual a probe_n.oraculo, con la BOX como argumento (semillas=0 omite la banda de triangulación)."""
    mask, _lista, d = ORA.detectar(m13, m15, box, dayflag, sg, devolver_diag=True)
    r = ORA.vrp(m13, mask)
    rr, cc = np.nonzero(mask)
    out = {"motivo_vacio": d.get("motivo"), "n_abs": d.get("n_abs"), "n_p1": d.get("n_p1"), "n_p2": d.get("n_p2"),
           "npix": r["npix"], "vrp_mw": None if r["npix"] == 0 else float(r["VRP_MW"]),
           "pixeles": [[int(a), int(b), int(box[a, b]), round(float(np.hypot(a - C, b - C) * 0.75), 2),
                        round(float(m13[a, b]), 5)] for a, b in zip(rr, cc)]}
    n_sem = PN.SEMILLAS if semillas is None else semillas
    if r["npix"] and n_sem:
        v = [ORA.vrp(m13, mask, jitter=1e-6, semilla=s)["VRP_MW"] for s in range(n_sem)]
        out["vrp_banda"] = [float(min(v)), float(max(v))]
    return out


def ventana_nativa(arrs, i0):
    """Recorte de 67 x 67 de cada arreglo del gránulo alrededor de i0, con NaN fuera del gránulo."""
    out = {}
    for k, a in arrs.items():
        w = np.full((N, N), np.nan, dtype=np.float64)
        r0, c0 = i0[0] - MEDIA_VENTANA, i0[1] - MEDIA_VENTANA
        rs, cs = max(r0, 0), max(c0, 0)
        re, ce = min(r0 + N, a.shape[0]), min(c0 + N, a.shape[1])
        w[rs - r0:re - r0, cs - c0:ce - c0] = a[rs:re, cs:ce]
        out[k] = w
    return out, (int(i0[0] - MEDIA_VENTANA), int(i0[1] - MEDIA_VENTANA))


def cobertura(m13g):
    nan = ~np.isfinite(m13g)
    return {"nan_67": int(nan.sum()), "nan_21": int(nan[C - 10:C + 11, C - 10:C + 11].sum()),
            "nan_7": int(nan[C - 3:C + 4, C - 3:C + 4].sum()), "nan_centro": bool(nan[C, C])}


def procesar_granulo(objs, destino, outdir):
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
            r["i0"] = [int(i0[0]), int(i0[1])]
            dayflag = 0 if geom.get("solar_zenith", 180) > 90 else 1
            sg = ORA.sunglint_deg(geom.get("sensor_zenith", 0), geom.get("solar_zenith", 0),
                                  geom.get("sensor_azimuth", 0), geom.get("solar_azimuth", 0))
            r["dayflag"], r["sunglint"] = dayflag, sg
            gg = PN.grillar(lat, lon, rad["M13"], rad["M15"], g, g["ul_x"], g["ul_y"], ("linear",))
            r["oraculo"] = {}
            if gg is None:
                r["oraculo_estado"] = "grilla_incompleta"
            else:
                a13, a15 = gg["linear"]
                r["cobertura"] = cobertura(a13)
                for nom, box in cajas(tuple(o["celda_crater"]), o["inner_km"]).items():
                    r["oraculo"][nom] = oraculo_caja(a13, a15, dayflag, sg, box)
                np.savez_compressed(outdir / f"grilla_{o['id']:05d}.npz", m13=a13.astype(np.float32),
                                    m15=a15.astype(np.float32))
            if o.get("en_sc"):
                vn, esq = ventana_nativa({"m13": rad["M13"], "m15": rad["M15"], "lat": lat, "lon": lon}, i0)
                r["nativo_esquina_fila_col"] = list(esq)
                b0 = PG.caja_mirova()
                b1 = b0.copy()
                b1[b1 == 1] = 2
                r["nativo"] = {"N0": oraculo_caja(vn["m13"], vn["m15"], dayflag, sg, b0),
                               "N1": oraculo_caja(vn["m13"], vn["m15"], dayflag, sg, b1)}
                np.savez_compressed(outdir / f"nativo_{o['id']:05d}.npz",
                                    **{k: v.astype(np.float32) for k, v in vn.items()},
                                    esquina=np.array(esq, dtype=np.int32))
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


def prueba_sin_red_v750b():
    """cajas(): B0 es la del .m; B1 no tiene anillo; B2 mueve la caja al cráter; B3 es un círculo. Y el recorte nativo
    respeta el borde del gránulo."""
    cj = cajas((C, C), 5.0)
    assert np.array_equal(cj["B0"], PG.caja_mirova())
    assert not (cj["B1"] == 1).any() and (cj["B1"] == 2).sum() == 21 * 21
    assert np.array_equal(cj["B2"], cj["B0"]), "cráter en el centro: B2 tiene que ser B0"
    assert (cj["B0e"] == 1).sum() == 350 and (cj["B0e"] == 2).sum() == 49, "B0e: los conteos de 00_box_mat.txt"
    cj2 = cajas((C - 6, C - 6), 7.0)   # Tupungatito: 4,9 km al NW
    assert (cj2["B2"] == 2).sum() == 49 and cj2["B2"][C - 6, C - 6] == 2 and cj2["B2"][C, C] == 1
    assert cj2["B3"][C, C] == 2 and (cj2["B3"] == 2).sum() > 49
    a = np.arange(100 * 80, dtype=float).reshape(100, 80)
    vn, esq = ventana_nativa({"x": a}, (5, 78))
    assert esq == (5 - MEDIA_VENTANA, 78 - MEDIA_VENTANA)
    assert vn["x"][MEDIA_VENTANA, MEDIA_VENTANA] == a[5, 78]
    assert np.isnan(vn["x"][0, 0]) and np.isnan(vn["x"][MEDIA_VENTANA, -1])
    print("prueba_sin_red_v750b: ok", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--objetivos", default=str(AQUI / "objetivos_v750b.json"))
    ap.add_argument("--out", default="out")
    ap.add_argument("--chunk", type=int, default=0)
    ap.add_argument("--nchunks", type=int, default=1)
    ap.add_argument("--solo", default="")
    ap.add_argument("--sin-red", action="store_true")
    a = ap.parse_args()
    PN.prueba_sin_red()
    PG.prueba_sintetica()
    prueba_sin_red_v750b()
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
            rs = procesar_granulo(grupos[k], destino, outdir)
        except Exception as e:  # noqa: BLE001
            rs = [{"id": o["id"], "volcan": o["volcan"], "hora_utc": o["hora_utc"],
                   "estado": f"error: {type(e).__name__}: {e}", "traza": traceback.format_exc()[-1500:]}
                  for o in grupos[k]]
        for r in rs:
            if r.get("estado") not in ("ok", "volcan_fuera_del_granulo"):
                faltan += 1
            orc = r.get("oraculo") or {}
            print(f"   {r['id']} {r['volcan']} {r['hora_utc']} estado={r.get('estado')} "
                  + " ".join(f"{n}={x.get('npix')}px" for n, x in orc.items())
                  + (" | nativo " + " ".join(f"{n}={x.get('npix')}px" for n, x in r["nativo"].items())
                     if r.get("nativo") else ""), flush=True)
            resultados.append(r)
        (outdir / f"resultados_{a.chunk:02d}.json").write_text(json.dumps(resultados, default=float), encoding="utf-8")
    print(f"pasadas sin procesar: {faltan} de {n_obj}", flush=True)
    return 2 if faltan else 0


if __name__ == "__main__":
    sys.exit(main())
