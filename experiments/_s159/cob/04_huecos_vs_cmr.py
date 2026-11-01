# -*- coding: utf-8 -*-
"""COB 04 (S159, VB-4). Cruza, para los ultimos 45 dias, los gránulos nocturnos que CMR sirve HOY sobre cada volcan
con los records de produccion (remoto, _remoto/). Ventana: 2026-09-07 .. 2026-10-21 (hoy parcial).

Para cada (volcan, sensor): S = granulos L1B de CMR (Standard + NRT, todas las versiones, caja de fetch.py:751-753)
con elevacion solar < 0 en el volcan (pipeline.fetch._solar_elevation, igual que el filtro de produccion);
R = records con ese sensor. Clases por granulo:
  ok        en S y en R
  sin_rec_B en S con GEO en CMR y sin record (produccion no lo proceso o no lo guardo)
  sin_geo_D en S sin GEO en CMR (VB-1: se descarta en silencio)
  rec_sin_cmr  en R y no en S: CMR no lo sirve hoy (R2-13) o lo filtramos como diurno (se separa por elevacion)

Pregunta 1: si produccion hubiera perdido granulos, sin_rec_B + sin_geo_D > 0 (control positivo esperado: el 13-oct y
el 20-oct). Si el catalogo estuviera vacio, S seria 0 en todos los dias: se imprime la cantidad de granulos por dia.
Pregunta 2: un dia sin hallazgos solo cuenta como sano si S > 0 ese dia.
Limite: CMR hoy puede no coincidir con CMR del dia en que produccion corrio (R2-13), por eso "rec_sin_cmr" se informa
aparte y no se cuenta como falla.
"""
from __future__ import annotations
import sys, io, json
from datetime import datetime
from pathlib import Path
import pandas as pd, yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
WT = Path(r"C:\vrp-trabajo\s159-pruebas")
HERE = WT / "experiments/_s159/cob"
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(WT))
import cmrpub as cmr  # noqa: E402
from pipeline.fetch import _solar_elevation  # noqa: E402

VOL = {v["name"]: v for v in yaml.safe_load(open(WT / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
VOLS = ["Lascar", "Chaiten", "PuyehueCordonCaulle", "Lastarria", "Villarrica", "NevadosDeChillan", "Isluga", "Copahue",
        "PlanchonPeteroa", "Llaima", "Tupungatito"]
SENS = list(cmr.PRODUCTOS)
T0, T1 = "2026-09-06T12:00:00Z", "2026-10-21T18:00:00Z"
INI = pd.Timestamp("2026-09-07")


def bbox(v):
    d = VOL[v].get("radius_km", 30) / 111.0
    return (VOL[v]["lon"] - d, VOL[v]["lat"] - d, VOL[v]["lon"] + d, VOL[v]["lat"] + d)


def main():
    recs = {}
    for v in VOLS:
        for r in json.load(open(HERE / "_remoto" / f"{v}.json", encoding="utf-8"))["records"]:
            t = pd.Timestamp(r["datetime_utc"])
            if t >= INI:
                recs.setdefault((v, r["sensor"]), {})[t.strftime("%Y-%m-%dT%H:%M")] = r.get("product_version")
    filas = []
    # CMR solo para 4 volcanes que cubren el pais de norte a sur (limite de tiempo; los huecos de plataforma son
    # comunes a todos los volcanes, y el conteo de records por volcan va completo en 03).
    VCMR = ["Isluga", "Lascar", "Villarrica", "Chaiten"]
    for v in VCMR:
        for s in SENS:
            l1b = cmr.catalogo(s, "l1b", T0, T1, bbox(v))
            geo = cmr.catalogo(s, "geo", T0, T1, bbox(v))
            R = recs.get((v, s), {})
            keys = set(l1b) | set(R)
            for k in keys:
                t = pd.Timestamp(k)
                if t < INI:
                    continue
                elev = _solar_elevation(VOL[v]["lat"], VOL[v]["lon"], datetime(t.year, t.month, t.day, t.hour, t.minute))
                en_s = k in l1b
                tipo = ",".join(sorted({x[1] for x in l1b.get(k, [])})) if en_s else ""
                if en_s and k in R:
                    c = "ok"
                elif en_s and elev >= 0:
                    c = "diurno"
                elif en_s and k in geo:
                    c = "sin_rec_B"
                elif en_s:
                    c = "sin_geo_D"
                else:
                    c = "rec_sin_cmr"
                filas.append(dict(vol=v, sensor=s, t=t, dia=t.normalize(), elev=round(elev, 1), clase=c, cmr_tipo=tipo,
                                  n_geo=len(geo.get(k, [])), geo_tipo=",".join(sorted({x[1] for x in geo.get(k, [])})),
                                  pid=l1b[k][0][0] if en_s else None, upd=l1b[k][0][5] if en_s else None, pv=R.get(k)))
        print("listo", v, flush=True)
    df = pd.DataFrame(filas)
    df.to_csv(HERE / "huecos_vs_cmr.csv", index=False)
    pd.set_option("display.width", 250)
    print("\nTOTAL por clase:", df.clase.value_counts().to_dict())
    print("granulos CMR nocturnos por dia (control: >0 todos los dias):")
    noc = df[(df.clase != "rec_sin_cmr") & (df.clase != "diurno")]
    tab = df.groupby(["dia", "clase"]).size().unstack(fill_value=0)
    tab["cmr_noche"] = noc.groupby("dia").size()
    print(tab.to_string())
    print("\nDETALLE por dia y sensor de sin_rec_B / sin_geo_D / rec_sin_cmr (conteos por sensor):")
    for cl in ("sin_rec_B", "sin_geo_D", "rec_sin_cmr"):
        g = df[df.clase == cl]
        print(f"\n{cl}: {len(g)}")
        if len(g):
            print(g.groupby(["dia", "sensor"]).size().unstack(fill_value=0).to_string())
    print("\nsin_rec_B por volcan:", df[df.clase == "sin_rec_B"].groupby("vol").size().to_dict())
    print("cobertura por dia = ok / (ok + sin_rec_B + sin_geo_D):")
    cov = df.pivot_table(index="dia", columns="clase", values="vol", aggfunc="count", fill_value=0)
    for c in ("ok", "sin_rec_B", "sin_geo_D"):
        if c not in cov:
            cov[c] = 0
    cov["cob"] = (cov.ok / (cov.ok + cov.sin_rec_B + cov.sin_geo_D)).round(3)
    print(cov[["ok", "sin_rec_B", "sin_geo_D", "cob"]].to_string())


if __name__ == "__main__":
    main()
