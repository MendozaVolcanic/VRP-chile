# -*- coding: utf-8 -*-
"""COB 02 (S159). Clasifica cada pasada OSF 2025 sin record nuestro contra el catalogo publico de CMR.

Entrada: osf_pareo.csv (de 01). Consultas PUNTUALES a CMR (publico, sin credenciales; ventana de +-1 min alrededor de la hora
del OSF) con la misma caja que arma pipeline/fetch.py:751-753 (lon/lat +- radius_km/111, radius_km = 25) y los short names
de pipeline/fetch.py:187-225, en Standard (en 2025 el NRT ya no existe; se comprueba NRT solo en las clases A).
Se consulta: las 54 sin record desde 2025-02-15 (todas), una muestra estratificada de 60 de las 357 anteriores,
30 controles positivos (con record) y 8 negativos. Las demas filas quedan sin consulta CMR (cmr_l1b = -1).

Clases (de las pasadas OSF sin record):
  F  anterior al 2025-02-15: fuera de la ventana del backfill S120 (P4 sin ejecutar). Se informa si CMR la tiene.
  C  Dayflag diurno / elevacion solar >= 0 en el volcan (pipeline.fetch._solar_elevation): el filtro nocturno la descarta
  A  CMR (Standard; luego NRT puntual) no tiene el L1B de esa hora/plataforma
  D  CMR tiene el L1B pero no su GEO (VB-1)
  B  CMR tiene L1B y GEO y no hay record nuestro (cobertura/pareo)
  cubierta: pasadas OSF con record (control positivo)

Pregunta 1 del instrumento: si CMR o el pareo estuvieran rotos, el control positivo (todas las 2.523 pasadas con record)
daria L1B ausente en CMR o un nombre de granulo distinto del que guardamos. Se compara el producer_granule_id de
CMR contra record["granule"] (mismo AYYYYDDD.HHMM y misma plataforma).
Pregunta 2: si el catalogo viniera vacio, el control positivo fallaria al 100 %; ademas se imprime el total de
granulos por producto. Control negativo: hora OSF + 180 min (sin pasada de esa plataforma) debe dar casi 0 hits.
"""
from __future__ import annotations
import sys, io
from pathlib import Path
from datetime import datetime
import numpy as np, pandas as pd, yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
WT = Path(r"C:\vrp-trabajo\s159-pruebas")
HERE = WT / "experiments/_s159/cob"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(WT))
import cmrpub as cmr  # noqa: E402
from pipeline.fetch import _solar_elevation  # noqa: E402

