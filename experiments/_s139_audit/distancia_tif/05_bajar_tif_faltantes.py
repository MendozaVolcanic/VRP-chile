# -*- coding: utf-8 -*-
"""S139 - baja de GitHub sólo los TIF que faltan para las pasadas que importan.

POR QUÉ. La copia local del archivo de TIF quedó congelada el 2026-05-20 (el `git pull`
del repo completo falló por espacio en disco). Las filas que deciden la pregunta son las
FALSO_POSITIVO NOCTURNAS (las que el scraper esconde del dashboard) y una muestra de
ALERTA_TERMICA para contraste, y entre el 21 de mayo y hoy hay varios meses de ésas sin
TIF local. Se bajan por HTTP de a un archivo, sólo los emparejables, con tope duro.

Escribe únicamente dentro de `_dl_/` (ignorado por git). No toca el archivo hermano.
"""
import io
import json
import os
import re
import sys
import time
import urllib.request

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
DL = os.path.join(AQUI, "_dl_")
BASE = "https://raw.githubusercontent.com/MendozaVolcanic/mirova-tif-archive/main/"
WEB = os.path.join(ROOT, "data", "mirova_reference", "mirova_v1_snapshot",
                   "registro_vrp_consolidado.csv")
TOPE = 400
TOL_MIN = 30
_TS = re.compile(r"(\d{8}_\d{6})")

ARCH2OURS = {"ChillanNevadosde": "NevadosDeChillan"}
SENS = {"MODIS": "MODIS", "VIIRS750": "VIIRS", "VIIRS375": "VIIRS375"}
ALIAS = {
    "Villarrica": {"Villarrica"},
    "PlanchonPeteroa": {"PlanchonPeteroa", "Planchon-Peteroa", "Planchon Peteroa"},
    "Lascar": {"Lascar", "Láscar"},
    "PuyehueCordonCaulle": {"PuyehueCordonCaulle", "Puyehue-Cordon Caulle",
                            "Puyehue Cordon Caulle", "Puyehue-Cordón Caulle"},
    "NevadosDeChillan": {"NevadosDeChillan", "Nevados de Chillan", "Nevados de Chillán"},
    "Copahue": {"Copahue"}, "Llaima": {"Llaima"}, "Lastarria": {"Lastarria"},
    "Isluga": {"Isluga"}, "Chaiten": {"Chaiten", "Chaitén"},
    "Tupungatito": {"Tupungatito"},
}
WEB2OURS = {n: k for k, s in ALIAS.items() for n in s}
LON = {"Villarrica": -71.93, "PlanchonPeteroa": -70.57, "Lascar": -67.73,
       "PuyehueCordonCaulle": -72.12, "NevadosDeChillan": -71.38, "Copahue": -71.18,
       "Llaima": -71.73, "Lastarria": -68.51, "Isluga": -68.83, "Chaiten": -72.65,
       "Tupungatito": -69.80}


def bajar(url, destino, reintentos=3):
    for i in range(reintentos):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                b = r.read()
            os.makedirs(os.path.dirname(destino), exist_ok=True)
            open(destino, "wb").write(b)
            return len(b)
        except Exception:
            if i == reintentos - 1:
                return None
            time.sleep(2 * (i + 1))
    return None


