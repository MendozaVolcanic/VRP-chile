# -*- coding: utf-8 -*-
"""S139 - tres cosas de contexto que el informe necesita declarar.

1. QUÉ ES EL TIMESTAMP DEL NOMBRE DEL TIF. El índice del archivo trae `acquisition_utc` y
   `last_modified_utc`; el nombre lleva uno de los dos y hay que saber cuál antes de parear.

2. EL UMBRAL DEL SCRAPER, medido y no supuesto. El scraper etiqueta FALSO_POSITIVO cuando la
   distancia publicada supera un límite por volcán. Ese límite no está en este repo: se
   despeja de los datos, como el corte entre la ALERTA más lejana y el FALSO_POSITIVO más
   cercano de cada volcán.

3. CUÁNTAS FILAS FALSO_POSITIVO PODRÍAN TENER EL CRÁTER ADENTRO, con el umbral real de cada
   volcán, calculado sobre el archivo OSF del propio MIROVA (donde las dos definiciones
   conviven en la misma fila y no hace falta ningún proxy).

Read-only.
"""
import io
import json
import os
import sys

import numpy as np
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
ARCH = os.path.abspath(os.path.join(ROOT, "..", "mirova-tif-archive"))
WEB = os.path.join(ROOT, "data", "mirova_reference", "mirova_v1_snapshot",
                   "registro_vrp_consolidado.csv")
OSF = os.path.join(ROOT, "data", "mirova_reference", "VRP_GLOBAL_ARCHIVE_2025.csv")
OSF2WEB = {"Láscar": "Lascar", "Chaitén": "Chaiten",
           "Puyehue-Cordón Caulle": "Puyehue-Cordon Caulle", "Lastarria": "Lastarria",
           "Villarrica": "Villarrica", "Chillán, Nevados de": "Nevados de Chillan",
           "Isluga": "Isluga", "Copahue": "Copahue",
           "Planchón-Peteroa": "PlanchonPeteroa", "Llaima": "Llaima"}


def main():
    R = {}
    # ── 1. Timestamp del nombre ────────────────────────────────────────────
    ix = pd.read_csv(os.path.join(ARCH, "index.csv"))
    acq = pd.to_datetime(ix.acquisition_utc, utc=True, errors="coerce")
    lm = pd.to_datetime(ix.last_modified_utc, utc=True, errors="coerce")
    fn = pd.to_datetime(ix.tif_path.str.extract(r"(\d{8}_\d{6})", expand=False),
                        format="%Y%m%d_%H%M%S", utc=True, errors="coerce")
    hay = acq.notna()
    R["timestamp_del_nombre"] = {
        "n_filas": int(len(ix)),
        "con_acquisition_utc_pct": round(100.0 * float(hay.mean()), 1),
        "nombre_==_acquisition_<=60s_pct": round(100.0 * float(
            ((fn - acq).abs().dt.total_seconds() <= 60)[hay].mean()), 1),
        "nombre_==_last_modified_<=60s_pct_donde_falta_acq": round(100.0 * float(
            ((fn - lm).abs().dt.total_seconds() <= 60)[~hay].mean()), 1),
        "conclusion": "cuando existe acquisition_utc el nombre ES la hora de adquisición; "
                      "cuando falta, el nombre es la hora de publicación (last_modified)"}

    # ── 2. Umbral del scraper por volcán ───────────────────────────────────
    w = pd.read_csv(WEB)
    w["Distancia_km"] = pd.to_numeric(w.Distancia_km, errors="coerce")
    w = w.dropna(subset=["Distancia_km"])
    umbrales = {}
    for v, g in w.groupby("Volcan"):
        a = g[g.Tipo_Registro == "ALERTA_TERMICA"].Distancia_km
        f = g[g.Tipo_Registro == "FALSO_POSITIVO"].Distancia_km
        if len(a) < 5 or len(f) < 5:
            continue
        umbrales[v] = {"n_alerta": int(len(a)), "n_falso": int(len(f)),
                       "alerta_max_km": round(float(a.max()), 2),
                       "falso_min_km": round(float(f.min()), 2),
                       "umbral_estimado_km": round(float((a.max() + f.min()) / 2), 2),
                       "solapan": bool(a.max() > f.min())}
    R["umbral_del_scraper_por_volcan"] = umbrales

    # ── 3. Filas que esconderían el cráter, con el umbral real ─────────────
    o = pd.read_csv(OSF)
    o = o[o.Volc_Name.isin(OSF2WEB)].copy()
    o["web"] = o.Volc_Name.map(OSF2WEB)
    la0, lo0 = o.Volc_LAT.values, o.Volc_LON.values
    dy = (o.LAT.values - la0) * 110.574
    dx = (o.LON.values - lo0) * 111.320 * np.cos(np.radians(la0))
    o["d_hot"] = np.hypot(dx, dy)
    o["md"] = o.Max_Dist / 1000.0
    o = o.dropna(subset=["d_hot", "md"])
    esconde = {}
    for vweb, u in umbrales.items():
        g = o[o.web == vweb]
        if len(g) < 100:
            continue
        r = u["umbral_estimado_km"]
        sup = g[g.md > r]
        adentro = sup[sup.d_hot <= r]
        esconde[vweb] = {
            "umbral_km": r, "n_filas_osf": int(len(g)),
            "superan_por_max_dist": int(len(sup)),
            "de_esas_con_el_mas_caliente_adentro": int(len(adentro)),
            "pct": round(100.0 * len(adentro) / max(1, len(sup)), 2)}
    tot_sup = sum(e["superan_por_max_dist"] for e in esconde.values())
    tot_ad = sum(e["de_esas_con_el_mas_caliente_adentro"] for e in esconde.values())
    R["falsos_positivos_que_esconderian_el_crater"] = {
        "por_volcan": esconde,
        "agregado": {"superan_por_max_dist": tot_sup,
                     "con_el_mas_caliente_adentro": tot_ad,
                     "pct": round(100.0 * tot_ad / max(1, tot_sup), 2)},
        "nota": "medido sobre el archivo OSF 2000-2025, donde Max_Dist y el píxel más "
                "caliente conviven en la misma fila. Es la cota de cuántas filas "
                "FALSO_POSITIVO tendrían señal en el cráter SI la web publica Max_Dist."}

    out = os.path.join(AQUI, "11_umbral_del_scraper_y_timestamps.json")
    json.dump(R, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
    print("escrito:", out)
    print(json.dumps(R, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
