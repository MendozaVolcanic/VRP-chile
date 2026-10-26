# -*- coding: utf-8 -*-
"""V1 (S158): alertas VIIRS 750 de MIROVA en la ventana K contra nuestros records VIIRS 750 (F1-H2, F1-H7).

Ventana: observaciones desde 2026-09-18 00:00 UTC (los datos cambian de detector ahi, marca S157) hasta el
ultimo record de cada volcan. Referencia: latest_consolidado.csv (tabla, ALERTA_TERMICA, Sensor == 'VIIRS')
+ OCR snapshot (ALERTA_TERMICA_OCR y ALERTA_SIN_GEOMETRIA_OCR, Sensor == 'VIIRS'), deduplicado por volcan+minuto.
Par: record nuestro VIIRS *_750 del mismo volcan con |dt| <= 8 min (un granulo VIIRS dura ~6 min).
Dia/noche: elevacion solar con la misma funcion de store.py en el crater (volcanoes.yaml).

Pregunta 1: si perdieramos alertas, se veria? Si: se lista cada alerta sin par. Pregunta 2: instrumento muerto (sin
records cargados, o tolerancia de tiempo rota) daria CERO pares en todo; por eso se imprime el total de pares
como control positivo: la mayoria de alertas nocturnas debe tener par.
"""
import os, sys, io, json, glob
sys.path.insert(0, os.getcwd())
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import pandas as pd, numpy as np, yaml
from pipeline.store import _solar_elevation as _se
sol = lambda t, la, lo: _se(la, lo, t)
NOMBRES = {"Chaiten": "Chaiten", "Copahue": "Copahue", "Isluga": "Isluga", "Lascar": "Lascar",
           "Lastarria": "Lastarria", "Llaima": "Llaima", "Nevados de Chillan": "NevadosDeChillan",
           "PlanchonPeteroa": "PlanchonPeteroa", "Puyehue-Cordon Caulle": "PuyehueCordonCaulle",
           "Tupungatito": "Tupungatito", "Villarrica": "Villarrica"}
DESDE = pd.Timestamp("2026-09-18 00:00")

cons = pd.read_csv("latest_consolidado.csv")
ocr = pd.read_csv("data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv")
cons = cons[(cons.Sensor == "VIIRS") & (cons.Tipo_Registro == "ALERTA_TERMICA")].assign(canal="tabla")
ocr = ocr[(ocr.Sensor == "VIIRS") & ocr.Tipo_Registro.isin(["ALERTA_TERMICA_OCR", "ALERTA_SIN_GEOMETRIA_OCR"])].assign(canal="ocr")
ref = pd.concat([cons, ocr], ignore_index=True)
ref["t"] = pd.to_datetime(ref.Fecha_Satelite_UTC)
ref = ref[ref.t >= DESDE]
ref["min"] = ref.t.dt.floor("min")
ref = ref.sort_values("canal", ascending=False).drop_duplicates(["Volcan", "min"])  # tabla primero

vy = yaml.safe_load(open("volcanoes.yaml", encoding="utf-8"))
vlist = vy["volcanoes"] if isinstance(vy, dict) and "volcanoes" in vy else vy
coords = {}
for v in vlist:
    nm = v.get("name") or v.get("id")
    coords[nm] = (v.get("vent_lat", v.get("lat")), v.get("vent_lon", v.get("lon")))

recs = {}
fin = {}
for csvn, jn in NOMBRES.items():
    d = json.load(open(f"data/mirova_equivalent/{jn}.json", encoding="utf-8"))
    rr = [r for r in d["records"] if str(r.get("sensor", "")).endswith("_750")]
    for r in rr:
        r["_t"] = pd.Timestamp(r["datetime_utc"]).tz_localize(None) if pd.Timestamp(r["datetime_utc"]).tzinfo else pd.Timestamp(r["datetime_utc"])
    recs[csvn] = rr
    fin[csvn] = max(r["_t"] for r in rr) if rr else None

def coord(csvn):
    jn = NOMBRES[csvn]
    for k, (la, lo) in coords.items():
        if k.replace(" ", "").replace("-", "").lower() == jn.lower():
            return la, lo
    return None

print("ultimo record V750 por volcan:", {k: str(v) for k, v in fin.items()})
filas = []
for _, a in ref.iterrows():
    v = a.Volcan
    if fin.get(v) is None or a.t > fin[v]:
        continue
    c = coord(v)
    elev = sol(a.t.to_pydatetime(), c[0], c[1]) if c else np.nan
    cand = [r for r in recs[v] if abs((r["_t"] - a.t).total_seconds()) <= 8 * 60]
    best = min(cand, key=lambda r: abs((r["_t"] - a.t).total_seconds())) if cand else None
    filas.append(dict(volcan=v, t=str(a.t), canal=a.canal, vrp=a.VRP_MW, dist=a.Distancia_km, elev=round(elev, 1),
                      dia=elev > 0, par=best is not None,
                      sens=best["sensor"] if best else None, dt_s=int((best["_t"] - a.t).total_seconds()) if best else None,
                      n_pix=best.get("n_anomalous_pixels") if best else None,
                      pc_vrp=(best.get("primary_cluster") or {}).get("vrp_mw") if best else None,
                      dclass=best.get("distance_class") if best else None))
F = pd.DataFrame(filas)
F.to_csv(os.path.join(os.path.dirname(__file__), "cruce_v750_k.csv"), index=False)
print("alertas V750 MIROVA en ventana (dedup volcan+minuto):", len(F), " noche", int((~F.dia).sum()), " dia", int(F.dia.sum()))
print("protegidas (>=1 MW):", int((F.vrp >= 1).sum()), " noche", int(((F.vrp >= 1) & ~F.dia).sum()), " dia", int(((F.vrp >= 1) & F.dia).sum()))
print("CONTROL: alertas nocturnas con par", int((~F.dia & F.par).sum()), "de", int((~F.dia).sum()))
print("\nALERTAS DIURNAS:")
print(F[F.dia].to_string(index=False))
print("\nALERTAS NOCTURNAS SIN RECORD NUESTRO (|dt|<=8 min):")
print(F[~F.dia & ~F.par].to_string(index=False))
print("\nALERTAS NOCTURNAS CON RECORD PERO 0 PIXELES:")
print(F[~F.dia & F.par & (F.n_pix == 0)].to_string(index=False))