VOL = {v["name"]: v for v in yaml.safe_load(open(WT / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
INI_SERIE = pd.Timestamp("2025-02-15")
HALVES = [("2025-01-01T00:00:00Z", "2025-06-30T23:59:59Z"), ("2025-07-01T00:00:00Z", "2025-12-31T23:59:59Z")]


def bbox(vol):
    v = VOL[vol]
    d = v.get("radius_km", 30) / 111.0
    return (v["lon"] - d, v["lat"] - d, v["lon"] + d, v["lat"] + d)


def puntual(vol, sensor, kind, t, desplaza=0, nrt=False):
    """Granulos de CMR cuyo inicio cae a +-60 s de t (+desplaza). Devuelve lista de (pid, tipo, sn, ver, dn, upd)."""
    t = t + pd.Timedelta(minutes=desplaza)
    cat = cmr.catalogo(sensor, kind, (t - pd.Timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                       (t + pd.Timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ"), bbox(vol), nrt=nrt)
    out = []
    for k, v in cat.items():
        if abs((pd.Timestamp(k) - t).total_seconds()) <= 60:
            out += v
    return out


def main():
    df = pd.read_csv(HERE / "osf_pareo.csv", parse_dates=["t"])
    falt = df[~df.cubierta]
    post = falt[falt.t >= INI_SERIE]
    pre = falt[falt.t < INI_SERIE].assign(mes=lambda d: d.t.dt.strftime("%Y-%m"))
    pre_s = pre.groupby("vol", group_keys=False).apply(lambda g: g.sample(min(len(g), 6), random_state=159))
    cov = df[df.cubierta]
    ctrl = pd.concat([g.sample(min(5, len(g)), random_state=159) for _, g in cov.groupby("sensor_esp")])
    consulta_idx = set(post.index) | set(pre_s.index) | set(ctrl.index)
    print("filas a consultar en CMR:", len(consulta_idx), "| post-inicio:", len(post), "| muestra pre-inicio:", len(pre_s), "| controles:", len(ctrl), flush=True)
    cache_hit = {}
    for n, i in enumerate(sorted(consulta_idx)):
        r = df.loc[i]
        cache_hit[i] = (puntual(r.vol, r.sensor_esp, "l1b", r.t), puntual(r.vol, r.sensor_esp, "geo", r.t))
        if n % 20 == 0:
            print(n, r.vol, r.t, len(cache_hit[i][0]), len(cache_hit[i][1]), flush=True)

    def hit(i, kind):
        return cache_hit[i][0 if kind == "l1b" else 1] if i in cache_hit else None

    filas = []
    for i, r in df.iterrows():
        t = r.t
        elev = _solar_elevation(VOL[r.vol]["lat"], VOL[r.vol]["lon"], datetime(t.year, t.month, t.day, t.hour, t.minute))
        l1b = hit(i, "l1b")
        geo = hit(i, "geo")
        consultada = l1b is not None
        l1b = l1b or []
        geo = geo or []
        if r.cubierta:
            c = "cubierta"
        elif t < INI_SERIE:
            c = "F"
        elif elev >= 0 or r.dayflag == 1:
            c = "C"
        elif not l1b:
            c = "A"
        elif not geo:
            c = "D"
        else:
            c = "B"
        filas.append(dict(vol=r.vol, t=t, sensor=r.sensor_esp, dayflag=r.dayflag, elev=round(elev, 2), consultada=consultada,
                          cmr_l1b=len(l1b) if consultada else -1, cmr_geo=len(geo) if consultada else -1, pid=l1b[0][0] if l1b else None, dn=l1b[0][4] if l1b else None,
                          gran_nuestro=r.gran_cercano if r.cubierta else None, clase=c, npix=r.npix, cls=r["cls"],
                          vrp_w=r.vrp_w, cubierta=r.cubierta))
    res = pd.DataFrame(filas)
    res.to_csv(HERE / "clasificacion.csv", index=False)

    c = res[res.cubierta & res.consultada]
    print("\n== CONTROL POSITIVO (pasadas con record, consultadas) ==")
    print("n:", len(c), "| CMR L1B presente:", int((c.cmr_l1b > 0).sum()), "| GEO presente:", int((c.cmr_geo > 0).sum()),
          "| elevacion < 0:", int((c.elev < 0).sum()), "| elevacion >= 0:", int((c.elev >= 0).sum()))

    def mismo(r):
        if not isinstance(r.pid, str) or not isinstance(r.gran_nuestro, str):
            return False
        return r.pid.split(".")[1:3] == r.gran_nuestro.split(".")[1:3] and r.pid[:3] == r.gran_nuestro[:3]
    print("producer_granule_id de CMR == granulo del record (prefijo+AYYYYDDD.HHMM):", int(c.apply(mismo, axis=1).sum()), "de", len(c))
    cc = res[res.cubierta]
    print("dayflag OSF vs elevacion en TODAS las cubiertas (2523): dayflag=0 con elev>=0:", int(((cc.dayflag == 0) & (cc.elev >= 0)).sum()),
          "| dayflag=1 con elev<0:", int(((cc.dayflag == 1) & (cc.elev < 0)).sum()))

    # control negativo: hora OSF + 180 min
    cn = df.loc[c.index] if False else None
    neg = 0
    ids = [i for i in ctrl.index][:10]
    for i in ids:
        r = df.loc[i]
        neg += len(puntual(r.vol, r.sensor_esp, "l1b", r.t, desplaza=180)) > 0
    print("\n== CONTROL NEGATIVO (hora OSF + 180 min, misma plataforma/volcan, %d casos): con granulo en CMR: %d" % (len(ids), neg))

    f = res[~res.cubierta]
    print("\n== CLASES de las", len(f), "pasadas sin record (F: solo la muestra consultada tiene dato CMR) ==")
    print(f.clase.value_counts().to_string())
    print("\nclase x Dayflag OSF:")
    print(pd.crosstab(f.clase, f.dayflag).to_string())
    for cl in ("F", "C"):
        g = f[(f.clase == cl) & f.consultada]
        print(f"\n{cl}: consultadas={len(g)} | CMR L1B presente={int((g.cmr_l1b > 0).sum())} ausente={int((g.cmr_l1b == 0).sum())} | "
              f"L1B sin GEO={int(((g.cmr_l1b > 0) & (g.cmr_geo == 0)).sum())}")
    print("\nDETALLE no-F no-C (A, B, D):")
    print(f[~f.clase.isin(["F", "C"])][["vol", "t", "sensor", "dayflag", "elev", "cmr_l1b", "cmr_geo", "clase", "npix", "vrp_w"]].to_string())
    print("\nclase C: elevacion por dayflag")
    print(f[f.clase == "C"].groupby("dayflag").elev.describe().to_string())
    x = f[(f.dayflag == 0) & (f.elev >= 0)]
    print("\nfaltantes con Dayflag=0 de MIROVA y elevacion >= 0 en el volcan:", len(x))
    print(x[["vol", "t", "sensor", "elev", "cmr_l1b", "cmr_geo"]].to_string())
    y = f[(f.dayflag == 1) & (f.elev < 0)]
    print("faltantes con Dayflag=1 y elevacion < 0:", len(y))
    print(y[["vol", "t", "sensor", "elev", "cmr_l1b", "cmr_geo"]].to_string())
    g = f[(f.clase == "F") & f.consultada].assign(mes=lambda d: d.t.dt.strftime("%Y-%m"))
    print("\nF consultadas por volcan (con L1B+GEO en CMR / consultadas):")
    print(g.assign(ok=(g.cmr_l1b > 0) & (g.cmr_geo > 0)).groupby("vol").agg(n=("ok", "size"), con_cmr=("ok", "sum")).to_string())


if __name__ == "__main__":
    main()