def main():
    os.makedirs(DL, exist_ok=True)
    ix = os.path.join(DL, "index_remoto.csv")
    if not os.path.exists(ix):
        n = bajar(BASE + "index.csv", ix)
        print(f"index.csv remoto: {n} bytes")
    idx = pd.read_csv(ix)
    idx["volcano"] = idx.volcano.map(lambda v: ARCH2OURS.get(v, v))
    acq = pd.to_datetime(idx.acquisition_utc, utc=True, errors="coerce")
    fn = idx.tif_path.str.extract(_TS, expand=False)
    fnts = pd.to_datetime(fn, format="%Y%m%d_%H%M%S", utc=True, errors="coerce")
    idx["acq"] = acq.fillna(fnts)
    idx = idx.dropna(subset=["acq"]).sort_values("captured_at_utc")
    idx = idx.drop_duplicates(subset=["volcano", "sensor", "md5"], keep="first")
    idx = idx.drop_duplicates(subset=["volcano", "sensor", "acq"], keep="first")
    print("index remoto:", len(idx), "filas |", str(idx.acq.min()), "->", str(idx.acq.max()))

    w = pd.read_csv(WEB)
    w["t"] = pd.to_datetime(w.Fecha_Satelite_UTC, errors="coerce", utc=True)
    w["vol"] = w.Volcan.map(lambda v: WEB2OURS.get(str(v).strip()))
    w["VRP_MW"] = pd.to_numeric(w.VRP_MW, errors="coerce")
    w["Distancia_km"] = pd.to_numeric(w.Distancia_km, errors="coerce")
    w = w.dropna(subset=["t", "vol"])
    w = w[w.Tipo_Registro.isin(["ALERTA_TERMICA", "FALSO_POSITIVO"])]
    w = w[w.VRP_MW > 0]
    # Nocturnas: hora solar local = UTC + lon/15, fuera de [06, 19).
    hsol = (w.t.dt.hour + w.t.dt.minute / 60.0 + w.vol.map(LON) / 15.0) % 24
    w = w[(hsol >= 19) | (hsol < 6)]
    # Sólo lo que falta: desde el 21 de mayo (lo previo ya está en la copia local).
    w = w[w.t >= pd.Timestamp("2026-05-21", tz="UTC")]
    print("filas web nocturnas con VRP>0 desde 2026-05-21:", len(w),
          dict(w.Tipo_Registro.value_counts()))

    # Emparejar cada fila con su TIF en el índice remoto.
    objetivos = []
    for _, r in w.iterrows():
        c = idx[(idx.volcano == r["vol"]) & (idx.sensor.map(SENS) == r["Sensor"])]
        if c.empty:
            continue
        dt = (c.acq - r["t"]).abs().dt.total_seconds() / 60.0
        j = dt.idxmin()
        if dt.loc[j] > TOL_MIN:
            continue
        objetivos.append({"tif_path": c.loc[j, "tif_path"], "volcan": r["vol"],
                          "sensor": r["Sensor"], "tipo": r["Tipo_Registro"],
                          "acq": c.loc[j, "acq"].isoformat(),
                          "t_web": r["t"].isoformat(),
                          "vrp_mw": float(r["VRP_MW"]),
                          "dist_pub_km": float(r["Distancia_km"])})
    # Dedup por TIF y prioridad: primero FALSO_POSITIVO, después ALERTA.
    vistos, orden = set(), []
    for t in ("FALSO_POSITIVO", "ALERTA_TERMICA"):
        for o in objetivos:
            if o["tipo"] == t and o["tif_path"] not in vistos:
                vistos.add(o["tif_path"])
                orden.append(o)
    print("pasadas emparejables:", len(orden),
          {t: sum(1 for o in orden if o["tipo"] == t)
           for t in ("FALSO_POSITIVO", "ALERTA_TERMICA")})

    bajados, bytes_tot, fallos = [], 0, 0
    for o in orden[:TOPE]:
        destino = os.path.join(DL, o["tif_path"].replace("/", os.sep))
        if os.path.exists(destino):
            o["bytes"] = os.path.getsize(destino)
            bajados.append(o)
            continue
        n = bajar(BASE + o["tif_path"], destino)
        if n is None:
            fallos += 1
            continue
        bytes_tot += n
        o["bytes"] = n
        bajados.append(o)
        if len(bajados) % 50 == 0:
            print(f"  {len(bajados)} bajados ({bytes_tot/1e6:.1f} MB)")
    R = {"tope": TOPE, "n_emparejables": len(orden), "n_bajados": len(bajados),
         "fallos": fallos, "MB": round(bytes_tot / 1e6, 2),
         "ventana": [min(o["acq"] for o in bajados), max(o["acq"] for o in bajados)]
         if bajados else None,
         "por_tipo": {t: sum(1 for o in bajados if o["tipo"] == t)
                      for t in ("FALSO_POSITIVO", "ALERTA_TERMICA")},
         "por_sensor": {s: sum(1 for o in bajados if o["sensor"] == s)
                        for s in ("MODIS", "VIIRS", "VIIRS375")},
         "detalle": bajados}
    json.dump(R, open(os.path.join(AQUI, "05_bajados.json"), "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)
    print(json.dumps({k: v for k, v in R.items() if k != "detalle"},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
